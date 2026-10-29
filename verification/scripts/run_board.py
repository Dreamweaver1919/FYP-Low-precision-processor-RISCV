"""Verify build hashes, freshly program one image, and validate a physical trial."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight(directory):
    build = json.loads((directory/'build.json').read_text())
    if build['status'] != 'PASS': raise ValueError('build failed')
    timing = build['implementation']
    if timing.get('period_ns') != 20 or min(timing['wns_ns'], timing['whs_ns']) < 0 or timing['drc_errors']:
        raise ValueError('final 50 MHz implementation required')
    for name, digest in {**build['memory_sha256'], 'board.bit': build['bitstream_sha256'],
                         'board.ltx': build['probes_sha256']}.items():
        if sha(directory/name) != digest: raise ValueError('build artifact changed: '+name)
    for item in build['sources'] + [build['finalization_script']]:
        if sha(ROOT/item['path']) != item['sha256']: raise ValueError('source changed: '+item['path'])
    identity = json.dumps({'config': build['config'], 'sources': build['sources'],
                           'memory': build['memory_sha256']}, sort_keys=True).encode()
    digest = hashlib.sha256(identity).hexdigest()
    if digest != build['source_identity_sha256'] or digest[:8] != build['build_id']:
        raise ValueError('build identity inconsistent')
    return build


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--build-dir', type=Path, required=True)
    p.add_argument('--trial', type=Path, required=True, help='New directory; never overwrites a trial')
    p.add_argument('--vivado', default=os.environ.get('VIVADO', 'E:/vivado/2026.1/Vivado/bin/vivado.bat'))
    a = p.parse_args()
    directory, trial = a.build_dir.resolve(), a.trial.resolve()
    build = preflight(directory)
    trial.mkdir(parents=True, exist_ok=False)
    manifest = {'config': build['config'], 'build_id': build['build_id'], 'status': 'RUNNING',
                'fresh_programming': True, 'bitstream_sha256': build['bitstream_sha256'],
                'scripts': [{'path': path, 'sha256': sha(ROOT/path)} for path in
                            ('scripts/program_board.tcl', 'scripts/run_board.tcl',
                             'verification/scripts/run_board.py', 'verification/scripts/board_results.py')]}
    try:
        for phase in ('program', 'run'):
            args = [str(directory), build['build_id']]
            if phase == 'run': args.append(str(trial/'capture.json'))
            command = [a.vivado, '-mode', 'batch', '-notrace', '-source', str(ROOT/f'scripts/{phase}_board.tcl'),
                       '-log', str(trial/f'{phase}.log'), '-journal', str(trial/f'{phase}.jou'), '-tclargs', *args]
            print(f'{phase}: {build["config"]} {build["build_id"]}', flush=True)
            with (trial/f'{phase}.stdout.log').open('w') as log:
                subprocess.run(command, cwd=trial, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run([sys.executable, str(ROOT/'verification/scripts/board_results.py'),
                        '--build-dir', str(directory), '--capture', str(trial/'capture.json'),
                        '--out', str(trial/'result.json')], check=True)
        manifest['status'] = 'PASS'
    except Exception as error:
        manifest.update(status='FAIL', error=str(error))
        raise
    finally:
        (trial/'trial.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__': main()
