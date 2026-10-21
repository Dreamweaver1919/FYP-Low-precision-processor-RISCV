"""Collect original Vivado reports and wrapper-image proof without rerunning tools."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]


def resources(path):
    names={'lut':'CLB LUTs','ff':'Register as Flip Flop','latch':'Register as Latch',
           'dsp':'DSPs','bram_tiles':'Block RAM Tile','ramb36':'RAMB36/FIFO',
           'ramb18':'RAMB18','bufgce':'BUFGCE','bufgce_div':'BUFGCE_DIV','bufgctrl':'BUFGCTRL'}
    found={}
    for line in path.read_text(errors='replace').splitlines():
        columns=[x.strip().rstrip('*') for x in line.split('|')]
        if len(columns)<4: continue
        for name,label in names.items():
            if name not in found and columns[1]==label:
                try: found[name]=float(columns[2]) if '.' in columns[2] else int(columns[2])
                except ValueError: pass
    return found


def timing(path):
    text=path.read_text(errors='replace');lines=text.splitlines();found={}
    for i,line in enumerate(lines):
        if 'WNS(ns)' in line and 'TNS(ns)' in line and 'WHS(ns)' in line:
            for candidate in lines[i+1:i+8]:
                values=candidate.split()
                if len(values)>=8:
                    try:
                        numbers=[float(x) for x in values]
                        found.update(dict(zip(['wns_ns','tns_ns','setup_failing_endpoints','setup_total_endpoints',
                                               'whs_ns','ths_ns','hold_failing_endpoints','hold_total_endpoints'],numbers[:8])))
                        break
                    except ValueError: continue
            break
    found['checks']={name:int(value) for name,value in re.findall(r'checking\s+(\w+)\s+\((\d+)\)',text)}
    return found


def summarize():
    result={'scope':'OOC synthesis/place/route and actual wrapper simulation; no board deployment',
            'part':'xck26-sfvc784-2LV-c','runs':[], 'wrapper_runs':[],
            'board_programming':'NOT_RUN','bitstream':'NOT_RUN'}
    for path in sorted((ROOT/'artifacts/fpga').rglob('run.json')):
        meta=json.loads(path.read_text());directory=path.parent
        entry={'artifact':str(directory),'status':meta.get('status','UNKNOWN'),'config':meta.get('config'),
               'stage':meta.get('stage'),'source_hashes':meta.get('sources',[]),
               'constraints':{'period_ns':meta.get('clock_period_ns'),'clock_port':'clk_i',
                              'clock_name':'fyp_clk','mode':'out_of_context',
                              'input_output_delays':'not specified; exact counts retained below',
                              'false_paths':'none added','device':meta.get('part')},
               'run_metadata':str(path),'log':str(directory/'vivado.stdout.log')}
        for kind in ('routed','synth'):
            util=directory/f'utilization_{kind}.rpt';report=directory/f'timing_{kind}.rpt'
            if util.exists(): entry[kind+'_resources']=resources(util)
            if report.exists(): entry[kind+'_timing']=timing(report)
            if util.exists() or report.exists():
                entry[kind+'_evidence']={'utilization':str(util),'timing':str(report)}
        entry['matches_current_sources']=all(Path(x['original']).exists() and
            hashlib.sha256(Path(x['original']).read_bytes()).hexdigest()==x['sha256']
            for x in entry['source_hashes']) if entry['source_hashes'] else None
        for key in ('error','exit_code','timing_met','signature_digest_words','imem.hex_sha256','dmem.hex_sha256'):
            if key in meta: entry[key]=meta[key]
        for name in ('routed.dcp','synth.dcp','clocks.rpt','clock_utilization.rpt','drc.rpt'):
            evidence=directory/name
            if evidence.exists(): entry.setdefault('evidence',{})[name]=str(evidence)
        result['runs'].append(entry)
    candidates=[]
    for path in (ROOT/'artifacts/verification').glob('system_wrapper*/run.json'):
        meta=json.loads(path.read_text());candidates.append((path,meta))
        result['wrapper_runs'].append({'artifact':str(path.parent),**{k:v for k,v in meta.items() if k!='sources'}})
    latest={}
    for path,meta in sorted(candidates,key=lambda item:item[0].stat().st_mtime):
        if meta.get('status')=='PASS' and meta.get('test')=='bench_common': latest[meta['config']]=(path,meta)
    if 'frozen_ff_pulp1' in latest and 'overlay_nn1' in latest:
        bpath,baseline=latest['frozen_ff_pulp1'];epath,extended=latest['overlay_nn1']
        result['common_rom_proof']={
            'baseline':str(bpath),'extension':str(epath),
            'imem_equal':baseline['imem_sha256']==extended['imem_sha256'],
            'dmem_equal':baseline['dmem_sha256']==extended['dmem_sha256'],
            'imem_sha256':baseline['imem_sha256'],'dmem_sha256':baseline['dmem_sha256'],
            'deterministic_digest_equal':baseline['signature']==extended['signature'],
            'deterministic_digest':baseline['signature'],'verified_result_words':baseline['digest_words'],
            'scope':'complete output words verified in wrapper bench; runtime words retained separately',
            'whole_program_cycles_comparable':False,
            'reason':'NN-enabled ROM executes the baseline kernels plus additional native kernels'}
        # The actual wrapper's memory service differs from the core TB agent.
        # Extract matching measured intervals from this platform itself.
        common_info=bpath.parent/'benchmark.json'
        nn_info=epath.parent/'benchmark.json'
        manifests_match=common_info.exists() and nn_info.exists() and hashlib.sha256(common_info.read_bytes()).hexdigest()==baseline.get('benchmark_manifest_sha256')==extended.get('benchmark_manifest_sha256')==hashlib.sha256(nn_info.read_bytes()).hexdigest()
        if manifests_match:
            info=json.loads(common_info.read_text())
            base_words=[int(x,16) for x in (bpath.parent/'actual.hex').read_text().split()]
            nn_words=[int(x,16) for x in (epath.parent/'actual.hex').read_text().split()]
            def counter(words,at):return words[at]|(words[at+1]<<32)
            metrics=[]
            for n,data in enumerate(info['datasets']):
                at=info['metrics_offset']+n*info['metrics_per_dataset']
                bcycles=counter(base_words,at+4);ncycles=counter(nn_words,at+8)
                bprep=counter(base_words,at);nprep=counter(nn_words,at)
                metrics.append({'name':data['name'],'baseline_legacy_cycles':bcycles,
                    'extension_native_cycles':ncycles,'baseline_preparation_cycles':bprep,
                    'extension_preparation_cycles':nprep,'kernel_cycle_speedup':bcycles/ncycles,
                    'including_preparation_speedup':(bprep+bcycles)/(nprep+ncycles)})
            result['wrapper_kernel_metrics']=metrics
            good={cfg:sorted({r['constraints']['period_ns'] for r in result['runs']
                if r['config']==cfg and r['stage']=='system_ooc' and r.get('timing_met') and
                r.get('matches_current_sources') and r.get('imem.hex_sha256')==baseline['imem_sha256'] and
                r.get('dmem.hex_sha256')==baseline['dmem_sha256']}) for cfg in ('frozen_ff_pulp1','overlay_nn1')}
            common=sorted(set(good['frozen_ff_pulp1'])&set(good['overlay_nn1']))
            if common:
                period=common[0]
                result['wrapper_time_estimate']={'common_routed_period_ns':period,
                    'scope':'cycles measured in wrapper simulation times routed clock constraint; not board wall-clock measurement',
                    'kernels':[{'name':r['name'],'baseline_ns':r['baseline_legacy_cycles']*period,
                    'extension_ns':r['extension_native_cycles']*period,'speedup':r['kernel_cycle_speedup']} for r in metrics]}
    result['generated_projects']=[str(x) for x in (ROOT/'artifacts/vivado').rglob('*.xpr')]
    target=ROOT/'artifacts/fpga/summary.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'summary':str(target),'runs':len(result['runs']),
                      'wrapper_runs':len(result['wrapper_runs']),
                      'common_rom_proof':result.get('common_rom_proof')},indent=2))
    return result


if __name__=='__main__': summarize()
