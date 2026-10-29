# CV32E40P 低精度扩展：实施与验证记录

日期：2026-10-21。本文按用户已批准的 Route A 与 `DATE2020-local-v1` 规格记录实现。功能回归 PASS，核心及完整封装的两组 20 ns OOC 实现均满足时序；扩展核的 10 ns 时序未闭合。

2026-10-29 补充：已完成 KV260 完整器件构建、实际 JTAG 编程及 baseline/XPulpNN 各两次重新烧录验证，四次均 PASS。新板级 top 在 20 ns 下闭合时序；每次核对 356 字确定性输出并采集全部 472 字。实测周期、源码/bitstream 身份、原始读回及复现命令见 [实板验证报告](kv260-board-validation.md)。下文 2026-10-21 的仿真/OOC 数据继续保留为历史记录。

## 1. 实现内容与论文的对应关系

| 项目 | 本地实现与依据 |
|---|---|
| 处理器 | 冻结当前 FYP 的 CV32E40P；保留四级流水线、32 位 GPR、累加器及 OBI 总线 |
| 4/2 位 packed ALU | add/sub/avg/avgu/min/minu/max/maxu/srl/sra/sll/abs，包含论文列出的向量与标量广播形式 |
| 点积 | dotup/dotusp/dotsp 与 sdotup/sdotusp/sdotsp；独立的 8×4 位和 16×2 位乘法区域、平衡加法树与输入隔离 |
| 累加与相关 | sdot 读旧 rd，32 位回绕；组合 EX 路径保留连续累加和源/目的别名行为 |
| 双通道量化 | qnt.n/qnt.c 使用两个 signed16 激活、两张阈值表，独立二叉搜索状态，通过原 LSU/OBI 读取阈值 |
| 提交 | 普通访存和 load 写回排空后取得总线所有权；最终 done 握手才写回、转发与释放；忙碌时保持年轻指令 |
| 软件 | 72 个内联指令 helper、独立 Python 模型、scalar/dot8/native 三组 kernel、完整 ELF/反汇编及签名 |
| 平台 | FF 寄存器堆、真实睡眠 BUFGCE、64 KiB IMEM 与 64 KiB DMEM、37 位封装接口 |

对应论文 DATE 2020 Table II 共 **72 种形式：70 种算术形式及 2 种 qnt**。本范围没有加入后续论文的 MAC&LOAD、NN-RF 或不等位宽点积。详细原文页码、图表与歧义分析见 [论文分析](../investigation/paper-analysis.md)。

论文没有给出可直接复刻的完整机器码与量化 ABI。本项目明确使用 [已批准规格](../superpowers/specs/2026-10-20-xpulpnn-cv32e40p-design.md) 中的本地编码：custom-3 `0x7b`，保留原有合法功能码。量化表每通道占 64 字节；阈值是 32 位存储字中的 signed16；相等时进入较高区间；两个 Q 位补码紧密打包。`dotusp` 沿当前核心约定为 unsigned A × signed B；`avg` 按元素先回绕再移位。这里没有声称与作者编译器二进制兼容。

FPGA 用输入隔离控制非活动算术区域，不照搬 ASIC 每个区域的时钟门控单元。单周期 EX 是流水线延迟属性，能否满足目标时钟由布线结果单独决定。

## 2. 功能与集成证据

逐条命令、配置、种子、源哈希及工件路径见 [验证索引](verification-index.md) 和 [机器可读汇总](../../artifacts/verification/summary.json)。历史 RED、FAIL 与工具中断保留。

最终 `all` 为 19 个顶层组、42 个叶测试。6 个较早叶测试保留其原始 TB 哈希，并显式关联同配置/套件/种子的当前 PASS 重跑；其余叶测试与当前输入匹配。OBI 压力种子 1/42/20261020 均有当前 RTL/TB 哈希证据。host 模型、编码及运行器检查共 17 项通过；特殊 IRQ/debug 时点使用定向场景，不能扩大表述为所有时序组合的随机证明。

| 验证项 | 已获得的证据 |
|---|---|
| ALU/dot 单元 | 种子 1/42/20261020；每种子主测试 243,264 ALU + 60,816 dot，补充 96,880 ALU + 51,648 dot；三种子合计 1,357,824 个向量 |
| 译码 | 32,768 个选择器组合；2,242 个合法选择器类别对应 72 形式；比较旧 44 个功能码的控制输出 |
| 真实算术程序 | 70 形式 × 8 组寄存器/输入情况，共 560 个逐字签名；包括源/目的别名与 x0 |
| 量化单元 | 每种子 4,069 次完成操作、24,509 次读取，另有 4 类复位；每种 Q 各 2,000 随机非递减阈值表；理想单元延迟 Q2=5/Q4=9 周期 |
| 量化整核 | 每种子 206 条 qnt；逐字比对、x0 仍访存、load→qnt、交替精度、非法基址精确 trap2；独立统计 ID 接受、minstret 事件与提交 |
| 总线边界 | 随机 grant/response 停顿；实际达到两个未完成阈值请求；LSU FIFO 同时出入队、普通 load 元数据隔离 |
| 最终提交 | 外部 WB ready 人为阻塞 6 周期；期间保持结果/所有权、禁止写回与释放，解除后恰好一次提交 |
| IRQ/debug/reset | 发射前、WAIT_DRAIN、首 grant、响应中途、请求被阻塞、末响应六个时点；真实 dcsr 单步进入 DBG_FLUSH；全局复位同步清存储器队列 |
| 兼容 | frozen FF、NN-off、NN-on 的 smoke/旧 SIMD/extract/shuffle/pack/complex 结果一致；72 新形式在 frozen 与 NN-off 均产生精确非法指令异常 |
| 参数 | 7 组合，包括支持配置、NN-off/PULP0，以及非法启用组合；非法组合在仿真 time 0 由明确 guard 拒绝 |
| 负面环境 | 未映射阈值地址由 TB 拒绝；无服务测试先完成普通基址 load，再拒绝首条阈值响应，记录 issue=1/commit=0 与预期 watchdog。它们不是程序执行成功或 CPU 访存异常支持证明 |

量化 trace 区分 `id_accept`、`lsu_drained_unit_start`、`first_grant`、`last_response`、`writeback`、`next_id_accept`。例如真实单步用例中，ID 在第 106 周期接受，107 启动单元，108 首 grant，115 末响应/写回，119 接受下一指令。这里的周期是该程序的仿真时间点；5/9 周期指标仅指量化单元的理想服务条件。

5.6 Terra 的 [独立审查](independent-review.md) 未发现可复现的 RTL 功能缺陷。审查指出的回归入口遗漏已经纳入公开 `all` 入口；结果仍由实际运行判定。

## 3. 性能解释

详见 [基准比较](benchmark-comparison.md)。数据集为 Q4/Q2 的 8×32×8 MatMul、8×8×8 输入/3×3×8×8 filter 的 valid 卷积，以及 K=35 尾部测试。host 逐字核对全部输出；Q2 卷积 K=72 的物理 lane 长度补到 80，K=35 分别补到 40/48。

主分母是本项目包含解包、符号扩展和软件阈值量化的 dot8 实现；它尚未做到论文作者 kernel 的优化程度，部分场景比 scalar 更慢。报告中的倍数描述这份代码，不能当作最佳 Xpulp 基线、论文 5.3/8.9 倍或普遍神经网络加速比。包含准备/im2col 的端到端区间更适合描述本演示的总体收益。

`mcycle/minstret` 采用 high/low/high 的 64 位读取，显式启用计数。计时包括区间内取指与数据停顿，排除区间外签名检查和邮箱；空测量框架单独记录且未静默扣除。共同 ROM 在 NN-on 下额外执行 native kernel，**整个测试程序的完成周期不可直接计算加速比**。

FPGA 封装使用不同于 core TB 的存储器服务，因此 [FPGA 汇总](../../artifacts/fpga/summary.json) 从两组封装的实际签名中另外提取 `wrapper_kernel_metrics`。物理时间估算必须用这些周期乘以已满足的布线时钟周期；它仍是仿真周期结合实现约束的估算，不是板上计时。

## 4. FPGA 实现与边界

<!-- MEASURED_PERFORMANCE_START -->
| 数据集 | 基线 dot8 周期 | 扩展 native 周期 | kernel 周期比 | 含准备周期比 |
|---|---:|---:|---:|---:|
| matmul_q4 | 61152 | 3498 | 17.482× | 2.854× |
| conv_q4 | 587429 | 25562 | 22.981× | 2.608× |
| tail_q4 | 4265 | 322 | 13.245× | 1.495× |
| matmul_q2 | 59286 | 2378 | 24.931× | 2.954× |
| conv_q2 | 579842 | 16058 | 36.109× | 2.694× |
| tail_q2 | 4164 | 250 | 16.656× | 1.510× |

两组都满足 20 ns（50 MHz）的 OOC 约束。以相同频率估算：

| 数据集 | 基线 kernel μs | 扩展 kernel μs |
|---|---:|---:|
| matmul_q4 | 1223.040 | 69.960 |
| conv_q4 | 11748.580 | 511.240 |
| tail_q4 | 85.300 | 6.440 |
| matmul_q2 | 1185.720 | 47.560 |
| conv_q2 | 11596.840 | 321.160 |
| tail_q2 | 83.280 | 5.000 |

基线还通过 100 MHz；若比较基线 100 MHz 与扩展 50 MHz，时间加速比为上表周期比的一半。主 MatMul/Conv 含准备区间的估算时间收益约为 1.30–1.48×。不能只用周期减少量忽略频率差。
<!-- MEASURED_PERFORMANCE_END -->

<!-- ROUTED_RESULTS_START -->
| 范围 | 配置 | 约束 ns | LUT | FF | latch | DSP | BRAM tile | BUFGCE | WNS ns | WHS ns | 时序 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| core_ooc | [frozen_ff_pulp1](../../artifacts/fpga/summary.json) | 10.0 | 7065 | 2485 | 0 | 7 | 0 | 1 | +0.085 | +0.045 | 满足 |
| core_ooc | [overlay_nn1](../../artifacts/fpga/summary.json) | 10.0 | 9071 | 2728 | 0 | 7 | 0 | 1 | -3.058 | +0.058 | 未满足 |
| core_ooc | [frozen_ff_pulp1](../../artifacts/fpga/summary.json) | 20.0 | 6876 | 2485 | 0 | 7 | 0 | 1 | +5.385 | +0.021 | 满足 |
| core_ooc | [overlay_nn1](../../artifacts/fpga/summary.json) | 20.0 | 8557 | 2719 | 0 | 7 | 0 | 1 | +1.144 | +0.028 | 满足 |
| system_ooc | [frozen_ff_pulp1](../../artifacts/fpga/summary.json) | 10.0 | 7495 | 2633 | 0 | 7 | 32 | 1 | +0.269 | +0.012 | 满足 |
| system_ooc | [overlay_nn1](../../artifacts/fpga/summary.json) | 10.0 | 9443 | 2872 | 0 | 7 | 32 | 1 | -4.399 | +0.013 | 未满足 |
| system_ooc | [frozen_ff_pulp1](../../artifacts/fpga/summary.json) | 20.0 | 7226 | 2633 | 0 | 7 | 32 | 1 | +3.232 | +0.021 | 满足 |
| system_ooc | [overlay_nn1](../../artifacts/fpga/summary.json) | 20.0 | 8745 | 2863 | 0 | 7 | 32 | 1 | +0.594 | +0.025 | 满足 |

上表为 routed 资源与时序，工具执行成功与 timing_met 分开判断；10 ns 失败结果未删除。

| 范围/配置/周期 | 无输入 delay 的端口 | 无输出 delay 的端口 | 无时钟端点 | 未约束内部端点 |
|---|---:|---:|---:|---:|
| core_ooc/frozen_ff_pulp1/10 ns | 237 | 111 | 0 | 0 |
| core_ooc/overlay_nn1/10 ns | 237 | 111 | 0 | 0 |
| core_ooc/frozen_ff_pulp1/20 ns | 237 | 111 | 0 | 0 |
| core_ooc/overlay_nn1/20 ns | 237 | 111 | 0 | 0 |
| system_ooc/frozen_ff_pulp1/10 ns | 2 | 34 | 0 | 0 |
| system_ooc/overlay_nn1/10 ns | 2 | 34 | 0 | 0 |
| system_ooc/frozen_ff_pulp1/20 ns | 2 | 34 | 0 | 0 |
| system_ooc/overlay_nn1/20 ns | 2 | 34 | 0 | 0 |

未配置板级 HD.CLK_SRC，因此 OOC 时钟输入的板级延迟/偏斜不在此验证范围内。

<!-- ROUTED_RESULTS_END -->

器件为 `xck26-sfvc784-2LV-c`。基线与扩展使用相同 FF RF、BUFGCE、存储器、共同 ROM、约束与 OOC 流程。先 10 ns，再为两组提供相同 20 ns 实现；完整日志、DCP、资源、时序、DRC、时钟和未约束路径计数保存在 [FPGA 汇总](../../artifacts/fpga/summary.json)。

共同映像 IMEM SHA-256 为 `48763bbe9aaa8a77dea7fe0103f143106381714fca78c1fce4fe2fca4359089a`，DMEM 为 `591eb7ddfc7ae37061e60600eba5d524ff64e8aa515dde8ab41f2ea1a8154d10`。两组封装均核验 472 字，其中 356 字为确定性输出、116 字为运行指标；共同确定性 fold 为 `0x39a7d0b7`。公开发布的汇总数值以 [FPGA 汇总](../../artifacts/fpga/summary.json) 为准；逐次运行的 `run.json/actual.hex` 保留在本地工作区。

RAM 地址选择最初阻碍 BRAM 推断，原综合警告已保留。修正为读端口前统一选择 CPU/扫描地址后，两组封装仿真通过，综合确认 Block RAM、无 LUTRAM。初版 Vivado 工作目录中的 memory 文件在运行过程中消失；归档按已记录 SHA 恢复相同映像，后续工程把永久输入保存到独立 `memory/` 目录，并检查运行后完整性。

OOC 未设置板级 input/output delay、管脚与 I/O standard；这些未约束端点保留在报告中，没有用全局 false path 掩盖。当前 top 没有外部总线错误输入且关闭 PMP，故相应精确访存故障扩展为 NOT_APPLICABLE。截至 2026-10-21，bitstream、KV260 编程、板级运行与功耗测量均为 NOT_RUN；2026-10-29 已新增 bitstream、编程与板级运行 PASS 证据，功耗仍未测量，详见本文开头链接。

## 5. 重建与原项目保护

从仓库根目录执行 [公开 README](../../README.md) 的命令。主要入口：

```powershell
& ./verification/scripts/run_tests.ps1 -Config overlay_nn1 -Suite all -Seed 1
& ./verification/scripts/run_tests.ps1 -Config overlay_nn1 -Suite obi_stress -Seed 42 -GrantMax 7 -ResponseMax 11
& ./verification/scripts/run_tests.ps1 -Config overlay_nn1 -Suite obi_stress -Seed 20261020 -GrantMax 7 -ResponseMax 11
& ./verification/scripts/run_tests.ps1 -Config frozen_ff_pulp1 -Suite regression -Seed 1
& ./verification/scripts/run_tests.ps1 -Config overlay_nn0 -Suite regression -Seed 1
```

公开运行器使用本会话的 PowerShell 7 调用算术脚本，避免硬编码的 Windows PowerShell 5 在本机禁止脚本执行；没有修改系统执行策略。每次运行使用独立目录。

原 `FYP.xpr` SHA-256 保持 `9d348bcda279dbd563006ed12d1ae816f06b0ff66022e54145c753f7af3f0e82`。原 E 盘及本地冻结快照通过逐文件哈希复核；D 盘旧原型没有被本次实现写入，但没有最初的全树哈希，不能声称完成了其全树密码学验证。交付包含源码清单、相对冻结基线的覆盖补丁和源码 zip。

两份最终 20 ns 工程已从不同工作目录重新打开，检查 top、持久 XDC 与 ROM 输入路径；这一重开检查及最终 timing 状态记录在 [FPGA 汇总](../../artifacts/fpga/summary.json)。源码包固定共同 ROM，并校验 ZIP CRC 和每个归档文件的 SHA-256；原始输入完整性检查覆盖 140 个来源文件及 `FYP.xpr`。完整日志和 DCP 留在本工作区；迁移重建方法与工具路径见 README。
