# DATE 2020 XpulpNN：本地编码与算术语义冻结笔记

日期：2026-10-20。范围：为路线 A 的正式实施计划提供已核对的编码、语义、集成位置和验收条目；本文件本身不是实现，也不证明新指令已经通过仿真。当前活动 RTL 和工程未因本项研究而修改。

## 1. 结论与身份

采用 **FYP 自定义机器码、DATE 2020 功能复现**；不宣称与原作者的工具链或二进制兼容。论文没有给出编码表。扩展开关名固定为 `COREV_XPULPNN`，缺省 `0`，有效组合要求 `COREV_PULP=1`。保留全部现有指令及其编码、宽松编码别名、算术行为；不开启新扩展时，下述新机器码继续产生非法指令异常。

已审计的活动文件为：

- `E:\cv32e40p-master\cv32e40p-master\rtl\cv32e40p_decoder.sv`，`instruction_decoder`，custom-3 分支 2126–2670 行。
- 同目录 `include\cv32e40p_pkg.sv`，custom opcode 58–61 行、乘法枚举 163–174 行、向量模式 178–180 行。
- 同目录 `cv32e40p_id_stage.sv`，操作数复制和流水寄存器。
- 为核实语义另读 `cv32e40p_alu.sv`、`cv32e40p_mult.sv` 和 `docs\source\instruction_set_extensions.rst`。

译码器当前 SHA-256：`6e12f673e05380e34a35c38d8ee8b6878935d96b6f2dfda72c67f8a6e92a6e4e`。行号对应这份未修改文件；正式实现复制源快照后应重新定位并记录哈希。

## 2. 完整 custom-3 空间审计

`OPCODE_CUSTOM_3=7'h7b`。当前先按 `instr[31:26]` 精确 `unique case` 分派，所有未列出的 funct6 均在 2666 行进入 `illegal_insn_o=1`。其他 custom opcode 的低 7 位不同，不会与本分配相交。

现有 44 个 funct6：

```text
00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d
20 22 24 26 28 2a 2e 30 32 34 36 38 3c 3e
```

真正完全未分配的 20 个 funct6：

```text
1e 1f 21 23 25 27 29 2b 2c 2d 2f 31 33 35 37 39 3a 3b 3d 3f
```

其中 19 个分配给本扩展，`3f` 完整保留。注意数字是**十六进制 funct6 值**，不是既有指令注释中五位主操作码。不能把 `6'b11001_0` 等看成空闲；它的值是 `0x32`，属于现有 shuffleI 指令。

保留情况：

| 既有类别 | funct6（十六进制） | 审计位置 |
| --- | --- | --- |
| add/sub/avg/avgu/min/minu/max/maxu/srl/sra/sll/or/xor/and/abs | 偶数 `00` 到 `1c` | decoder 2160–2340 |
| dotup/dotusp/dotsp/sdotup/sdotusp/sdotsp | `20 22 24 26 28 2a` | 2341–2420 |
| extract/extractu/insert | `2e` | 2421–2438 |
| shuffle/shuffleI0/I1/I2/I3 | `30 32 34 36` | 2439–2467 |
| shuffle2 | `38` | 2468–2480 |
| pack/pack.h/packhi/packlo | `3c 3e` | 2481–2496 |
| 比较 | 奇数 `01` 到 `13` | 2499–2608 |
| complex multiply/conjugate/subrot、带缩放 add/sub | `15 17 19 1b 1d` | 2611–2664 |

没有复用任何上述指令原来非法的子格式，也没有收紧上述 case 内部原有字段。分配使用的是整个旧译码器未处理的 funct6，因此不需要借用 extract、shuffle、pack 或 complex 空间。

## 3. 字段、mask 与完整 72 形式表

所有新指令使用 R 型字段：

```text
31       26 25 24       20 19       15 14   12 11        7 6         0
+----------+--+-----------+-----------+-------+-----------+-----------+
|  funct6  |0 |    rs2    |    rs1    | form  |    rd     |  1111011  |
+----------+--+-----------+-----------+-------+-----------+-----------+
```

`form=000` 为 `.n`（4 位，vv），`001` 为 `.c`（2 位，vv），`100` 为 `.sc.n`（4 位，rs2 低 4 位广播），`101` 为 `.sc.c`（2 位，rs2 低 2 位广播）。`010/011/110/111` 全部非法；不增加 `.sci`。bit25 必须为 0，置 1 非法，不能被解释为立即数。

`abs` 仅允许 form `000/001`，并要求 `rs2=0`。`qnt` 仅允许 form `000/001`，其 rs2 是阈值表基址寄存器，任意 0–31 号寄存器编号均合法；地址值是否符合量化内存约定是运行时检查，不是指令编码限制。其他 17 个二元操作族各有四种形式。共 `17×4+2+2=72` 个命名形式。

匹配规则为 `(instruction & MASK) == MATCH`。所有值均为 32 位十六进制；表内 MATCH 的 rs1、rs2、rd 暂填 0，实际寄存器字段按位或进去。abs 的 rs2 固定 0，不可加入其他值。

| 操作族 | funct6 | funct7=`funct6<<1` | MASK | `.n` MATCH | `.c` MATCH | `.sc.n` MATCH | `.sc.c` MATCH |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pv.add | 1e | 3c | fe00707f | 7800007b | 7800107b | 7800407b | 7800507b |
| pv.sub | 1f | 3e | fe00707f | 7c00007b | 7c00107b | 7c00407b | 7c00507b |
| pv.avg | 21 | 42 | fe00707f | 8400007b | 8400107b | 8400407b | 8400507b |
| pv.avgu | 23 | 46 | fe00707f | 8c00007b | 8c00107b | 8c00407b | 8c00507b |
| pv.min | 25 | 4a | fe00707f | 9400007b | 9400107b | 9400407b | 9400507b |
| pv.minu | 27 | 4e | fe00707f | 9c00007b | 9c00107b | 9c00407b | 9c00507b |
| pv.max | 29 | 52 | fe00707f | a400007b | a400107b | a400407b | a400507b |
| pv.maxu | 2b | 56 | fe00707f | ac00007b | ac00107b | ac00407b | ac00507b |
| pv.srl | 2c | 58 | fe00707f | b000007b | b000107b | b000407b | b000507b |
| pv.sra | 2d | 5a | fe00707f | b400007b | b400107b | b400407b | b400507b |
| pv.sll | 2f | 5e | fe00707f | bc00007b | bc00107b | bc00407b | bc00507b |
| pv.abs | 31 | 62 | fff0707f | c400007b | c400107b | — | — |
| pv.dotup | 33 | 66 | fe00707f | cc00007b | cc00107b | cc00407b | cc00507b |
| pv.dotusp | 35 | 6a | fe00707f | d400007b | d400107b | d400407b | d400507b |
| pv.dotsp | 37 | 6e | fe00707f | dc00007b | dc00107b | dc00407b | dc00507b |
| pv.sdotup | 39 | 72 | fe00707f | e400007b | e400107b | e400407b | e400507b |
| pv.sdotusp | 3a | 74 | fe00707f | e800007b | e800107b | e800407b | e800507b |
| pv.sdotsp | 3b | 76 | fe00707f | ec00007b | ec00107b | ec00407b | ec00507b |
| pv.qnt | 3d | 7a | fe00707f | f400007b | f400107b | — | — |

一般机器码公式：`(funct6<<26)|(rs2<<20)|(rs1<<15)|(form<<12)|(rd<<7)|0x7b`。所有 rd/rs1/rs2 编号均允许 0–31，遵循 x0 的读 0、写丢弃规则；abs 的 rs2 编号例外须为 0。sdot 的旧 rd 是隐含第三源，未增加编码字段。qnt 即使 rd=x0 也必须完成访存和异常行为，只丢弃正常的最终结果。

非法边界必须完整冻结：未开启扩展；bit25=1；form 为保留值；abs/qnt 的 sc form；abs 的 rs2 非零；funct6=3f 的所有组合。原来其他 funct6 的合法/非法边界保持不变。

## 4. 静态枚举证据与其范围

使用 bundled Python 3.12 通过标准输入执行一次只读脚本，没有建立工具源文件或 RTL 测试平台。脚本从上述 custom-3 分支提取所有 `6'b...` case 标签，得出 44 个已用、20 个未用，检查 19 个新增值和 44 个旧值交集为空；随后生成表中 72 个 mask/match，并用条件 `((matchA ^ matchB) & maskA & maskB)==0` 检查两个模式是否可能重叠。

再枚举 `64 funct6 × 2 bit25 × 8 form × 32 rs2 = 32768` 个选择字段组合。rs1 和 rd 不参与当前 custom-3 的合法性判定，可按等价类压缩掉；opcode 固定 0x7b。结果：

```text
labels_used=44
labels_free=20
new_patterns=72
new_pairwise_collisions=0
selector_tuples_enumerated=32768
new_legal_selector_tuples=2242
new_legal_tuples_hitting_legacy_case=0
```

2242 的复核：70 个不限制 rs2 的模式各 32 个 rs2，加 abs 两个固定 rs2 的模式，`70×32+2=2242`。扩展表与旧表在 funct6 层面完全分离，因此旧 case 后面任何 rs2、bit25、form 条件都不可能制造交集。这是当前源文件的静态编码不相交证据，**不是运行 RTL 译码器或执行指令的功能验证**。未来必须把表纳入单一机器可读 ISA 描述并实际驱动译码器验证，不可用这里的枚举替代。

## 5. 算术语义，作为模型与 RTL 的共同契约

令 `w=4`（n）或 `w=2`（c），`N=32/w`，`M=2^w-1`。lane i 对应寄存器位 `[w*i +: w]`，i=0 是最低 lane。A 为 rs1 的各 lane；vv 的 B 为 rs2 同编号 lane；sc 的 B 为 rs2 最低 w 位向所有 lane 复制，rs2 高位完全不参与结果。packed ALU 输出每个 lane 重新拼回原位置，lane 间不串进位。

| 操作 | 冻结行为 |
| --- | --- |
| add/sub | 各 lane 加减后取低 w 位，模 `2^w`，不饱和。 |
| avg | `S=(A+B)&M`，先把 S 解释为 w 位有符号数，再算术右移 1，结果取低 w 位；不加 1，不保留加法溢出的那一位。 |
| avgu | `S=(A+B)&M`，对 w 位无符号 S 逻辑右移 1；不加 1，不保留 carry。 |
| min/max | A/B 按 w 位二补码有符号比较，返回获选 lane 的原始位型。 |
| minu/maxu | A/B 按 w 位无符号比较，返回获选 lane 的原始位型。 |
| srl/sll | 每 lane 的移位量 `k=B&(w-1)`，即 n 只看低 2 位，c 只看低 1 位；逻辑移位，sll 结果取低 w 位。 |
| sra | 同样 k，A 解释为 w 位有符号数并算术右移，保留低 w 位。 |
| abs | w 位有符号绝对值后取低 w 位；最小负数保持其二补码位型，例如 n 的 -8 仍为 0x8、c 的 -2 仍为 0x2；不饱和。 |
| dotup / sdotup | A 无符号、B 无符号。 |
| dotusp / sdotusp | **rs1/A 无符号，rs2/B 有符号**；sc 广播的是有符号解释的 B 最低 lane。 |
| dotsp / sdotsp | A、B 均为有符号。 |
| dot / sdot 结果 | 先以足够宽度准确求和全部 N 个乘积；dot 的累加初值为 0，sdot 的初值为旧 rd 的 32 位位型；最终模 `2^32`，无饱和。 |
| qnt | A 为两个打包的有符号 16 位激活，B 为阈值树基址；n/c 指定输出宽度 4/2 位。树布局、相等阈值归属、输出位域和访存异常服从正式量化契约；不能从普通 lane ALU 广播逻辑推导。 |

### avg/avgu 为什么采用看似异常的溢出行为

这是明确选择保留现有 COREV 语义。活动官方说明 `docs\source\instruction_set_extensions.rst:1360–1366` 写出先 AND 掩码再右移；活动 ALU 168–186 行也先从分区加法中提取低 lane 位，再于 244–295 行进行移位。avg 使用 `ALU_ADD`，avgu 使用 `ALU_ADDU`，均不选择带 R 的舍入操作，因此无 +1。DATE Table II 是操作概要，没有提供足以推翻上述规则的位级舍入定义。

必须在新规格和测试中显式保留：`avg.n(7,7)=-1`（lane 位型 f），`avgu.n(15,15)=7`，`avg.n(-1,0)=-1`；c 对应 `avg.c(1,1)=-1`、`avgu.c(3,3)=1`。这些不是 widened mathematical mean，也不是向零截断。有需求改变为 widened mean 时需要单独修订本地 ISA 契约；本计划不做该改变，也不修改既有 h/b 指令。

### dotusp 的证据链

decoder 2354–2357、2393–2396 行令混合符号 dot 的 `mult_dot_signed_o=2'b01`。mult 256–264 行用 bit1 控制 A 的符号扩展，用 bit0 控制 B 的符号扩展；16 位路径 284–296 行相同。因此本地规范必须为 U(rs1)×S(rs2)，不能按论文段落中“first signed / second unsigned”的叙述反转软件参数。

### 模型实现时避免的 C/Python陷阱

Python 模型应先按 w 截 lane 并显式符号扩展；不依赖宿主 int 宽度或负数移位之外的隐含截断。C 模型使用无符号位操作和显式符号转换/宽整数求和，避免 signed overflow、对负数左移或错误的 uint32_t 右移。最终按 32 位掩码比较原始位型。

## 6. 内部控制编码与保留值

采用明确扩宽，避免新增辅助位和旧字段组合出隐藏模式。

| 控制字段 | 宽度 | 保留旧数值 | 新值 | 保留非法/不应使用值 |
| --- | --- | --- | --- | --- |
| 向量模式 | 3 位，建议 `VEC_MODE_WIDTH=3` | 32=`000`、16=`010`、8=`011` | 4=`100`、2=`101` | `001/110/111` |
| `mul_opcode_e` | `MUL_OP_WIDTH=4` | MAC32=`0000`、MSU32=`0001`、I=`0010`、IR=`0011`、DOT8=`0100`、DOT16=`0101`、H=`0110` | DOT4=`0111`、DOT2=`1000` | `1001`–`1111` |

旧枚举应全部写成相应新宽度常数，端口/寄存器不要残留 `[1:0]` 向量模式或三位乘法控制的手写声明。新 dot 精度以其专用 `MUL_DOT4/2` 编码传到乘法/新点积单元，不依赖 ALU 的 EX mode：现有 dot 时 `alu_en=0`，ALU mode 寄存器不会更新。qnt 的输出精度另有它自己的锁存字段，不能依赖可能陈旧的 ALU mode 或 mult opcode。

## 7. 正式实施时的集成位置

下面是计划目标，不在本项研究中创建或复制这些目录。父计划采用 FYP 内 `vendor/cv32e40p/rtl` 保存不可变基线、`rtl/core` 保存修改覆盖文件、`rtl/nn/cv32e40p_nn_{alu,dotp,quant}.sv` 保存新单元。工程只能编译每个 module 的一个定义；不可把 vendor 和同名 overlay 同时加入设计源。

| 目标文件/逻辑 | 当前参考位置 | 必要改变 |
| --- | --- | --- |
| package overlay | pkg 163–180 | 扩宽 mode 与 mul enum，固定上述数值；增加参数传播所需类型/常量。 |
| top/core/ID/decoder 参数链 | 各 module 参数与实例 | `COREV_XPULPNN=0` 缺省，传至所有需要的位置；拒绝 XPULPNN=1/PULP=0 的无效构建组合。 |
| `instruction_decoder` | decoder 2126–2159、2666 | 在原 exact case 中增加上述 19 个全新 funct6，分别检查 enable 和完整合法性，再使能目标单元；不修改原 44 个 case 的解释。 |
| common custom-3 前置设置 | decoder 2128–2156 | 新 ALU 和 dot 覆盖旧 bit12→16/8 选择为 4/2；sc 仅对17个二元族使能。abs 取消不必要 regb 依赖；qnt 取消 packed ALU/mult 使能并设置专属控制。 |
| 普通 dot | decoder 2341–2377 为参考 | `alu_en=0,mult_dot_en=1`，对应 signed bits 00/01/11，REGC_ZERO，不读旧 rd。 |
| sdot | decoder 2378–2419；ID 525–551 | `regc_used=1,REGC_RD`，复用第三读口、EX/WB forwarding 和相关检测。 |
| B 广播 | ID 667–679 | 显式 case 增加 `{8{B[3:0]}}` 和 `{16{B[1:0]}}`；不得让新模式落入旧“else=16位”的默认分支。 |
| C 广播 | ID 714–724 | 保留旧行为，审计扩宽后的所有 mode 分支；sdot 不广播累加器，`scalar_replication_c=0`。 |
| ALU 流水寄存器 | ID 1514–1532 | 新 ALU 仅在有效指令且 alu_en 时捕获操作数/mode/控制，失效和停顿保持原握手规则。 |
| DOT 流水寄存器 | ID 1544–1552 | 在现有 mult_dot_en 条件同时锁存新 DOT4/2 枚举和三操作数；不可从 ALU mode 间接恢复精度。 |
| core/EX mode 通路 | core 179、588、767；EX 55、272 | 统一扩到 3 位；在 EX 结果选择、valid/ready 与旁路处加入新单元并保留旧优先关系。 |
| 新 ALU 单元 | `rtl/nn/cv32e40p_nn_alu.sv` | 4/2 位分区加减、wrap后avg移位、逐lane比较/移位/abs；旧32/16/8路径不改语义。 |
| 新 DOT 单元 | `rtl/nn/cv32e40p_nn_dotp.sv` | 独立8×4/16×2区域、充分位宽归约、32位累加、输入隔离；保留旧mult的8/16/complex路径。 |
| assertions / tracing | ID 1763–1829 及仿真/trace组件 | 扩宽模式断言并按新参数检查禁止使用新 mode/op；非法指令还须约束新 nn/qnt 使能、请求与写回。扩展 trace/disassembler，避免显示 unknown 后无法审计执行证据。 |

“增加 case”不能提前盖住全部 custom-3，也不能用低 5 位家族推导忽略 bit26。所有新增 case 均需在非法变体下抑制新单元副作用，并遵守 decoder 的 `deassert_we_i` 门控（2996–3005 行）。qnt 的请求、完成和唯一提交还需要父计划的 LSU/FSM 契约，不能只复用普通 ALU enable。

## 8. 未来软件封装接口（本项不创建代码）

后续 `verification/sw/common/xpulpnn.h` 提供明确 n/c 和 sc 名称，`verification/sw/common/xpulpnn_words.h` 提供生成的编码常量，所有 packed 输入/输出以 `uint32_t` 表示原始寄存器位型：

```c
uint32_t xpulpnn_add_n(uint32_t a, uint32_t b);       // 各普通二元族、n/c各一对
uint32_t xpulpnn_add_sc_n(uint32_t a, uint32_t b);    // sc只读b最低lane
uint32_t xpulpnn_abs_n(uint32_t a);
uint32_t xpulpnn_dotusp_n(uint32_t a_unsigned, uint32_t b_signed);
uint32_t xpulpnn_sdotusp_n(uint32_t acc, uint32_t a_unsigned, uint32_t b_signed);
uint32_t xpulpnn_qnt_n(uint32_t packed_act16, const int32_t *tables);
```

阈值以32位字存储，每个字是一个有符号16位阈值的32位符号扩展，两个通道的表入口固定相距64字节；因此接口指针使用 `const int32_t *tables`。只在 RV32 目标上将阈值指针转换为寄存器地址；host reference API 接收内存对象/地址模型，不能把64位宿主指针截断为模拟地址。其余 qnt 参数含义服从正式量化契约。

GNU assembler `.insn r 0x7b, FORM, FUNCT7, rd, rs1, rs2` 可以先绕开新增助记符。例如 `pv.add.n a0,a1,a2` 使用 funct7=0x3c，编码应为 `0x78c5857b`。abs 使用 rs2=x0。sdot 使用读写累加器约束 `+r`，其输出寄存器就是隐含第三源旧 rd；不可写成只写的 `=r`。qnt 是真实内存读取，封装应使用 volatile asm 和 `memory` clobber，防止阈值初始化/修改跨指令重排；普通算术封装不需要虚假的内存副作用。

建立单一 ISA manifest：每个形式记录 name/funct6/form/mask/match/operand-kind/signedness；从它生成 helper常量、汇编测试输入、反汇编识别表和译码预期值。reference 算术算法独立编写，避免由 RTL 拷贝生成同一错误。软件发布注明 FYP 自定义编码版本，保留未识别机器码的 `.word` 审计路径。现有 xpack 工具能否接受 `.insn` 和反汇编展示应在实施时实际编译、反汇编验证；这里未运行新指令软件。

## 9. 后续必须新增的编码与语义验收

1. **表驱动译码**：72 个合法形式，所有寄存器字段边界/别名；对全部 32768 个选择字段类实际驱动 RTL decoder，核对非法和控制输出。合法分类不相交只是第一步，必须核对 ALU/mult/qnt 互斥、C源选择、宽度和符号位。
2. **严格非法检查**：对全部新增 funct6 翻转 bit25；遍历保留 form；abs rs2=1…31；abs/qnt sc；保留 funct6=3f；XPULPNN关闭；PULP关闭。检查无寄存器写回、无访存、无新单元启动，并出现正确非法指令异常。不要把旧指令的合法别名列为新增非法要求。
3. **兼容性**：扩展关/开分别对全部原 44 个 case 的合法/非法字段组合比较译码控制与原始基线；再执行 h/b vv/sc/sci、extract/insert、全部shuffle、pack、比较和complex指令回归。比较项包含原有非法行为，不能只比较正常结果。
4. **算术模型**：2位各lane所有A/B位型组合；4位所有A/B位型组合和边界；随机整寄存器、单lane走动模式和满进位模式；标量高位扰动不应改变sc结果；移位量高位扰动只取mask后低位；abs最小负数；本文件列出的avg异常边界。
5. **点积/累加**：用仅一lane非零定位打包方向，dotusp用A全1/B符号位检查U×S顺序；穷举2位lane乘积、4位符号边界、全最大值；覆盖32位累加wrap和连续相关sdot。
6. **真实取指执行**：明确检查生成的机器码，覆盖rd=rs1、rd=rs2、rs1=rs2、三者相同、rd=x0、源x0、连续sdot和load-use/EX/WB旁路；qnt精度/输入在接受指令时锁存，量化中不能被后续译码改变。
7. **构建矩阵与静态宽度审计**：PULP0/XPULPNN0、PULP1/XPULPNN0、PULP1/XPULPNN1均编译展开，PULP0/XPULPNN1应被明确拒绝；检索全部VEC/MUL端口和比较，不允许静默截断；旧比较器/移位器的default不得将新mode当32或16位计算。

本文件已完成的是局部源审计与编码静态枚举；RTL实现、测试平台、软件封装、综合和时序实验均留待正式计划审阅之后开始。
