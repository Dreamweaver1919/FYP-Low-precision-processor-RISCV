"""Run real overlay configuration guards; no program/FPGA success is inferred."""
import hashlib
import datetime
import json
import pathlib
import subprocess
import sys
from run_tests import ROOT, VIVADO, resolve_sources


def invoke(args, out, log, timeout=90):
    with (out / log).open('w') as stream:
        result = subprocess.run([str(arg) for arg in args], cwd=out,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    return result.returncode


def run():
    out = ROOT / 'artifacts/verification/arithmetic/parameter_matrix' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out.mkdir(parents=True, exist_ok=True)
    sources = resolve_sources('overlay_nn1')
    # Integer baseline list prunes the FPU. For the rejected FPU1 case, include
    # the actual frozen dependencies so a missing module cannot mimic rejection.
    fpnew = ROOT / 'vendor/cv32e40p/rtl/vendor/pulp_platform_fpnew'
    extras = sorted((fpnew / 'src').glob('*.sv')) + sorted((fpnew / 'vendor/opene906').rglob('*.v'))
    sources += [p for p in extras if p not in sources]
    sources += [ROOT / 'verification/tb/tb_nn_config.sv']
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    (out / 'run.json').write_text(json.dumps({'sources': hashes}, indent=2) + '\n')
    (out / 'sources.prj').write_text(''.join(f'sv xil_defaultlib "{p.as_posix()}"\n' for p in sources))
    compile_rc = invoke([VIVADO / 'xvlog.bat', '--sv', '-d', 'XSIM', '--prj', 'sources.prj',
                         '-i', ROOT / 'rtl/core/include', '-i', ROOT / 'vendor/cv32e40p/rtl/include',
                         '-i', ROOT / 'vendor/cv32e40p/rtl/vendor/pulp_platform_common_cells/include',
                         '--log', 'xvlog.log'], out, 'xvlog.stdout.log')
    cases = [
        ('disabled_pulp0', (0, 0, 0, 0, 0), False),
        ('disabled_pulp1', (1, 0, 0, 0, 0), False),
        ('enabled_supported', (1, 1, 0, 0, 0), False),
        ('invalid_pulp0', (0, 1, 0, 0, 0), True),
        ('invalid_cluster1', (1, 1, 1, 0, 0), True),
        ('invalid_fpu1', (1, 1, 0, 1, 0), True),
        ('invalid_zfinx1', (1, 1, 0, 0, 1), True),
    ]
    results = []
    for name, params, rejection in cases:
        item = {'name': name, 'params': dict(zip(('pulp', 'nn', 'cluster', 'fpu', 'zfinx'), params)),
                'expected_rejection': rejection, 'status': 'UNRUNNABLE'}
        if compile_rc:
            item['reason'] = 'source compilation failed'
            results.append(item)
            continue
        (out / f'{name}.args').write_text(''.join(
            f'--generic_top "TEST_{key}={value}"\n'
            for key, value in zip(('PULP', 'NN', 'CLUSTER', 'FPU', 'ZFINX'), params)))
        rc = invoke([VIVADO / 'xelab.bat', 'xil_defaultlib.tb_nn_config', '--file', f'{name}.args',
                     '--mt', '2', '--timescale', '1ns/1ps', '--snapshot', name,
                     '--log', f'{name}.xelab.log'], out, f'{name}.xelab.stdout.log')
        item['xelab_exit'] = rc
        if rc:
            item['reason'] = 'elaboration failed before configuration guard could execute; inspect log'
        else:
            rc = invoke([VIVADO / 'xsim.bat', name, '--runall', '--log', f'{name}.xsim.log'],
                        out, f'{name}.xsim.stdout.log')
            item['xsim_exit'] = rc
            text = (out / f'{name}.xsim.log').read_text()
            rejected = 'Fatal: COREV_XPULPNN requires PULP=1, CLUSTER=0, FPU=0, ZFINX=0' in text
            passed = 'NN_CONFIG_PASS' in text and 'Fatal:' not in text and rc == 0
            item['status'] = 'PASS' if (rejected if rejection else passed) else 'FAIL'
            item['observed'] = 'configuration guard rejected at time0' if rejected else 'accepted reset-only configuration' if passed else 'unexpected simulator outcome'
        results.append(item)
        print(name, item['status'], item.get('observed', item.get('reason')), flush=True)
    changed = [path for path, digest in hashes.items()
               if hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() != digest]
    summary = {'artifact': str(out), 'status': 'PASS' if all(x['status'] == 'PASS' for x in results) and not changed else 'FAIL',
               'note': 'initial $fatal guards execute at simulation time0; xelab acceptance alone is not rejection',
               'compile_exit': compile_rc, 'changed_sources': changed, 'cases': results}
    (out / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    result = run()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
