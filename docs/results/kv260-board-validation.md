# KV260 实板验证报告

日期：2026-10-29。CV32E40P frozen baseline 与 XPulpNN 扩展核均已在连接的 KV260 上加载 bitstream 并执行共同 benchmark。最终每个配置各进行两次独立重新烧录，四次均 PASS；同配置两次读回的全部 472 字及总周期完全一致。原始读回和可重新计算的指标见 [证据汇总](board-2026-10-29/summary.json)。

## 板上运行的设计及身份

板级 top 为 [`fyp_board_top`](../../rtl/platform/fpga/fyp_board_top.sv)。PS 提供 PL0 时钟和复位，RISC-V 核、64 KiB IMEM、64 KiB DMEM 均位于 PL。程序结束后，现有封装的签名扫描输出被动写入独立的 512×32 capture BRAM；JTAG VIO 控制启动并读取结果。该捕获路径不参与 CPU 执行时的指令或数据存储器访问。

| 项目 | frozen baseline | XPulpNN 扩展核 |
|---|---|---|
| 配置 | `frozen_ff_pulp1` | `overlay_nn1` |
| 构建标识，USR_ACCESS 与 VIO 双重核对 | `ea507b7d` | `f584e920` |
| 实测状态值 | `3`：done、pass | `19`：NN、done、pass |
| 最终独立重新烧录次数 | 2 | 2 |
| 每次读回 | 472 字 | 472 字 |
| 确定性输出 | 356/356 匹配 | 356/356 匹配 |
| 确定性 fold | `0x39a7d0b7` | `0x39a7d0b7` |
| 全程序周期，每次相同 | 2,874,743 | 2,927,425 |

状态同时要求 running=0、overflow=0。每次测试先核对源码、ROM、bitstream、LTX 的 SHA-256，再重新编程恢复 RAM 初值；旧 done 或非零捕获计数会被拒绝。构建标识取输入清单 SHA-256 的前 32 位，完整哈希及 bitstream 哈希保存在 [baseline manifest](board-2026-10-29/baseline/build.json) 和 [NN manifest](board-2026-10-29/nn/build.json)。32 位硬件标识用于匹配本次构建，完整哈希用于文件完整性核对。

最终板上保留扩展核 `f584e920`，程序已运行完成并保持 PASS 结果。设备 IDCODE `04724093`、DNA、读回时间和活动心跳见 [最终只读检查](board-2026-10-29/final-board.json)。这里的“运行仓库内容”由当前源文件哈希、共同 ROM、实际加载文件哈希、硬件双重标识和实际结果联合支持。

## 时钟与完整器件实现

本次沿用已初始化且 PL 可用的 PS 状态。只调整 PL0 分频，不修改 PLL、DDR 或 PS 处理器复位，也未执行额外的隔离解除写入。IOPLL_CTRL=`0x00015a00`、FRAC_CFG=0、PLL_STATUS=`0x1b`；PL0_REF_CTRL 调整后为 `0x01011e00`。以标称 33.333333 MHz PS 参考时钟计算：IOPLL 为约 1.5 GHz，PL0 除以 30，得到标称 **50 MHz**。测试期间及最终只读寄存器快照均保存；这是寄存器推导频率，没有使用示波器测量。

Vivado PS IP 初始生成的时钟约束为 20.625 ns。最终流程明确将该时钟收紧至 **20.000 ns**，重新检查 routed 设计并生成最终 bitstream；没有把较宽松约束的 PASS 冒充 50 MHz PASS。

| 完整板级 top，含 PS/VIO/debug/capture | LUT | FF | BRAM tile | DSP | WNS ns | WHS ns | DRC error |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 8,816 | 4,903 | 32.5 | 7 | +7.693 | +0.010 | 0 |
| XPulpNN | 10,533 | 5,146 | 32.5 | 7 | +0.338 | +0.012 | 0 |

两组时序报告的 no_clock、unconstrained_internal_endpoints、no_input_delay、no_output_delay 均为 0；top 无外部 PL 数据引脚。DRC 及 methodology 警告保留在原始报告中，未宣称零警告。板级资源含调试设施，不能与历史 core/system OOC 资源直接混作同一范围。原始 [baseline 报告](board-2026-10-29/baseline) 与 [NN 报告](board-2026-10-29/nn) 均已发布。

## 实测性能

以下是板上 `mcycle/minstret` 记录的区间，其中计数器读取框架开销未扣除。legacy 为本项目的 dot8 kernel，含低精度解包、符号扩展和软件量化；scalar 为同一冻结核心的标量实现；native 为扩展核的低精度点积及双通道量化实现。它们都使用固定的合成 Q4/Q2 MatMul、Conv 和尾部数据集，未使用真实模型的准确率数据。

| 数据集 | baseline legacy 周期 | baseline scalar 周期 | native 周期 | legacy/native | scalar/native |
|---|---:|---:|---:|---:|---:|
| matmul_q4 | 61,152 | 41,577 | 3,498 | 17.482× | 11.886× |
| conv_q4 | 587,429 | 388,458 | 25,562 | 22.981× | 15.197× |
| tail_q4 | 4,265 | 2,906 | 322 | 13.245× | 9.025× |
| matmul_q2 | 59,286 | 39,711 | 2,378 | 24.931× | 16.699× |
| conv_q2 | 579,842 | 380,871 | 16,058 | 36.109× | 23.718× |
| tail_q2 | 4,164 | 2,805 | 250 | 16.656× | 11.220× |

两种配置下 preparation、legacy、scalar 的 cycles 和 instret 逐项相同；每个配置内两次全部指标也逐字一致。最终输出区域会被最后执行的 scalar 路径覆盖，因此还必须检查固件 PASS：固件在每条执行路径结束后均自检结果，native 失败不能被最终 scalar 输出遮盖。板上程序也要求 native 计数非零；baseline 对应计数为零。

加入公共准备过程（含所需数据准备/im2col）后，收益如下。此处为“准备 + kernel”区间，不包含完整系统的 I/O、模型加载或应用调度。

| 数据集 | (准备+legacy)/(准备+native) | (准备+scalar)/(准备+native) | native 时间 μs，按标称 50 MHz 换算 |
|---|---:|---:|---:|
| matmul_q4 | 2.854× | 2.225× | 69.960 |
| conv_q4 | 2.608× | 2.039× | 511.240 |
| tail_q4 | 1.495× | 1.324× | 6.440 |
| matmul_q2 | 2.954× | 2.282× | 47.560 |
| conv_q2 | 2.694× | 2.096× | 321.160 |
| tail_q2 | 1.510× | 1.333× | 5.000 |

MatMul/Conv 相对 scalar 的 kernel 收益为 11.886–23.718×，加入准备后为 2.039–2.282×。legacy 实现尚未达到论文作者的优化程度，以上比值只描述此仓库代码。NN 完整程序多执行 native 路径，所以总周期略大；不能拿完整程序总周期计算加速比。

logical MACs 表示数学上有效乘加，physical lane-MACs 包含 packed dot 的补零 lane。例如 Q2 Conv 的 K=72 补齐至 80，有效 20,736 MAC，对应 23,040 lane-MAC；Q4/Q2 尾部 K=35 分别补齐至 40/48，有效 140 MAC，对应 160/192 lane-MAC。完整数据和 64 位计数均保存在原始 capture 与 summary 中。

## 验证覆盖与限制

被动签名输出的完整封装仿真在两种配置均通过，包含实际共同 ROM、472 字顺序及数据核对。capture 单元验证了 472 字读写、越界拒绝及复位。VIO Tcl 测试覆盖完整无符号 32 位读取、被拆分的常量构建标识和不完整总线拒绝。首次采集遇到的地址格式问题，以及 Tcl `%x` 在 Windows 上的有符号解释问题均已修正；最终四次采集使用修正后的脚本重新编程执行，早期日志留在本机。

本次新增的是实板 benchmark 验证，未把全部随机 ISA/IRQ/debug 仿真重新在板上执行。已有核心 RTL 未改变；修改限于被动输出和板级设施。没有测量功耗、长期稳定性或真实神经网络准确率，也没有完成 100 MHz 扩展核实板验证。烧录使用易失性 JTAG FPGA 配置，未写入 QSPI/启动介质，断电后需要重新加载。

## 复现

工具为 Vivado/XSDB 2026.1、Python 3.12+；完整器件型号 `xck26-sfvc784-2LV-c`。构建输出目录必须不存在。以下从仓库根目录执行；替换工具及输出路径。脚本当前锁定本次电缆序列号 `XFL114E3TLZIA`，换板需明确选择新的目标。

```powershell
$env:VIVADO = 'E:/vivado/2026.1/Vivado/bin/vivado.bat'
$xsdb = 'E:/vivado/2026.1/Vivado/bin/xsdb.bat'
python verification/scripts/build_board.py --config frozen_ff_pulp1 --out D:/board-repro/baseline
python verification/scripts/build_board.py --config overlay_nn1 --out D:/board-repro/nn
foreach ($build in @('D:/board-repro/baseline','D:/board-repro/nn')) {
    & $env:VIVADO -mode batch -source scripts/check_board_50mhz.tcl -tclargs $build
    if ($LASTEXITCODE -ne 0) { throw '50 MHz timing failed' }
    python verification/scripts/record_board_build.py $build
    if ($LASTEXITCODE -ne 0) { throw 'Build finalization failed' }
}
# Connect the powered, already initialized KV260 through hw_server :3121.
& $xsdb scripts/inspect_ps_clock.tcl
& $xsdb scripts/configure_pl_clock.tcl
if ($LASTEXITCODE -ne 0) { throw 'Unsupported PS clock state' }
foreach ($build in @('D:/board-repro/baseline','D:/board-repro/nn')) {
    foreach ($n in @(1,2)) {
        python verification/scripts/run_board.py --build-dir $build --trial "$build/trial$n"
        if ($LASTEXITCODE -ne 0) { throw 'Physical trial failed; inspect its logs' }
    }
}
& $xsdb scripts/inspect_ps_clock.tcl
```

`configure_pl_clock.tcl` 会拒绝不匹配的 IOPLL 状态。它仅适用于本次已启动的 PS 环境，不是独立冷启动初始化程序。不要省略 20 ns 最终检查或用复位代替重新烧录恢复内存。`run_board.py` 自动检查已最终确认的 manifest、执行 programming/capture/validation，并为每次测试建立全新目录。

无需 Vivado 即可审计已发布的原始结果并重算所有比值：

```powershell
python verification/scripts/summarize_board.py
python -m unittest discover -s verification/tests -v
python scripts/check_public_repository.py --index
```

证据中的 `base_commit` 为构建开始时的 `3d8db86`；未提交的新增板级源码由 manifest 逐文件 SHA-256 固定，不能仅用 base_commit 重建。当前提交包含这些源码及脚本。`artifacts/delivery/source-manifest.json` 和历史 OOC/仿真汇总仍是 2026-10-21 快照；本次板级证据使用这里的新 manifest。大型 bitstream/DCP/完整日志留在本机，仓库发布源码、哈希、原始读回及紧凑报告。
