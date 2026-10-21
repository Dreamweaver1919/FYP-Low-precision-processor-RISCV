"""Run the controller block test and retain an immutable structured evidence artifact."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path('E:/vivado/2026.1/Vivado/bin')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = ROOT / 'artifacts/verification/controller_unit/1' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out.mkdir(parents=True)
    pkg = ROOT / 'rtl/core/include/cv32e40p_pkg.sv'
    if not pkg.exists(): pkg = ROOT / 'vendor/cv32e40p/rtl/include/cv32e40p_pkg.sv'
    files = [pkg, ROOT / 'rtl/core/cv32e40p_controller.sv', ROOT / 'verification/tb/tb_nn_controller.sv']
    result = {'suite': 'controller_unit', 'artifact': str(out), 'sources': {str(p.relative_to(ROOT)): digest(p) for p in files}, 'commands': [], 'status': 'UNRUNNABLE'}
    try:
        (out / 'sources.prj').write_text(''.join(f'sv xil_defaultlib "{p.as_posix()}"\n' for p in files), encoding='utf-8')
        (out / 'run.tcl').write_text('run all\nquit\n', encoding='utf-8')
        for tool, args in [('xvlog', ['--sv', '--prj', 'sources.prj']), ('xelab', ['xil_defaultlib.tb_nn_controller', '--snapshot', 'ctrl_unit', '--mt', '2']), ('xsim', ['ctrl_unit', '--tclbatch', 'run.tcl'])]:
            command = [str(TOOLS / (tool + '.bat')), *args]; started = time.monotonic()
            completed = subprocess.run(command, cwd=out, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', timeout=180)
            log = out / (tool + '.log'); log.write_text(completed.stdout, encoding='utf-8')
            result['commands'].append({'command': command, 'exit_code': completed.returncode, 'elapsed_seconds': round(time.monotonic() - started, 3), 'log': str(log)})
            if completed.returncode or 'ERROR:' in completed.stdout or 'Fatal:' in completed.stdout:
                result.update(status='FAIL', failure=f'{tool} failed'); return 1
            if tool == 'xsim' and 'PASS NN controller' not in completed.stdout:
                result.update(status='FAIL', failure='xsim completed without PASS NN controller marker'); return 1
        result['status'] = 'PASS'; return 0
    except (OSError, subprocess.TimeoutExpired) as exc:
        result.update(status='UNRUNNABLE', failure=f'{type(exc).__name__}: {exc}'); return 2
    finally:
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
