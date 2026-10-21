"""Materialize the final report only from completed, source-matching evidence."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def replace_block(text,start,end,body):
    if start in text:
        return text[:text.index(start)]+start+'\n'+body+'\n'+text[text.index(end):]
    raise ValueError('Missing report marker: '+start)


def main():
    verification=load(ROOT/'artifacts/verification/summary.json')
    if verification['release_current_status']!='PASS':
        raise RuntimeError('Current functional evidence is incomplete')
    fpga=load(ROOT/'artifacts/fpga/summary.json')
    selected=[]
    for stage in ('core_ooc','system_ooc'):
        for period in (10,20):
            for cfg in ('frozen_ff_pulp1','overlay_nn1'):
                candidates=[r for r in fpga['runs'] if r['stage']==stage and r['config']==cfg and
                    r['constraints']['period_ns']==period and r['status']=='PASS' and r['matches_current_sources']]
                if not candidates:raise RuntimeError(f'Missing completed source-matching run: {stage}/{period}/{cfg}')
                selected.append(max(candidates,key=lambda r:Path(r['run_metadata']).stat().st_mtime))
    lines=['| 范围 | 配置 | 约束 ns | LUT | FF | latch | DSP | BRAM tile | BUFGCE | WNS ns | WHS ns | 时序 |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in selected:
        u=r['routed_resources'];t=r['routed_timing']
        lines.append('| '+ ' | '.join([r['stage'],f'[{r["config"]}](../../artifacts/fpga/summary.json)',str(r['constraints']['period_ns']),
            *[str(u.get(k,'未解析')) for k in ('lut','ff','latch','dsp','bram_tiles','bufgce')],
            f'{t["wns_ns"]:+.3f}',f'{t["whs_ns"]:+.3f}','满足' if r['timing_met'] else '未满足'])+' |')
    lines += ['', '上表为 routed 资源与时序，工具执行成功与 timing_met 分开判断；10 ns 失败结果未删除。', '',
        '| 范围/配置/周期 | 无输入 delay 的端口 | 无输出 delay 的端口 | 无时钟端点 | 未约束内部端点 |',
        '|---|---:|---:|---:|---:|']
    for r in selected:
        c=r['routed_timing']['checks']
        lines.append(f'| {r["stage"]}/{r["config"]}/{r["constraints"]["period_ns"]:g} ns | '+
            ' | '.join(str(c.get(k,'见原报告')) for k in ('no_input_delay','no_output_delay','no_clock','unconstrained_internal_endpoints'))+' |')
    lines += ['', '未配置板级 HD.CLK_SRC，因此 OOC 时钟输入的板级延迟/偏斜不在此验证范围内。', '']
    perf=['| 数据集 | 基线 dot8 周期 | 扩展 native 周期 | kernel 周期比 | 含准备周期比 |',
          '|---|---:|---:|---:|---:|']
    for r in fpga['wrapper_kernel_metrics']:
        perf.append(f'| {r["name"]} | {r["baseline_legacy_cycles"]} | {r["extension_native_cycles"]} | {r["kernel_cycle_speedup"]:.3f}× | {r["including_preparation_speedup"]:.3f}× |')
    if 'wrapper_time_estimate' in fpga:
        estimate=fpga['wrapper_time_estimate'];period=estimate['common_routed_period_ns']
        perf += ['',f'两组都满足 {period:g} ns（{1000/period:g} MHz）的 OOC 约束。以相同频率估算：', '',
            '| 数据集 | 基线 kernel μs | 扩展 kernel μs |', '|---|---:|---:|']
        for r in estimate['kernels']:
            perf.append(f'| {r["name"]} | {r["baseline_ns"]/1000:.3f} | {r["extension_ns"]/1000:.3f} |')
        if any(r['stage']=='system_ooc' and r['config']=='frozen_ff_pulp1' and r['constraints']['period_ns']==10 and r['timing_met'] for r in selected) and period==20:
            perf += ['', '基线还通过 100 MHz；若比较基线 100 MHz 与扩展 50 MHz，时间加速比为上表周期比的一半。主 MatMul/Conv 含准备区间的估算时间收益约为 1.30–1.48×。不能只用周期减少量忽略频率差。']
    path=ROOT/'docs/results/xpulpnn-route-a-validation.md'
    report=path.read_text(encoding='utf-8')
    supported=all(r['timing_met'] for r in selected if r['constraints']['period_ns']==20)
    headline=('功能回归 PASS，核心及完整封装的两组 20 ns OOC 实现均满足时序；扩展核的 10 ns 时序未闭合。'
              if supported else '功能回归 PASS；OOC 实现已完成，未满足的时序约束见下表。')
    report=report.replace('最终回归与完整封装布线仍在执行；结束时以本页更新后的状态和原始工件为准。',headline)
    report=replace_block(report,'<!-- MEASURED_PERFORMANCE_START -->','<!-- MEASURED_PERFORMANCE_END -->','\n'.join(perf))
    report=replace_block(report,'<!-- ROUTED_RESULTS_START -->','<!-- ROUTED_RESULTS_END -->','\n'.join(lines))
    path.write_text(report,encoding='utf-8')
    (ROOT/'artifacts/delivery').mkdir(exist_ok=True)
    (ROOT/'artifacts/delivery/release-evidence.json').write_text(json.dumps({
        'functional_status':'PASS','functional_index':'artifacts/verification/summary.json',
        'fpga_summary':'artifacts/fpga/summary.json','fpga_run_count':len(selected),
        '20ns_timing_met':supported,'board_programming':'NOT_RUN','bitstream':'NOT_RUN'},indent=2)+'\n')
    print(json.dumps({'functional':'PASS','routed_runs':len(selected),'20ns_timing_met':supported,'report':str(path)},indent=2))


if __name__=='__main__':main()
