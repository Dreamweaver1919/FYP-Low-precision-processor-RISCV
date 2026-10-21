# XpulpNN DATE 2020: paper evidence and CV32E40P implementation requirements

Source: `C:\Users\CEG\Downloads\XpulpNN_Accelerating_Quantized_Neural_Networks_on_RISC-V_Processors_Through_ISA_Extensions.pdf`, Angelo Garofalo et al., **XpulpNN: Accelerating Quantized Neural Networks on RISC-V Processors Through ISA Extensions**, DATE 2020, printed pp.186-191, six PDF pages. Page references below give PDF page / printed page. Text extracted to `xpulpnn-paper.txt`. PDF pages 2-5 were rendered with bundled Poppler and visually inspected, including Tables II/III and Figs.1-7. This report uses this exact paper; later XpulpNN publications must be treated as separate designs.

## 1. Scope corrections that affect the FYP

- This paper extends RI5CY's RV32IMCXpulpV2 packed SIMD from 16/8-bit to **4-bit (`n`, nibble) and 2-bit (`c`, crumb)**. A 32-bit source register holds eight 4-bit elements or sixteen 2-bit elements. [PDF p.2 / p.187, III-A; PDF p.3 / p.188, III-B1]
- It has **same-bitwidth input vector dot products**. It does not define unequal-precision operand operations such as 8-bit activations times 4-bit weights, or 4-bit times 2-bit. Layerwise precision selection is different from an unequal-precision dot-product ISA. Fig.3's `8x4` and `16x2` identify lane count times element bitwidth, not operand precisions. The title of reference [11] contains “Mixed Low Precision”; that citation does not add an unequal-precision datapath to this paper.
- **MAC&LOAD and an NN register file (NN-RF) are absent** from the complete six-page paper, ISA Table II, and architecture figures. Ordinary baseline auto-increment load/store support is described, but there is no fused MAC-and-load extension here. Do not make NN-RF, MAC&LOAD load hazards, or a second register-file writeback path mandatory when reproducing this paper. [II-1; Table II; Figs.1,3,4]
- The major non-dot-product contribution is instead **`pv.qnt.n` / `pv.qnt.c`**, a multicycle, memory-reading threshold quantizer that stalls the main pipeline. Omitting it gives a valid staged research implementation, but not a complete reproduction of this paper's extension. [III-A, III-B2]
- It is an **ASIC PULPissimo evaluation**, not an FPGA result. Its cycle counts, area percentages, clock frequency and energy numbers are not direct targets or guarantees for CV32E40P on the user's FPGA.

## 2. ISA contract supported by the paper

| Family | Operations in Table II | Supported forms | Paper evidence |
| --- | --- | --- | --- |
| Packed arithmetic | `pv.add`, `pv.sub`, `pv.avg`, `pv.avgu` | `.n` / `.c`; vector-vector or `.sc` | PDF p.3 / p.188, Table II |
| Packed min/max | `pv.max`, `pv.maxu`, `pv.min`, `pv.minu` | `.n` / `.c`; vector-vector or `.sc` | Table II; pooling/ReLU motivation in III-A |
| Packed shifts | `pv.srl`, `pv.sra`, `pv.sll` | `.n` / `.c`; vector-vector or `.sc` | Table II |
| Packed absolute value | `pv.abs` | `.n` / `.c`; no `.sc` listed | Table II |
| Dot product | `pv.dotup`, `pv.dotusp`, `pv.dotsp` | `.n` / `.c`; vector-vector or `.sc` | Table II; III-B1 |
| Accumulating dot product | `pv.sdotup`, `pv.sdotusp`, `pv.sdotsp` | `.n` / `.c`; vector-vector or `.sc`; reads old `rd` | Table II; III-B1 |
| Threshold quantization | `pv.qnt` | `.n` / `.c`; two 32-bit inputs, one 32-bit output | III-A; III-B2; Fig.4 |

The baseline also has `.sci` immediate forms for 8/16-bit operations, but **the proposed 4/2-bit extension explicitly omits `.sci`** because the existing RV32IMCXpulpV2 encoding space is constrained. `.sc` broadcasts a scalar taken from the second register operand. [PDF p.2 bottom / p.187, continued PDF p.3 / p.188, III-A]

For element width `b` and lane count `L = 32/b`, the dot semantics are:

```text
dot:  rd_new = sum(i=0..L-1, interpret(a[i]) * interpret(b[i]))
sdot: rd_new = rd_old + sum(i=0..L-1, interpret(a[i]) * interpret(b[i]))
```

The result/accumulator register is **32 bits**, and `sdot` has an additional 32-bit accumulation input. The paper's discussion of “16-bit MatMul results” concerns the software range exploited by quantization; it is not permission to make the architectural dot accumulator only 16 bits. [III-A; III-B1]

Signedness: III-B1 explicitly describes both operands signed, both unsigned, or **first signed / second unsigned**, with sign or zero extension before multiplication. Table II distinguishes `up` / `usp` / `sp`, but does not annotate each source's signedness or specify exact decoder signals. Therefore use the source RTL/compiler convention as the normative operand-order definition before freezing a mnemonic-to-signedness mapping. Do not silently infer `rs1`/`rs2` signedness from the English mnemonic alone. The paper also mentions the signed/unsigned interpretation of the scalar accumulation input without providing a bit-level overflow specification.

Sub-byte lanes are packed inside 32-bit GPR values; **there is no new fractional-width GPR or memory bus**. The paper illustrates indexed elements, but does not normatively specify lane-zero bit placement, memory byte order, the `.sc` source slice, per-lane shift-count masking, saturating versus modulo overflow, minimum-negative `abs`, or exact `avg` rounding. These details require the baseline ISA specification/source or an explicit FYP contract. A natural local model would take lane `i` from bits `[b*i +: b]`, but that is an implementation decision until verified against source.

Useful arithmetic checks derived from the stated operation (not additional paper requirements): eight unsigned 4-bit products can sum to **1800**, so the reduction must not truncate to 8 bits; sixteen unsigned 2-bit products can sum to **144**, so it must not truncate to 4 bits. Eight signed 4-bit products can produce **512**, and sixteen signed 2-bit products **64**. Preserve sufficient signed width throughout the adder tree and then perform the specified 32-bit accumulation. Fig.3 labels must not be read as permission to truncate a reduction sum to a single product's width.

## 3. Dot-product microarchitecture and CV32E40P integration implications

The paper's implementation has four separate precision regions: baseline two 16-bit multipliers, baseline four 8-bit multipliers, **eight 4-bit multipliers**, and **sixteen 2-bit multipliers**, each with its own reduction tree. It deliberately avoids sharing multipliers and reduction trees among precisions because the muxing/routing would increase the critical path. A final selector chooses the 32-bit result. [PDF p.3 / p.188, Fig.3 and III-B1]

- Both dot and accumulating dot complete in **one cycle** in their design. `sdot` adds `OpC`, the 32-bit old destination/accumulator, at the reduction. [III-B1]
- Sign/zero extension permits one signed multiplier representation for signed and unsigned inputs. Fig.3 shows **5-bit multipliers for 4-bit lanes and 3-bit multipliers for 2-bit lanes**, corresponding to an extra sign bit. [Fig.3; see discrepancy below]
- They avoid inserting a register between multiply and accumulate because dependent, consecutive `sdot` instructions would otherwise stall; dot-heavy QNN loops would lose performance. [PDF p.4 / p.189, first two paragraphs]
- Each precision region has input registers with clock gating to suppress switching in inactive regions. This operand isolation/power-management logic contributes area but substantially reduces power overhead. [Fig.3; III-B1; Table III]

For CV32E40P, map this behavior onto the checked-out version's decoder, precision-selection signals, signedness selection, dot-product/ALU datapath, source-C selection and result mux. The existing architectural `rd` read/forwarding for an accumulating instruction must remain correct for back-to-back accumulation, `rd == rs1`, `rd == rs2`, and dependence on a preceding producer. The paper does not prescribe CV32E40P signal names or claim that an old RI5CY patch can be copied unchanged.

Single-cycle latency is a **design objective to measure** on FPGA. A 16-lane reduction may lower Fmax, and using LUTs or DSP blocks may differ from the ASIC's replication tradeoff. If a multicycle or pipelined implementation is chosen, document latency, throughput and interlock/forwarding behavior explicitly; its cycle-level results are then a different microarchitecture from the paper.

## 4. Quantization unit: required behavior and open details

The quantizer implements a staircase function using a balanced threshold-comparison tree. A Q-bit output has **2^Q - 1 precomputed 16-bit thresholds per output channel**, while only Q comparisons are visited along one tree path. Bias/batch-normalization can be absorbed in those offline thresholds. The paper's 4-bit Fig.2 shows thresholds `th[0]..th[14]` and signed outputs -8..7. [PDF p.2 / p.187, II-2, Fig.2]

Architectural inputs and outputs:

1. Source A is a 32-bit register holding two 16-bit activations, `activation1` in `[15:0]` and `activation2` in `[31:16]`, as drawn in Fig.4.
2. Source B supplies the threshold-tree entry address for the first activation/channel.
3. A hardwired offset derives the second activation's threshold entry point because the channel threshold vectors are consecutive in memory. No third input register is required.
4. Two quantized activations are returned in a single 32-bit destination register. Exact bit placement of the two final sub-byte values and values of unused bits are not specified clearly enough to build a binary interface from the paper alone.

Microarchitecture in III-B2 / Fig.4:

- A compare-and-update region performs a 16-bit comparison and constructs the result bits iteratively; a separate region generates the next threshold address.
- An initial unpipelined prototype computes one 4-bit result in 5 cycles (one 2-bit result in 3 cycles), but **increases the system critical path by 90%**. These are not the final published latencies.
- The final design pipelines address generation and comparison and duplicates the relevant resources to interleave the two activations. Under the assumed memory response behavior it returns **two 4-bit results in 9 cycles**, or **two 2-bit results in 5 cycles**.
- A **3-bit FSM** sequences phases and handles memory stalls. While active, the quantizer takes control of execution and stalls the main core until the result is ready.
- The unit requests threshold data through the LSU and applies operand isolation at comparator inputs. With suitably aligned threshold vectors, the next-address updates require only the low 6 address bits in their layout. The paper reports misalignment as the stall cause in its specific evaluated system.

Do not infer a universal no-stall property from that system. On the FYP bus, the unit must preserve requests across backpressure, wait for valid data, avoid duplicate completion/writeback, and handle the actual core/bus's fault, flush, debug and reset behavior. These are integration requirements inferred from adding a memory-consuming multicycle instruction, not all specified by the paper.

**Unknowns that must be resolved before implementing a compatible `pv.qnt`:** exact opcode; threshold address/layout/alignment and second-channel offset; equality convention at a threshold; threshold and activation signedness; output lane placement and unused bits; overflow/truncation before accepting two 16-bit activations; memory-request handshake/error semantics; interaction with exceptions, interrupts and debug. The diagram illustrates `>` and `<` branches but does not state equality handling. Do not guess that the offset is 30/6 bytes or 32/8 bytes: the paper does not give the padded stride.

## 5. Encoding availability and software contract

There is **no instruction bit-encoding table** in this paper. Table II is a semantic mnemonic overview, not an opcode map. No `opcode`, `funct3`, `funct7`, field placement or collision analysis is given for `n`, `c` or `qnt`. It is therefore not defensible to claim exact binary compatibility based only on this PDF.

Two legitimate FYP routes are:

- Locate the authors' corresponding RTL/GCC sources, pin versions and derive an encoding map, checking against the exact CV32E40P/Xpulp baseline already in the workspace.
- Define an explicitly local custom encoding, audit all existing decoder uses and illegal-instruction behavior, and use `.insn` / raw-word helpers or a matching compiler patch. This reproduces the operation concept but should not be advertised as binary-compatible XpulpNN without evidence.

The authors extended **GCC machine descriptions and integer-based built-in functions** because normal C types cannot express sub-byte vectors directly. They state this gives better optimization than inline assembly and uses 32-bit registers efficiently. [PDF p.5 / p.190, paragraph before IV-A]

Consequently a hardware-only patch is insufficient for a reproducible demonstration: supply packing helpers, instruction emission/built-ins, a golden scalar model, kernels and a repeatable build/run method. Inspect the generated disassembly or instruction words to prove that a benchmark actually executes the new operations.

## 6. Evaluation conditions and results: what is actually supported

| Item | Paper condition/result | Evidence |
| --- | --- | --- |
| Core/platform | 4-stage, in-order, single-issue RI5CY; RV32IMC + XpulpV2; full PULPissimo MCU with 512 kB SRAM | II-1, IV |
| Physical design | Commercial 22nm FDX; Synopsys Design Compiler 2016.03; Cadence Innovus 15.20.100; full place and route | PDF p.4 / p.189, IV |
| Timing corner | SS, 0.59 V, -40 C / 125 C | IV |
| Power method | Post-place-and-route simulation; Modelsim 10.6c VCD; Synopsys PrimeTime 2016.03; typical corner stated TT 0.65 V, 25 C | PDF p.5 / p.190, IV-A |
| Frequency | 250 MHz in the power comparison and conclusion | IV-A; V |
| Benchmark shape | Input 16x16x32; filter tensor 64x3x3x32; separate 8/4/2-bit convolution kernels derived from [3] | PDF p.5 / p.190, IV |
| Core area | Baseline 19,729.9 um^2; managed extension 21,912.8 um^2 = about 0.022 mm^2; +11.1% | Table III; IV-A |
| dotp area | 5,708.9 to 6,844.4 um^2; +19.9% | Table III |
| Core power on 8-bit MatMul | 1.15 mW baseline, 1.41 mW extension without power management, 1.22 mW with it; stated +22.5% and +5.9% | Table III |
| SoC power on 8-bit MatMul | 5.93 to 6.04 mW with managed extension; stated +1.8% | Table III |
| qnt's contribution | Relative to sub-byte kernels with software quantization, `qnt` improves total cycles 1.21x for 4-bit and 1.16x for 2-bit; remaining quantization fractions 4% and 11% | Fig.6; IV-B |
| Same-core sub-byte speedup | 5.3x for 4-bit and 8.9x for 2-bit relative to baseline RI5CY/XpulpV2 kernels that require packing/unpacking | Fig.7; IV-B |
| Energy efficiency vs baseline | 5.5x and 9x on 4/2-bit; abstract peak 279 GMAC/s/W | Abstract; Fig.7; V |
| Commercial MCU comparison | STM32H743/Cortex-M7 and STM32L476/Cortex-M4 with extended CMSIS-NN | PDF p.6 / p.191, IV-B; Figs.8/9 |

The 5.3x/8.9x factors are **whole convolution-kernel cycle reductions against a particular unpacking baseline**, not the speedup of one multiplier and not an expected factor for every model. The paper's near-linear scaling versus its 8-bit kernel (Fig.6: 1.85x/3.32x for full 4/2-bit kernels) has a different denominator. One dot instruction performs eight or sixteen scalar multiply-accumulates, but loads, im2col, quantization and loop control remain.

The reported energy efficiency couples the architectural extension with the ASIC process, voltage, memory system, clock gating and workload. It cannot establish FPGA watts, FPGA MAC/s/W, LUT/DSP cost, BRAM utilization, Fmax or battery life. FPGA work should report measured cycles, post-route timing/resource use and, only if a valid power method exists, a separately qualified board/tool power estimate. Re-run both baseline and extension under the same FPGA constraints and memory arrangement.

## 7. Internal ambiguities and apparent typographical errors

1. **Multiplier width:** III-B1 says the 4/2-bit inputs become “5- or 2-bit” operands after extension. Fig.3 visibly labels `Mult-5b` / `Mult-3b`, and extension by one bit gives 5/3. Treat the prose's `2-bit` as a likely typo, not a hardware specification.
2. **Quantizer timing caption:** Fig.4 caption calls its timing diagram `pv.qnt.c`, but the diagram shows four comparison levels and nine cycles; III-B2 consistently specifies 9 cycles for 4-bit and 5 for 2-bit. Use the prose distinction and identify the caption discrepancy.
3. **Power voltage:** Table III headings say **0.75 V, 250 MHz**, whereas IV-A says **TT, 0.65 V, 25 C**, and the conclusion says operation at **0.65 V, 250 MHz**. This is an unresolved source inconsistency. Do not normalize it silently or state one voltage as unambiguous.
4. **Table III percentages:** the no-power-management ID-stage area is 6,530.2 versus baseline 6,363.1 um^2; the table prints `1%`, while these values imply approximately 2.63%. Use the absolute entries if reproducing component-level arithmetic; the total +11.1% is consistent after rounding.

## 8. Suggested acceptance checklist for a paper-based FYP

The checklist below is an engineering interpretation for the target core, not a claim that the paper supplies all details.

1. Freeze the CV32E40P version, optional baseline extensions and selected scope: sub-byte dot/sdot first; packed ALU coverage and the distinct `qnt` unit as separately visible milestones.
2. Freeze the instruction contract before RTL changes: widths, signedness per operand, packing, scalar broadcast, accumulator behavior, encoding and latency. Resolve the unknowns above from pinned source or mark local decisions.
3. Verify 4/2-bit arithmetic against a scalar golden model, including min/max signed values, unsigned upper half, mixed signedness, all lanes active, independent lane boundaries and 32-bit accumulator carry/overflow behavior.
4. Verify dependency behavior: repeated `sdot` on the same destination, aliases, result consumption, preceding loads, all supported source positions, and inactive extension encodings. Compare existing 8/16-bit and standard integer behavior before/after.
5. If `qnt` is included, verify the two parallel outputs independently, every threshold boundary including equality, both precisions, alignment/layout, injected memory stalls, reset/flush/error behavior and one completion/writeback per instruction.
6. Build an instruction-emitting microbenchmark and a packed QNN kernel with fixed tensors, compare output bit-for-bit against the reference, then report baseline/extension cycles and the exact compiler/build configuration.
7. Synthesize/place/route both FPGA configurations with equal constraints, report LUT/FF/DSP/BRAM and Fmax separately from instruction count and cycle speedup. A latency reduction only becomes a time reduction after accounting for achievable clock frequency.

Only research notes, extracted text and rendered paper pages were produced for this analysis. No RTL, compiler, project constraints or dependencies were modified.
