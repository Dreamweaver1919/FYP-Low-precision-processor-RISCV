"""Check actual JTAG readback against pinned expected results and build identity."""
import argparse
import json
from pathlib import Path


def validate_capture(build, expected, capture):
    errors = []
    if build.get('status') != 'PASS': errors.append('build did not pass')
    for key in ('build_id', 'usr_access'):
        if capture.get(key, '').lower() != build['build_id'].lower(): errors.append(key+' mismatch')
    wanted = 19 if build['config'] == 'overlay_nn1' else 3
    if capture.get('status') != wanted: errors.append('completion/pass/config/overflow status invalid')
    if capture.get('elapsed_cycles', 0) <= 0: errors.append('no elapsed cycles')
    if capture.get('count') != len(expected): errors.append('signature count mismatch')
    actual = capture.get('words', [])
    if len(actual) != len(expected): errors.append('readback length mismatch')
    for n, value in enumerate(expected):
        if value is not None and (n >= len(actual) or actual[n] != value):
            errors.append(f'output mismatch at {n}')
    fold = 0
    for value in expected:
        if value is None: break
        fold = ((fold << 5) | (fold >> 27)) & 0xffffffff
        fold ^= value
    if capture.get('signature') != fold: errors.append('signature fold mismatch')
    return errors


def kernel_metrics(words, benchmark, nn):
    def u64(at): return words[at] | (words[at+1] << 32)
    metrics = []
    for n, dataset in enumerate(benchmark['datasets']):
        at = benchmark['metrics_offset'] + n*benchmark['metrics_per_dataset']
        row = {'name': dataset['name'], 'logical_macs': dataset['logical_macs'],
               'physical_lane_macs': dataset['nn_physical_lane_macs']}
        for label, offset in [('preparation',0), ('legacy',4), ('native',8), ('scalar',12)]:
            cycles, instret = u64(at+offset), u64(at+offset+2)
            if label == 'native' and not nn:
                if cycles or instret: raise ValueError('baseline unexpectedly executed native kernel')
            elif cycles <= 0 or instret <= 0:
                raise ValueError('missing measured counters: '+dataset['name']+'/'+label)
            row[label+'_cycles'] = cycles
            row[label+'_instret'] = instret
        metrics.append(row)
    return metrics


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--build-dir', type=Path, required=True)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a=p.parse_args()
    build=json.loads((a.build_dir/'build.json').read_text())
    expected=json.loads((a.build_dir/'expected.json').read_text())['signature']
    capture=json.loads(a.capture.read_text())
    errors=validate_capture(build,expected,capture)
    metrics=[]
    if not errors:
        try:
            metrics=kernel_metrics(capture['words'],json.loads((a.build_dir/'benchmark.json').read_text()),
                                   build['config']=='overlay_nn1')
        except (ValueError,IndexError) as error: errors.append(str(error))
    report={'status':'FAIL' if errors else 'PASS', 'errors':errors, 'config':build['config'],
            'build_id':build['build_id'], 'bitstream_sha256':build.get('bitstream_sha256'),
            'deterministic_words':sum(x is not None for x in expected), 'signature_words':len(expected),
            'elapsed_cycles':capture.get('elapsed_cycles'), 'kernel_metrics':metrics}
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return bool(errors)


if __name__ == '__main__': raise SystemExit(main())
