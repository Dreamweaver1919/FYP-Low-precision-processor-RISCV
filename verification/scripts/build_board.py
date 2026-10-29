"""Build a pinned KV260 physical design; large outputs stay outside Git."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from run_tests import ROOT, resolve_sources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', choices=['frozen_ff_pulp1', 'overlay_nn1'], required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--vivado', default=os.environ.get('VIVADO', 'E:/vivado/2026.1/Vivado/bin/vivado.bat'))
    a = p.parse_args()
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    image = ROOT/'artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671'
    sources = resolve_sources(a.config, platform='fpga') + [
        ROOT/'rtl/platform/fpga/fyp_nn_system.sv', ROOT/'rtl/platform/fpga/fyp_board_capture.sv',
        ROOT/'rtl/platform/fpga/fyp_board_top.sv']
    incs = [ROOT/'rtl/core/include' if a.config == 'overlay_nn1' else ROOT/'vendor/cv32e40p/rtl/include',
            ROOT/'vendor/cv32e40p/rtl/include', ROOT/'vendor/cv32e40p/rtl/vendor/pulp_platform_common_cells/include']
    selected = set(sources)
    for inc in incs:
        selected.update(x for x in inc.rglob('*') if x.is_file())
    selected.add(ROOT/'scripts/build_board.tcl')
    selected.add(Path(__file__).resolve())
    records = [{'path': x.relative_to(ROOT).as_posix(), 'sha256': sha(x)} for x in sorted(selected)]
    memory = {name: sha(image/name) for name in ('imem.hex', 'dmem.hex', 'expected.json', 'benchmark.json')}
    identity = json.dumps({'config': a.config, 'sources': records, 'memory': memory}, sort_keys=True).encode()
    build_id = hashlib.sha256(identity).hexdigest()[:8]
    for name in memory:
        shutil.copy2(image/name, out/name)
    manifest = {'config': a.config, 'build_id': build_id, 'source_identity_sha256': hashlib.sha256(identity).hexdigest(),
                'sources': records, 'memory_sha256': memory, 'target_period_ns': 20, 'status': 'BUILDING',
                'base_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    def brace(x): return '{'+str(x).replace('\\', '/')+'}'
    values = {'board_sources': '[list '+' '.join(brace(x) for x in sources)+']',
              'board_includes': '[list '+' '.join(brace(x) for x in dict.fromkeys(incs))+']',
              'board_nn': str(int(a.config == 'overlay_nn1')), 'board_out': brace(out),
              'board_build_id': brace(build_id)}
    (out/'inputs.tcl').write_text(''.join(f'set {k} {v}\n' for k,v in values.items()))
    (out/'build.json').write_text(json.dumps(manifest, indent=2)+'\n')
    command = [a.vivado, '-mode', 'batch', '-notrace', '-source', str(ROOT/'scripts/build_board.tcl'),
               '-log', str(out/'vivado.log'), '-journal', str(out/'vivado.jou'), '-tclargs', str(out/'inputs.tcl')]
    with (out/'build.stdout.log').open('w') as log:
        code = subprocess.call(command, cwd=out, stdout=log, stderr=subprocess.STDOUT)
    manifest['exit_code'] = code
    manifest['status'] = 'PASS' if code == 0 and (out/'board.bit').exists() else 'FAIL'
    if manifest['status'] == 'PASS':
        manifest['bitstream_sha256'] = sha(out/'board.bit')
        manifest['probes_sha256'] = sha(out/'board.ltx')
        manifest['implementation'] = json.loads((out/'implementation.json').read_text())
    (out/'build.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ('sources','memory_sha256')}, indent=2))
    return 0 if manifest['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
