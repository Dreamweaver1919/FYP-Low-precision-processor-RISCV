"""Freeze actual OOC inputs and run bounded Vivado jobs without editing originals."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from run_tests import ROOT, config, resolve_sources


def brace(value):
    return '{' + str(value).replace('\\', '/') + '}'


def validate_checkpoint_inputs(previous, current):
    for key in ('config', 'stage'):
        if previous[key] != current[key]:
            raise ValueError('checkpoint configuration/stage mismatch')
    old_hashes = {entry['original']: entry['sha256'] for entry in previous['sources']}
    if any(old_hashes.get(entry['original']) != entry['sha256'] for entry in current['sources']):
        raise ValueError('checkpoint RTL or include headers differ from current inputs')
    if current['stage'] == 'system_ooc':
        for key in ('imem.hex_sha256', 'dmem.hex_sha256', 'signature_digest_words'):
            if previous.get(key) != current.get(key):
                raise ValueError('checkpoint system input mismatch: ' + key)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', choices=['frozen_ff_pulp1','overlay_nn0','overlay_nn1'], required=True)
    p.add_argument('--stage', choices=['core_ooc','system_ooc'], default='core_ooc')
    p.add_argument('--clock-ns', type=float, default=10)
    p.add_argument('--timeout', type=int, default=1800)
    p.add_argument('--image-dir', type=Path)
    p.add_argument('--reuse-synth', type=Path, help='Use a previously synthesized checkpoint with identical sources/configuration; re-place and route at this period')
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    run_id = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    out = (a.out or ROOT/f'artifacts/fpga/{a.config}/{a.stage}/{a.clock_ns:g}ns/{run_id}').resolve()
    out.mkdir(parents=True, exist_ok=True)
    cfg = config(a.config)
    meta = {'config':a.config,'stage':a.stage,'clock_period_ns':a.clock_ns,
            'part':'xck26-sfvc784-2LV-c','scope':'out_of_context; no board pins/bitstream',
            'status':'RUNNING','sources':[],'started':datetime.datetime.now().isoformat()}
    result_path = out/'run.json'
    try:
        sources = resolve_sources(a.config, platform='fpga')
        if a.stage == 'system_ooc':
            sources.append(ROOT/'rtl/platform/fpga/fyp_nn_system.sv')
            if not a.image_dir: raise ValueError('system_ooc requires --image-dir with common imem.hex/dmem.hex')
            memory_dir = out/'memory'
            memory_dir.mkdir(exist_ok=True)
            for name in ('imem.hex','dmem.hex'):
                shutil.copy2(a.image_dir/name, memory_dir/name)
                meta[name+'_sha256'] = hashlib.sha256((memory_dir/name).read_bytes()).hexdigest()
        snapshot = out/'source'
        frozen_sources = []
        extras = set()
        include_dirs = [ROOT/('rtl/core/include' if cfg['overlay'] else 'vendor/cv32e40p/rtl/include'),
                        ROOT/'vendor/cv32e40p/rtl/include',
                        ROOT/'vendor/cv32e40p/rtl/vendor/pulp_platform_common_cells/include']
        include_dirs = list(dict.fromkeys(include_dirs))
        for directory in include_dirs:
            if directory.exists(): extras.update(x for x in directory.rglob('*') if x.is_file())
        for original in sorted(set(sources)|extras):
            data = original.read_bytes()
            target = snapshot/original.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            meta['sources'].append({'original':str(original),'snapshot':str(target),
                                    'sha256':hashlib.sha256(data).hexdigest()})
        for original in sources: frozen_sources.append(snapshot/original.relative_to(ROOT))
        meta['selected_sources']=[str(x) for x in sources]
        meta['include_dirs']=[str(x) for x in include_dirs]
        if a.reuse_synth:
            previous=json.loads((a.reuse_synth.parent/'run.json').read_text())
            meta['reuse_synth']={'checkpoint':str(a.reuse_synth.resolve()),
                                 'sha256':hashlib.sha256(a.reuse_synth.read_bytes()).hexdigest(),
                                 'original_run':str(a.reuse_synth.parent/'run.json'),
                                 'scope':'same synthesized netlist; new placement and routing at requested clock period'}
        (out/'clock.xdc').write_text(f'create_clock -name fyp_clk -period {a.clock_ns:g} [get_ports clk_i]\n')
        project_name = 'FYP_xpulpnn' if cfg['overlay'] else 'FYP_baseline_ff'
        project_dir = ROOT/'artifacts/vivado'/project_name
        generics = ['COREV_PULP=1','COREV_CLUSTER=0','FPU=0','ZFINX=0']
        if cfg['overlay']: generics.append('COREV_XPULPNN='+str(cfg['nn']))
        if a.stage == 'system_ooc':
            generics = ['COREV_XPULPNN='+str(cfg['nn'])]
            # Absolute captured image paths survive opening the saved project
            # from a different working directory and launching synth_1 in GUI.
            generics += [f'{key}="{(memory_dir/name).as_posix()}"' for key,name in
                         (('IMEM_FILE','imem.hex'),('DMEM_FILE','dmem.hex'))]
            expected_path=a.image_dir/'expected.json'
            if expected_path.exists():
                expected=json.loads(expected_path.read_text())['signature']
                digest_words=next((i for i,x in enumerate(expected) if x is None),len(expected))
                generics.append('SIGNATURE_DIGEST_WORDS='+str(digest_words))
                meta['signature_digest_words']=digest_words
        meta['generics'] = generics
        if a.reuse_synth:
            validate_checkpoint_inputs(previous, meta)
        manifest = out/'sources.tcl'
        variables = {
            'fyp_sources':'[list '+' '.join(brace(x) for x in frozen_sources)+']',
            'fyp_include_dirs':'[list '+' '.join(brace(snapshot/x.relative_to(ROOT)) for x in include_dirs if x.exists())+']',
            'fyp_defines':'[list SYNTHESIS'+(' FYP_OVERLAY' if cfg['overlay'] else '')+']',
            'fyp_generics':'[list '+' '.join(brace(x) for x in generics)+']',
            'fyp_top':brace('fyp_nn_system' if a.stage=='system_ooc' else 'cv32e40p_top'),
            'fyp_project_name':brace(project_name),'fyp_project_dir':brace(project_dir),
            'fyp_output':brace(out),'fyp_clock_ns':str(a.clock_ns),'fyp_stage':brace(a.stage),
            'fyp_clock_xdc':brace(out/'clock.xdc'),
            'fyp_memory_files':'[list '+(' '.join(brace(memory_dir/x) for x in ('imem.hex','dmem.hex')) if a.stage=='system_ooc' else '')+']',
            'fyp_synth_checkpoint':brace(a.reuse_synth.resolve() if a.reuse_synth else '')}
        manifest.write_text(''.join('set '+k+' '+v+'\n' for k,v in variables.items()), encoding='utf-8')
        command = ['E:/vivado/2026.1/Vivado/bin/vivado.bat','-mode','batch','-notrace',
                   '-source',str(ROOT/'scripts/run_ooc.tcl'),'-log',str(out/'vivado.log'),
                   '-journal',str(out/'vivado.jou'),'-tclargs',str(manifest)]
        meta['command'] = command
        result_path.write_text(json.dumps(meta,indent=2)+'\n')
        with (out/'vivado.stdout.log').open('w',encoding='utf-8') as stream:
            process = subprocess.Popen(command,cwd=out,stdout=stream,stderr=subprocess.STDOUT)
            try: code = process.wait(timeout=a.timeout)
            except subprocess.TimeoutExpired:
                # Terminate only this launch and its descendants, never unrelated tools.
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                meta['status']='UNRUNNABLE'; meta['error']='bounded Vivado timeout'
                return 2
        meta['exit_code']=code
        meta['finished']=datetime.datetime.now().isoformat()
        if code or not (out/'metrics.json').exists():
            meta['status']='FAIL'
            meta['error']='Vivado failed or did not reach routed metrics; inspect original logs'
            print((out/'vivado.stdout.log').read_text(errors='replace')[-7000:])
            return 1
        metrics=json.loads((out/'metrics.json').read_text())
        if a.stage == 'system_ooc':
            for name in ('imem.hex','dmem.hex'):
                if hashlib.sha256((memory_dir/name).read_bytes()).hexdigest()!=meta[name+'_sha256']:
                    raise ValueError('captured memory image changed during Vivado: '+name)
        meta['metrics']=metrics
        timing=(out/'timing_routed.rpt').read_text(errors='replace')
        for name in ('WNS','TNS','WHS','THS'):
            # Preserve full original timing report; structured summary uses primary paths.
            meta.setdefault('timing_report',str(out/'timing_routed.rpt'))
        meta['status']='PASS'
        meta['timing_met']=float(metrics['wns_ns'])>=0 and float(metrics['whs_ns'])>=0
        print(json.dumps({'artifact':str(out),'status':meta['status'],
                          'timing_met':meta['timing_met'],'metrics':metrics},indent=2))
        return 0
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        meta['status']='UNRUNNABLE';meta['error']=str(exc)
        print(str(exc),file=sys.stderr)
        return 2
    finally:
        result_path.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    raise SystemExit(main())
