"""Recheck published raw board captures and derive the performance comparison."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from board_results import validate_capture, kernel_metrics

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT/'docs/results/board-2026-10-29'
IMAGE = ROOT/'artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671'


def read(path): return json.loads(path.read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(directory=EVIDENCE):
    expected = read(IMAGE/'expected.json')['signature']
    benchmark = read(IMAGE/'benchmark.json')
    configs = {}
    for label, config in [('baseline', 'frozen_ff_pulp1'), ('nn', 'overlay_nn1')]:
        build = read(directory/label/'build.json')
        if build['config'] != config: raise ValueError('configuration mismatch')
        for item in build['sources'] + [build['finalization_script']]:
            if sha(ROOT/item['path']) != item['sha256']: raise ValueError('changed source: '+item['path'])
        for name, digest in build['memory_sha256'].items():
            if sha(IMAGE/name) != digest: raise ValueError('changed benchmark: '+name)
        identity = json.dumps({'config': config, 'sources': build['sources'],
                               'memory': build['memory_sha256']}, sort_keys=True).encode()
        digest = hashlib.sha256(identity).hexdigest()
        if digest != build['source_identity_sha256'] or digest[:8] != build['build_id']:
            raise ValueError('inconsistent build identity')
        timing = build['implementation']
        if timing.get('period_ns') != 20 or min(timing['wns_ns'], timing['whs_ns']) < 0 or timing['drc_errors']:
            raise ValueError('50 MHz timing/DRC failed')
        captures = []
        for trial in ('trial1', 'trial2'):
            path = directory/label/trial
            capture, manifest = read(path/'capture.json'), read(path/'trial.json')
            errors = validate_capture(build, expected, capture)
            if errors: raise ValueError('/'.join((label,trial))+': '+str(errors))
            if (manifest['status'] != 'PASS' or manifest['fresh_programming'] is not True or
                manifest['build_id'] != build['build_id'] or
                manifest['bitstream_sha256'] != build['bitstream_sha256']):
                raise ValueError('trial identity/programming failure')
            for script in manifest['scripts']:
                if sha(ROOT/script['path']) != script['sha256']: raise ValueError('changed trial script: '+script['path'])
            metrics = kernel_metrics(capture['words'], benchmark, label=='nn')
            if metrics != read(path/'result.json')['kernel_metrics']: raise ValueError('derived metrics mismatch')
            captures.append(capture)
        if captures[0] != captures[1]: raise ValueError('repeated trial data/counters differ')
        configs[label] = {'config': config, 'build_id': build['build_id'],
                          'bitstream_sha256': build['bitstream_sha256'],
                          'implementation': timing, 'trials_passed': 2,
                          'repeat_all_472_words_identical': True,
                          'elapsed_cycles': captures[0]['elapsed_cycles'], 'metrics': metrics}
    for name in ('ps-clock-readback.txt', 'ps-clock-after.txt', 'ps-clock-final.txt'):
        registers = {int(address, 16): int(value, 16) for address, value in
                     re.findall(r'PS_CLOCK_READ (0x[0-9A-Fa-f]+) (0x[0-9A-Fa-f]+)', (directory/name).read_text())}
        if (registers.get(0xFF5E0020) != 0x15a00 or registers.get(0xFF5E0028) != 0 or
            registers.get(0xFF5E00C0) != 0x01011e00 or not (registers.get(0xFF5E0040, 0) & 1)):
            raise ValueError('clock snapshot does not support nominal 50 MHz')
    receipt = read(directory/'final-board.json')
    if (receipt['usr_access'] != '0x'+configs['nn']['build_id'] or
        receipt['vio_build_id'] != receipt['usr_access'] or receipt['status'] != 19 or
        receipt['count'] != len(expected) or receipt['signature'] != captures[0]['signature'] or
        receipt['elapsed_cycles'] != configs['nn']['elapsed_cycles'] or
        receipt['heartbeat_before'] == receipt['heartbeat_after']):
        raise ValueError('final board receipt mismatch')
    for record in read(directory/'report-provenance.json'):
        if sha(directory/record['path']) != record['published_sha256']:
            raise ValueError('changed implementation report: '+record['path'])
    comparison = []
    for baseline, nn in zip(configs['baseline']['metrics'], configs['nn']['metrics'], strict=True):
        if baseline['name'] != nn['name']: raise ValueError('dataset order mismatch')
        for label in ('preparation', 'legacy', 'scalar'):
            for counter in ('cycles', 'instret'):
                key = label+'_'+counter
                if baseline[key] != nn[key]: raise ValueError('common kernel counters differ: '+key)
        n = nn['native_cycles']
        comparison.append({'name': nn['name'], 'logical_macs': nn['logical_macs'],
                           'physical_lane_macs': nn['physical_lane_macs'],
                           'baseline_legacy_cycles': baseline['legacy_cycles'],
                           'baseline_scalar_cycles': baseline['scalar_cycles'], 'native_cycles': n,
                           'legacy_over_native': baseline['legacy_cycles']/n,
                           'scalar_over_native': baseline['scalar_cycles']/n,
                           'preparation_plus_legacy_over_preparation_plus_native':
                               (baseline['preparation_cycles']+baseline['legacy_cycles'])/(nn['preparation_cycles']+n),
                           'preparation_plus_scalar_over_preparation_plus_native':
                               (baseline['preparation_cycles']+baseline['scalar_cycles'])/(nn['preparation_cycles']+n),
                           'native_us_at_nominal_50mhz': n/50})
    return {'status': 'PASS', 'date': '2026-10-29', 'nominal_clock_hz': 50000000,
            'clock_basis': 'PS register-derived; no oscilloscope measurement',
            'signature_words': len(expected), 'deterministic_words': sum(x is not None for x in expected),
            'configurations': configs, 'comparison': comparison}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--evidence-root', type=Path, default=EVIDENCE)
    p.add_argument('--write', action='store_true', help='Regenerate summary.json from raw evidence')
    a = p.parse_args()
    result = summarize(a.evidence_root)
    target = a.evidence_root/'summary.json'
    if a.write: target.write_text(json.dumps(result, indent=2)+'\n')
    elif result != read(target): raise ValueError('published summary differs from raw evidence')
    print('Board evidence audit: PASS (4 fresh trials, 472 words each, source/ROM identity matched)')
    for row in result['comparison']:
        print(f'{row["name"]}: legacy={row["baseline_legacy_cycles"]} scalar={row["baseline_scalar_cycles"]} '
              f'native={row["native_cycles"]}; scalar/native={row["scalar_over_native"]:.3f}x')


if __name__ == '__main__': main()
