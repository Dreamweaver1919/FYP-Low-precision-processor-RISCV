"""Public-runner implementation; no external source edits or shared build cleanup."""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from build_sw import build
from check_results import check
from prepare_sources import prepare
from generate_vectors import generate as generate_vectors

ROOT=pathlib.Path(__file__).resolve().parents[2]
VIVADO=pathlib.Path('E:/vivado/2026.1/Vivado/bin')
LAST_RUN={}


class RunnerFailure(RuntimeError):
    def __init__(self, phase, message):
        super().__init__(message)
        self.phase=phase


def classify_failure(phase, error):
    """A simulator that starts and exits nonzero has executed DUT code."""
    return 'FAIL' if phase=='simulate' else 'UNRUNNABLE'


def artifact_dir(cfgname,suite,seed):
    runid=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out=ROOT/f'artifacts/verification/{cfgname}/{suite}/{seed}/{runid}'
    out.mkdir(parents=True)
    return out


def run_unit(cfgname,suite,seed):
    out=artifact_dir(cfgname,suite,seed)
    try:
        if suite=='quant_unit':
            invoke([sys.executable,ROOT/'verification/scripts/run_quant_unit.py','--seed',str(seed),'--out',out],out,'unit.stdout.log')
            report=json.loads((out/'run.json').read_text())
            result={'status':report['status'],'suite':suite,'results':report['results']}
        else:
            unit={'arith_unit':'alu','dotp_unit':'dotp','decode':'decoder'}[suite]
            args=['C:/Users/CEG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe','-NoProfile','-File',
                  ROOT/'verification/scripts/run_arithmetic_units.ps1','-Unit',unit,'-Out',out]
            if unit!='decoder':
                generate_vectors(out/'vectors',seed)
                args += ['-Vectors',out/'vectors'/('alu.hex' if unit=='alu' else 'dot.hex')]
            invoke(args,out,'unit.stdout.log')
            result=json.loads((out/'result.json').read_text())
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    except (OSError,RuntimeError,subprocess.SubprocessError) as e:
        result={'status':classify_failure(getattr(e,'phase',None),e),'error':str(e)}
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    LAST_RUN.clear();LAST_RUN.update({'artifact':str(out),**result})
    print(json.dumps(LAST_RUN,indent=2))
    return 0 if result['status']=='PASS' else 1 if result['status']=='FAIL' else 2


def run_group(cfgname,suite,children,seed,max_cycles,grant_max,response_max):
    out=artifact_dir(cfgname,suite,seed);results=[];exit_code=0
    for child in children:
        code=run(cfgname,child,seed,max_cycles,grant_max,response_max)
        results.append(dict(LAST_RUN));exit_code=max(exit_code,code)
    summary={'status':'PASS' if exit_code==0 else 'UNRUNNABLE' if exit_code==2 else 'FAIL','suite':suite,'children':results}
    (out/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
    LAST_RUN.clear();LAST_RUN.update({'artifact':str(out),**summary})
    print(json.dumps({'artifact':str(out),'status':summary['status'],'children':len(results)}))
    return exit_code


def config(name):
    return json.loads((ROOT/'verification/manifests/configs.json').read_text())[name]


def resolve_sources(name, platform=None):
    prepare()
    cfg=config(name)
    result=[]
    text=(ROOT/'docs/investigation/baseline/baseline.prj').read_text()
    for original in re.findall(r'"([^"]+)"',text):
        if original.endswith('glbl.v'): continue
        if original.endswith('cv32e40p_clock_gate.sv'):
            path=ROOT/f'rtl/platform/{platform or cfg["platform"]}/cv32e40p_clock_gate.sv'
        else:
            relative=original.split('/rtl/',1)[1]
            if relative=='cv32e40p_register_file_latch.sv' and cfg['rf']=='ff': relative='cv32e40p_register_file_ff.sv'
            overlay=ROOT/'rtl/core'/relative
            path=overlay if cfg['overlay'] and overlay.exists() else ROOT/'vendor/cv32e40p/rtl'/relative
        if not path.exists(): raise FileNotFoundError(path)
        result.append(path)
    if cfg['overlay']:
        result += sorted((ROOT/'rtl/nn').glob('*.sv'))
    if len(result)!=len(set(result)): raise ValueError('duplicate source in resolved manifest')
    return result


def invoke(args,out,log,timeout=600,phase='prepare'):
    with (out/log).open('w') as f:
        proc=subprocess.run([str(x) for x in args],cwd=out,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    if proc.returncode: raise RunnerFailure(phase,f'{args[0]} failed {proc.returncode}; see {out/log}')


def run(cfgname,suite,seed=1,max_cycles=200000,grant_max=0,response_max=1):
    cfg=config(cfgname)
    if suite=='parameter_matrix':
        from run_arithmetic_matrix import run as run_matrix
        result=run_matrix();LAST_RUN.clear();LAST_RUN.update(result)
        return 0 if result['status']=='PASS' else 1
    if suite in ('disabled_frozen','disabled_overlay'):
        return run('frozen_ff_pulp1' if suite=='disabled_frozen' else 'overlay_nn0','disabled_isa',seed,max_cycles,grant_max,response_max)
    if suite in ('arith_unit','dotp_unit','decode','quant_unit'):return run_unit(cfgname,suite,seed)
    groups={'isa':['arith_isa','quant_isa','quant_bad_base'] if cfg['nn'] else ['arith_isa'],
            'regression':['smoke','legacy_isa','legacy_misc'],
            'reset_irq_debug':[f'{mode}_phase{phase}' for mode in ('irq','debug','reset') for phase in range(6)] + ['single_step','final_wb']}
    groups['all']=['arith_unit','dotp_unit','decode','parameter_matrix','disabled_frozen','disabled_overlay','quant_unit','regression','isa','dependencies','wrong_path','hwloop','obi_stress','obi_depth2','reset_irq_debug','negative_env','negative_unmapped','bench','bench_wait']
    if suite in groups:return run_group(cfgname,suite,groups[suite],seed,max_cycles,grant_max,response_max)
    test={'smoke':'rv32_smoke','arith_isa':'nn_arithmetic','quant_isa':'nn_quant','quant_bad_base':'nn_quant_bad_base',
          'legacy_isa':'legacy_xpulp','arith_stress':'nn_arithmetic','obi_stress':'nn_quant','bench':'bench_common',
          'dependencies':'dependencies','wrong_path':'wrong_path','legacy_misc':'legacy_misc','hwloop':'hwloop','disabled_isa':'disabled_isa',
          'irq':'nn_irq','debug':'nn_debug','reset':'nn_reset','single_step':'nn_step','final_wb':'nn_hold',
          'negative_env':'nn_quant','negative_unmapped':'nn_unmapped','obi_depth2':'nn_quant','bench_wait':'bench_common'}.get(suite.split('_phase')[0])
    if suite=='debug_phase4': test='nn_debug_pre'
    if test is None: raise ValueError(f'suite not implemented yet: {suite}')
    if suite=='obi_stress' and grant_max==0 and response_max==1:grant_max,response_max=7,11
    if suite=='obi_depth2' and grant_max==0 and response_max==1:grant_max,response_max=0,17
    if suite=='negative_env' and max_cycles==200000:max_cycles=2000
    if suite=='bench' and max_cycles==200000:max_cycles=10000000
    if suite=='bench_wait':
        grant_max,response_max=2,4
        if max_cycles==200000:max_cycles=50000000
    out=artifact_dir(cfgname,suite,seed)
    meta={'config':cfgname,'suite':suite,'seed':seed,'max_cycles':max_cycles,'grant_max':grant_max,'response_max':response_max,'fixed_wait':suite=='bench_wait'}
    try:
        sources=resolve_sources(cfgname)
        meta['sources']=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]
        verification_inputs = [ROOT/'verification/tb/obi_memory_agent.sv',ROOT/'verification/tb/tb_core_program.sv']
        for directory in ('verification/scripts','verification/model','verification/manifests','verification/sw'):
            verification_inputs += [p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.sv','.S','.c','.h','.ld','.json')]
        meta['verification_inputs']=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(verification_inputs))]
        (out/'run.json').write_text(json.dumps(meta,indent=2)+'\n')
        build(test,'xpulpnn' if test.startswith('nn_') or test=='bench_common' else 'xpulp' if test=='legacy_xpulp' else 'rv32imc',seed,out)
        if suite=='negative_env':
            expected=json.loads((out/'expected.json').read_text())
            expected['negative_environment_expected_watchdog']=True
            expected['signature']=[]
            expected.pop('data_requests',None)
            (out/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
        expected=json.loads((out/'expected.json').read_text())
        expected['suite']=suite
        if suite=='negative_unmapped':
            expected['negative_environment_expected_unmapped']=True
            expected['signature']=[]
        (out/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
        sources += [ROOT/'verification/tb/obi_memory_agent.sv',ROOT/'verification/tb/tb_core_program.sv']
        glbl=pathlib.Path('E:/vivado/2026.1/Vivado/data/verilog/src/glbl.v')
        (out/'sources.prj').write_text(''.join(f'sv xil_defaultlib "{p.as_posix()}"\n' for p in sources)+f'verilog xil_defaultlib "{glbl.as_posix()}"\n')
        args=[VIVADO/'xvlog.bat','--sv','--prj','sources.prj','-i',ROOT/'vendor/cv32e40p/rtl/include',
              '-i',ROOT/'rtl/core/include','-i',ROOT/'vendor/cv32e40p/rtl/vendor/pulp_platform_common_cells/include','--log','xvlog.log']
        if cfg['overlay']: args += ['-d','FYP_OVERLAY']
        invoke(args,out,'xvlog.stdout.log')
        generics={'NN_ENABLE':cfg['nn'],'GRANT_MAX':grant_max,'RESPONSE_MAX':response_max,'SEED':seed,'MAX_CYCLES':max_cycles}
        if suite=='negative_env': generics['NEGATIVE_ENV']=1
        if suite=='obi_depth2': generics['DATA_DEPTH']=2
        if suite=='final_wb': generics['FINAL_WB_HOLD']=1
        if suite=='bench_wait': generics['FIXED_WAIT']=1
        if test in ('nn_irq','nn_debug','nn_debug_pre','nn_reset','nn_step'):
            generics['EVENT_MODE']={'nn_irq':1,'nn_debug':2,'nn_debug_pre':2,'nn_reset':3,'nn_step':4}[test]
            generics['EVENT_PHASE']=int(suite.split('_phase')[1]) if '_phase' in suite else 0
            if test=='nn_step':generics['EVENT_PHASE']=4
        (out/'xelab.args').write_text(''.join(f'--generic_top "{key}={value}"\n' for key,value in generics.items()))
        invoke([VIVADO/'xelab.bat','xil_defaultlib.tb_core_program','xil_defaultlib.glbl','-L','unisims_ver',
                '--file','xelab.args','--mt','2','--timescale','1ns/1ps','--snapshot','run_core','--log','xelab.log'],out,'xelab.stdout.log')
        (out/'run.tcl').write_text('run all\nquit\n')
        invoke([VIVADO/'xsim.bat','run_core','--tclbatch','run.tcl','--log','xsim.log'],out,'xsim.stdout.log',phase='simulate')
        result=check(out)
    except (OSError,RuntimeError,subprocess.SubprocessError) as e:
        result={'status':classify_failure(getattr(e,'phase',None),e),'error':str(e)}
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'artifact':str(out),**result},indent=2))
    LAST_RUN.clear();LAST_RUN.update({'artifact':str(out),**result})
    return 0 if result['status']=='PASS' else 1 if result['status']=='FAIL' else 2


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--suite',required=True)
    p.add_argument('--seed',type=int,default=1);p.add_argument('--max-cycles',type=int,default=200000)
    p.add_argument('--grant-max',type=int,default=0);p.add_argument('--response-max',type=int,default=1)
    a=p.parse_args()
    raise SystemExit(run(a.config,a.suite,a.seed,a.max_cycles,a.grant_max,a.response_max))
