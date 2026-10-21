import argparse
import json
import pathlib


def check(out):
    out=pathlib.Path(out)
    expected=json.loads((out/'expected.json').read_text())
    sim=json.loads((out/'simulation.json').read_text())
    actual=[int(x,16) for x in (out/'actual.hex').read_text().split()]
    errors=[]
    negative_watchdog=expected.get('negative_environment_expected_watchdog',False)
    negative_unmapped=expected.get('negative_environment_expected_unmapped',False)
    if negative_watchdog:
        if sim['outcome']!=2 or sim['status']!=0: errors.append(f'expected watchdog, got outcome {sim["outcome"]} status={sim["status"]:#x}')
    elif negative_unmapped:
        if sim['outcome']!=1 or sim['protocol_fail']!=1 or sim['data_requests']!=1 or sim.get('qnt_commits')!=0:
            errors.append('unmapped threshold request was not rejected by the environment before commit')
    elif sim['outcome']!=0 or sim['status']!=1: errors.append(f'program outcome {sim["outcome"]} status={sim["status"]:#x}')
    if sim['protocol_fail'] and not negative_unmapped: errors.append('OBI protocol failure')
    if sim['instruction_requests']==0: errors.append('no instruction fetched')
    if 'data_requests' in expected and sim['data_requests']!=expected['data_requests']:
        errors.append(f'data request count expected {expected["data_requests"]}, actual {sim["data_requests"]}')
    if expected['test'] in ('nn_irq','nn_debug','nn_debug_pre','nn_reset','nn_step'):
        if sim.get('event_fired')!=1 or sim.get('qnt_commits')!=1:errors.append('event did not fire or quantization did not commit exactly once')
        if expected['test']=='nn_reset':
            if sim.get('reset_count')!=1:errors.append('global reset was not exercised')
        elif sim.get('event_acknowledgments')!=(2 if expected['test']=='nn_step' else 1):errors.append('interrupt/debug acknowledgment count mismatch')
        if expected['test']=='nn_step' and sim.get('step_flush_cycles',0)==0:errors.append('single-step did not hold DBG_FLUSH during qnt')
    if not negative_watchdog and not negative_unmapped and 'qnt_issues' in sim:
        if sim['qnt_issues']!=sim['qnt_retire_events'] or sim['qnt_issues']!=sim['qnt_commits']:
            errors.append('qnt ID acceptance / minstret event / commit counts differ')
    if expected.get('suite')=='obi_depth2' and sim.get('max_qnt_outstanding',0)!=2:errors.append('two outstanding qnt requests were not exercised')
    if expected.get('suite')=='final_wb' and sim.get('wb_hold_cycles',0)<6:errors.append('final writeback hold was not exercised')
    if not negative_watchdog and expected['test']=='nn_quant' and sim.get('qnt_commits')!=len(expected['signature']):errors.append('quantization commit count mismatch, including x0')
    mismatch=len(actual)!=len(expected['signature']) or any(e is not None and e!=a for e,a in zip(expected['signature'],actual))
    if mismatch:
        errors.append(f'signature differs: expected {len(expected["signature"])} words, actual {len(actual)}')
        for n,(e,a) in enumerate(zip(expected['signature'],actual)):
            if e is not None and e!=a:
                errors.append(f'word {n}: expected {e:08x}, actual {a:08x}')
                if len(errors)>=12: break
    bench=None
    if (out/'benchmark.json').exists() and len(actual)==len(expected['signature']):
        info=json.loads((out/'benchmark.json').read_text());bench=[]
        def metric(at):
            return {'cycles':actual[at]|(actual[at+1]<<32),'instructions':actual[at+2]|(actual[at+3]<<32)}
        for n,data in enumerate(info['datasets']):
            at=info['metrics_offset']+n*info['metrics_per_dataset']
            prep,legacy,native=metric(at),metric(at+4),metric(at+8)
            if prep['cycles']==0 or legacy['cycles']==0:errors.append('missing preparation or legacy cycle measurement')
            if sim.get('nn_capability',0) and native['cycles']==0:errors.append('missing native cycle measurement')
            scalar=metric(at+12) if info['metrics_per_dataset']==16 else None
            bench.append({**data,'preparation':prep,'legacy_dot8':legacy,'native_nn':native,'scalar':scalar,
                          'primary_speedup':legacy['cycles']/native['cycles'] if native['cycles'] else None,
                          'end_to_end_speedup':(prep['cycles']+legacy['cycles'])/(prep['cycles']+native['cycles']) if native['cycles'] else None})
        empty=metric(info['metrics_offset']+len(info['datasets'])*info['metrics_per_dataset'])
        throughput=[]
        if 'throughput_offset' in info:
            for n,q in enumerate((4,2)):
                at=info['throughput_offset']+n*8
                throughput.append({'q':q,'dependent_sdot_instructions':128,'legacy_dot8':metric(at),'native_nn':metric(at+4)})
        (out/'benchmark_results.json').write_text(json.dumps({'status':'FAIL' if errors else 'PASS','datasets':bench,'empty_bracket':empty,
                                                            'overhead_subtracted':False,'throughput':throughput},indent=2)+'\n')
    result={'status':'FAIL' if errors else 'PASS','test':expected['test'],'seed':expected['seed'],
            'checked_words':len(actual),'errors':errors,'simulation':sim}
    if negative_watchdog: result['negative_environment_expected_watchdog']=True
    if negative_unmapped: result['negative_environment_expected_unmapped']=True
    if bench is not None:result['benchmark']=bench
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    r=check(a.out);print(json.dumps(r));raise SystemExit(0 if r['status']=='PASS' else 1)
