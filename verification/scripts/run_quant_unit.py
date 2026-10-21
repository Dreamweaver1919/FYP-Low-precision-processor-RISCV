"""Run the standalone quantizer with XSim; no core source/model dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path('E:/vivado/2026.1/Vivado/bin')


def run_tool(name, args, cwd, log):
    command = [str(TOOLS / (name + '.bat')), *map(str, args)]
    started = time.monotonic()
    completed = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True,
                               encoding='utf-8', errors='replace', timeout=180)
    log.write_text(completed.stdout, encoding='utf-8')
    return {'command': command, 'exit_code': completed.returncode,
            'elapsed_seconds': round(time.monotonic() - started, 3),
            'log': str(log)}, completed.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, nargs='+', default=[1, 42, 20261020])
    parser.add_argument('--random-per-q', type=int, default=2000)
    parser.add_argument('--out', type=Path, default=ROOT / 'artifacts/verification/quant_unit')
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / 'rtl/nn/cv32e40p_nn_quant.sv', ROOT / 'verification/tb/tb_nn_quant.sv']
    metadata = {'suite': 'quant_unit', 'scope': 'standalone unit only',
                'seeds': args.seed, 'random_per_q': args.random_per_q,
                'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sources if p.exists()}, 'commands': [], 'results': []}
    metadata_path = output / 'run.json'
    try:
        build = output / 'build'
        build.mkdir(exist_ok=True)
        # An unresolved DUT is deliberately allowed through xvlog so xelab provides
        # the TDD missing-module failure rather than an unrelated runner error.
        for name, tool_args in [('xvlog', ['-sv', *[p for p in sources if p.exists()]]),
                                ('xelab', ['tb_nn_quant', '-s', 'quant_unit', '--debug', 'typical', '--mt', '2'])]:
            result, stdout = run_tool(name, tool_args, build, output / (name + '.stdout.log'))
            metadata['commands'].append(result)
            if result['exit_code']:
                metadata['status'] = 'FAIL'
                metadata['failure'] = name + ' failed'
                print(stdout[-7000:])
                return 1
        for seed in args.seed:
            target = output / ('seed_' + str(seed))
            target.mkdir(exist_ok=True)
            sv_result = target / 'result_sv.json'
            if sv_result.exists():
                sv_result.unlink()
            # loader.bat reparses bare '=' arguments. XSim's own options file
            # preserves each plusarg as one value without another shell layer.
            argfile = target / 'xsim.args'
            argfile.write_text('\n'.join('-testplusarg "' + value + '"' for value in [
                'SEED=' + str(seed), 'RANDOM_PER_Q=' + str(args.random_per_q),
                'RESULT=' + sv_result.as_posix(),
                'TRACE=' + (target / 'transactions.csv').as_posix()]) + '\n', encoding='utf-8')
            tool_args = ['quant_unit', '-runall', '-f', argfile]
            result, stdout = run_tool('xsim', tool_args, build, target / 'xsim.stdout.log')
            metadata['commands'].append(result)
            if result['exit_code'] or not sv_result.exists():
                metadata['status'] = 'FAIL'
                metadata['failure'] = 'xsim failed or produced no structured result for seed ' + str(seed)
                print(stdout[-7000:])
                return 1
            report = json.loads(sv_result.read_text(encoding='utf-8'))
            metadata['results'].append(report)
            if (report.get('status') != 'PASS' or report.get('random_q2') != args.random_per_q
                    or report.get('random_q4') != args.random_per_q
                    or report.get('ideal_q2_cycles') != 5 or report.get('ideal_q4_cycles') != 9):
                metadata['status'] = 'FAIL'
                metadata['failure'] = 'structured result/coverage mismatch'
                print(stdout[-7000:])
                return 1
            print(f"PASS quant_unit seed={seed} operations={report['operations']} "
                  f"reads={report['reads']} ideal_q2=5 ideal_q4=9")
        metadata['status'] = 'PASS'
        return 0
    except (OSError, subprocess.TimeoutExpired) as exc:
        metadata['status'] = 'UNRUNNABLE'
        metadata['failure'] = str(exc)
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        metadata_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
