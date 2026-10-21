# Route A verification and FPGA implementation notes

Planning input, inspected 2026-10-20. **Only this document is created by this task.** Every source, test, command interface and acceptance result below is proposed work after approval of the main implementation plan. Nothing below establishes an XPulpNN test pass or a new synthesis/timing result.

## 1. Evidence and non-negotiable boundaries

- `docs/investigation/verification-environment.md` and `baseline/run-baseline.ps1` establish analysis and elaboration of the active `cv32e40p_top` for `COREV_PULP=0/1`, `COREV_CLUSTER=0`, `FPU=0`, `ZFINX=0`. The 37 RTL files, project-local BUFGCE gate and Xilinx `glbl.v` are the known working source boundary. These are elaboration passes, not executed instruction tests.
- The existing project has no selected processor testbench, no XDC, and historical bare-core utilization of 351 IOBs/189 available, 992 latches and 33 BUFGCEs. A bare top with all processor buses external is not the FPGA system to implement.
- Keep `FYP.xpr`, `E:/cv32e40p-master/cv32e40p-master/` and `D:/fyp-xpulpnn/` unchanged. Do not use the failing D: project as a baseline or silently import its RTL, tests, expected data or decoder patches. Its bench names old parameters (`PULP_XPULP`, `PULP_CLUSTER`, `PULP_ZFINX`) rather than the active core's names, and its address mapper aliases unmapped addresses to memory index zero. It can supply historical debugging clues only.
- Do not require Git on PATH, a Git repository, worktrees, commits, Linux, Questa, Verilator or a custom GCC build. Reproducibility must work with file snapshots and SHA-256 manifests on this Windows host.
- Primary supported configuration is RV32IMC plus existing XPULP and Route A DATE2020 XPulpNN, with cluster/FPU/Zfinx disabled. FPU/cluster combinations remain explicitly untested unless added to the approved matrix.

## 2. Source snapshot and manifest rules

Create an immutable `vendor/cv32e40p/rtl/` snapshot of the **entire** active E: RTL tree, preserving nested vendor files and headers. Preserve upstream license/notice files under `vendor/cv32e40p/` and copy/hash the original local clock gate as provenance. Record original absolute paths, file sizes, SHA-256, timestamp of capture, tool versions, original XPR hash and the verified ordered 37-file list in `verification/manifests/source_snapshot.json`. Mark vendor files read-only after verifying all source and copy hashes. Do not modify originals to make them read-only. A later vendor mismatch is a preflight failure, not an invitation to re-baseline automatically.

`rtl/core/` contains only modified core files with the same basenames as their vendor counterparts; `rtl/nn/cv32e40p_nn_alu.sv`, `cv32e40p_nn_dotp.sv`, and `cv32e40p_nn_quant.sv` hold new units. A manifest resolver must select exactly one implementation per module: an explicit overlay when requested, otherwise the frozen vendor file. It must reject duplicate modules, an absent manifest file, a vendor hash mismatch, or an unknown configuration. Do not compile both latch and FF register files; both declare `cv32e40p_register_file`. Do not compile both platform clock gates.

Use `rtl/platform/sim/cv32e40p_clock_gate.sv` for a verified glitch-free simulation gate; retain a configuration using the original BUFGCE plus `glbl`/`unisims_ver` to bridge back to the investigated baseline. Use `rtl/platform/fpga/cv32e40p_clock_gate.sv` with BUFGCE for FPGA runs. FPGA baseline and extension both select the frozen `cv32e40p_register_file_ff.sv` and the same FPGA gate. The FF RF eliminates the latch RF's global write and per-register gates; with FPU disabled only the sleep-unit core gate should remain inside the core. Verify actual counts instead of assuming a count or replacing sleep gating with an unqualified clock wire.

Proposed configurations:

| Configuration | Source selection | RF / gate | Purpose |
|---|---|---|---|
| `frozen_latch_pulp0`, `frozen_latch_pulp1` | Frozen original core | Latch / original BUFGCE | Reproduce elaboration; first executable baseline bridge |
| `frozen_ff_pulp0`, `frozen_ff_pulp1` | Frozen original core | FF / selected common platform gate | Functional baseline and FPGA comparison |
| `overlay_nn0` | Modified overlays, extension disabled | FF / same gate | Backward compatibility of edited core |
| `overlay_nn1` | Modified overlays, extension enabled | FF / same gate | Route A validation |
| `overlay_pulp0` | Modified overlays, PULP and extension disabled | FF / same gate | Disabled decode and RV32IMC regression |

The exact new parameter name belongs to the parent ISA/integration plan (proposed `COREV_XPULPNN`). The frozen original top has no such parameter: the testbench instantiation must conditionally supply the new parameter only in overlay builds. Passing it to the frozen top and accepting a warning is not a valid baseline. Extension-on/PULP-off must be rejected with the agreed configuration error rather than behave as an undocumented ISA.

## 3. Artifact and executable interface contract

Proposed directories:

```text
verification/model/          independent arithmetic + quantization Python oracles
verification/tb/             unit benches, driven core bench, OBI agents and monitors
verification/sw/common/      crt0.S, vectors.S, link.ld, mailbox.h, xpulpnn_words.h
verification/sw/tests/       RV32IMC, old-XPULP, NN, exception/interrupt/debug programs
verification/sw/bench/       scalar and packed MatMul/Conv kernels
verification/scripts/        build_sw.py, generate_vectors.py, check_results.py,
                             run_tests.ps1, run_fpga.ps1, diagnose_vivado.ps1
verification/manifests/       source/config/test lists and frozen ISA specification
artifacts/verification/<configuration>/<suite>/<seed>/
artifacts/fpga/<configuration>/<stage>/
scripts/create_vivado_project.tcl
artifacts/vivado/FYP_xpulpnn/FYP_xpulpnn.xpr
```

`run_tests.ps1` is the single public verification entry point. Proposed required flags are `-Config`, `-Suite`, and optional `-Seed` (default 1), `-MaxCycles` (suite-specific), `-GrantMax` and `-ResponseMax`. Recognized suites: `elaborate`, `smoke`, `decode`, `arith_unit`, `dotp_unit`, `quant_unit`, `isa`, `obi_stress`, `reset_irq_debug`, `regression`, `bench`, `all`. Reject unsupported suite/configuration pairs explicitly. Record the exact resolved RTL paths/hashes, generics/defines, sources, ELF hash, vector hash, seeds, timeouts, tool version strings and commands in each run's `run.json`.

Run outputs include analysis/elaboration/simulation logs, ELF, disassembly, map, memory image, expected and actual signature data, OBI transaction trace, diagnostic pipeline trace, failure waveform only when requested or on rerun, `result.json` and `summary.md`. Never overwrite the original investigation logs. Use an isolated artifact directory per run (and a run-id or timestamp beneath it on repeated invocation); do not recursively delete shared simulator directories.

Public commands, **after the scripts exist**:

```powershell
Set-Location 'C:/Users/CEG/FYP'
& './verification/scripts/run_tests.ps1' -Config frozen_ff_pulp1 -Suite smoke -Seed 1
& './verification/scripts/run_tests.ps1' -Config overlay_nn0 -Suite regression -Seed 1
& './verification/scripts/run_tests.ps1' -Config overlay_nn1 -Suite all -Seed 1
& './verification/scripts/run_tests.ps1' -Config overlay_nn1 -Suite obi_stress -Seed 42 -GrantMax 7 -ResponseMax 11
& './verification/scripts/run_tests.ps1' -Config overlay_nn1 -Suite bench -Seed 1
```

Process exit codes: 0 only for all selected applicable checks passing; 1 for an observed DUT/result/protocol failure; 2 for an unavailable tool/license, missing prerequisite or incomplete tool run. A runner must require both successful process exit and the final structured test result, because `$finish`/tool exit 0 alone does not prove assertions or comparison passed. An unsupported/nonsensical invocation fails preflight; it must not become a green skipped run.

Status vocabulary:

| Status | Meaning |
|---|---|
| `PASS` | Selected test actually ran, reached its success condition, matched every expected result, met required case/coverage counts, and had no assertion/unknown/protocol failure |
| `FAIL` | A valid run observed a mismatch, unexpected trap/write, protocol violation, illegal termination, unknown architectural value, or DUT timeout under the promised bounded memory service |
| `UNRUNNABLE` | Required executable/license/source/prerequisite unavailable; analysis/elaboration or tool startup did not finish; simulation never executed the selected program |
| `NOT_RUN` | Planned check has not been attempted |
| `NOT_APPLICABLE` | A named, documented feature is absent from the frozen interface; excluded from numerical pass totals but retained in scope reporting |

A complete RTL verification claim requires all mandatory applicable suites to pass. A deliberately withheld memory response is a negative environment test and must report `EXPECTED_WATCHDOG` as its case outcome under a passing negative-test suite, not falsely claim successful program completion.

## 4. Software build and memory contract

Use the discovered tools by absolute path:

```text
E:/vivado/2026.1/Vivado/bin/{xvlog,xelab,xsim,vivado}.bat
D:/fyp-xpulpnn/tools/xpack-riscv-none-elf-gcc-15.2.0-1/bin/riscv-none-elf-{gcc,objcopy,objdump}.exe
C:/Users/CEG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe
```

`build_sw.py --test <name> --isa <rv32imc|xpulp|xpulpnn> --seed <n> --out <absolute-dir>` checks GCC/objcopy/objdump exit codes, uses no shell command concatenation, and emits ELF, map, disassembly, byte-addressed Verilog image and word-addressed little-endian images. Python subprocess argument arrays handle paths safely. Shared build flags: `-march=rv32imc_zicsr -mabi=ilp32 -mcmodel=medany -nostdlib -nostartfiles -ffreestanding -fno-builtin -fno-pic -fno-pie -msmall-data-limit=0 -mno-relax`; tests use `-O2`, controlled by the manifest. Explicit `zicsr` is needed for current binutils' CSR assembly. No XPulpNN mnemonic support is assumed. Assembly macros emit frozen `.word` encodings with fixed, documented register operands; generated numeric constants come from the frozen encoding manifest. Inspect disassembly plus raw opcode words even when objdump prints an unknown mnemonic.

Proposed software/memory layout, shared by the core simulation and on-chip system wrapper:

| Range/address | Role |
|---|---|
| `0x00000000..0x0000FFFF` | 64 KiB instruction memory, also readable on data port for `.rodata` |
| `0x00000100` | 256-byte-aligned trap/vector table (`mtvec_addr_i`) |
| `0x00000200` | `_start` and `boot_addr_i` |
| `0x00000400` | Debug entry (`dm_halt_addr_i`) |
| `0x00000480` | Debug exception entry (`dm_exception_addr_i`) |
| `0x00000800` onward | Main text and constants; linker ensures no overlap with entry sections |
| `0x10000000..0x1000FFFF` | 64 KiB data memory, initialized data/BSS/thresholds/signatures/stack |
| `0x1000F000..0x1000FFEF` | Reserved stack with lower guard/canary; program linker assertions bound other sections |
| `0x20000000` | Test/benchmark mailbox status: 0 running, 1 success, other nonzero failure code |
| `0x20000004`, `+0x08` | Signature base and signature word count |
| `0x2000000C` | First failing case ID / diagnostic result |
| `0x20000010..0x2000001C` | 64-bit cycle delta and 64-bit retired-instruction counter delta |
| `0x20000020` | Optional benchmark region marker; no measurement unless enabled |

Linker `ASSERT`s enforce all reserved sections and memory sizes. Startup initializes `sp`/`gp`, clears BSS, sets vectored `mtvec`, clears/initializes all test-visible state, enables mcycle/minstret via `mcountinhibit`, then calls a freestanding `main`; no libc constructors, heap, printf, syscalls or implicit runtime are needed. Supply small local `memcpy`/`memset` helpers if generated C requires them; fail link rather than silently pull an unknown library. Traps save `mcause`, `mepc` and relevant CSRs/registers into a fixed signature record; test-specific expected traps advance the correct 2/4-byte PC and return. Unexpected traps write failure status.

The image converter validates segments and ranges; it must never turn an unknown address into word zero. Keep byte-addressed objcopy output separate from word `$readmemh` files. Data memory is initialized at load address equal to run address for these tests, avoiding an unimplemented ROM-to-RAM copy. Fill otherwise unused executable space with a documented trap instruction; initialize all modeled memory before reset release. Test software stores a complete signature and writes status **last**, following earlier stores on the same in-order bus. Host-side Python compares every declared signature word to an independent oracle rather than trusting software's own success flag.

## 5. A real processor testbench

`verification/tb/tb_core_program.sv` instantiates the **active top** (`cv32e40p_top`, including its optional-FPU wrapper) rather than an undriven bare core. Drive every input deliberately:

- `clk_i`: 10 ns period; `rst_ni`: asserted for at least 10 full source-clock cycles and released on the opposite clock edge; `fetch_enable_i`: zero until initialization/reset complete, then pulse or assert to start.
- `pulp_clock_en_i=1`, `scan_cg_en_i=0`, `hart_id_i=0`; boot/vector/debug addresses are the constants above. Cluster remains disabled.
- Instruction bus: `instr_req_o`, `instr_addr_o` into an instruction OBI memory agent, which drives `instr_gnt_i`, `instr_rvalid_i`, `instr_rdata_i`.
- Data bus: `data_req_o`, `data_we_o`, `data_be_o[3:0]`, `data_addr_o[31:0]`, `data_wdata_o[31:0]` into a data agent, which drives `data_gnt_i`, `data_rvalid_i`, `data_rdata_i`.
- `irq_i[31:0]=0` and `debug_req_i=0` except in named tests. Observe `irq_ack_o`, `irq_id_o`, `debug_havereset_o`, `debug_running_o`, `debug_halted_o`, `core_sleep_o` in their directed suites.

Two in-order request/response queues serve the ports independently. Accept a transaction exactly on a sampled `req && gnt`; capture the entire address/control tuple at that event. Return exactly one in-order response for every granted load **and store**. Apply byte enables correctly. Service data transactions strictly in accepted order: apply a queued store and sample a queued load's returned data at that request's service event, retaining the result until its response. A delayed load must not accidentally observe a later accepted store because its address is reread from live memory at an arbitrary response cycle. Response payload belongs to the queued accepted address, not today's address bus. Allow simultaneous new acceptance/old response. Use independently seeded grant and response delays, default response latency at least one clock; test zero-wait grant separately without assuming same-cycle response is required. Delays count down independently so progress is guaranteed under the bounded-delay configuration. The agent's capacity must exceed the observed architectural outstanding bound and must never silently overwrite a queue entry.

Monitors assert stable request/address/we/be/wdata until grant, no orphan or duplicate responses, bounded queue depth, no X/Z when a transaction or architectural write is valid, legal byte-enable behavior and no unwanted data stores on an illegal/younger squashed instruction. At reset flush both agents' queues and specify that pre-reset transactions cannot produce a post-reset response. Reset belongs to the whole modeled system; do not assert only the CPU reset while secretly returning transactions from a previous execution unless that unsupported environment is explicitly the negative test.

Success requires observed boot fetch and progress, the correct case-count and signature, final mailbox status, drained response queues and a bounded final quiescence window with no forbidden late write. Timeout diagnostics contain last fetch PC, request/response counts, pending transactions, trap/debug state and first mismatch. A waveform is diagnostic, not a substitute for these checks.

An optional bind monitor can observe existing `dut.core_i.regfile_we_wb`, `regfile_waddr_fw_wb_o`, `regfile_wdata`, `regfile_alu_we_fw`, `regfile_alu_waddr_fw`, `regfile_alu_wdata_fw`, and accepted ID instruction/PC to diagnose wrong/duplicate writeback. These are internal pipeline events, **not an established retirement/RVFI interface**. Architectural acceptance uses stored signatures and software trap records. If a full architectural trace comparison is later required, first validate a proper retire adapter against the frozen baseline; do not label raw ID acceptance as retirement.

## 6. Oracles, decode legality and test coverage

`verification/model/packed.py` implements operations using mathematical Python integers, explicit lane extraction, signed interpretation and final width masks. Do not translate the RTL implementation or share its intermediate carry/sign/selection helpers. `quantize.py` implements direct threshold classification from the frozen local semantics based on DATE2020, independently of the RTL search FSM, threshold address calculation and LSU ownership logic. Models may share reviewed encoding/semantic input data with vector generation; they must not derive expected results from RTL simulation or previously failing D: outputs. Verify models first against manually worked edge examples in the ISA specification. Final mandatory sample counts and public interfaces are owned by the reviewed specification and implementation plan; larger populations below are research suggestions rather than an additional hidden acceptance gate.

The parent quantization contract fixes two 64-byte channel table slots: operand base points at the first slot, channel two uses base+64; the base is 64-byte aligned and at most `0xFFFFFF80` to prevent wrap across the second slot. Tables contain 15 thresholds for Q=4 or 3 for Q=2, each a signed int16 value sign-extended in one 32-bit memory word, in ascending order. Rank is the count of thresholds for which activation >= threshold (equality enters the upper bin). Output code is `rank - 2^(Q-1)`, represented in Q-bit two's complement; pack the first code in bits Q-1:0 and the second in bits 2Q-1:Q, with all upper result bits zero. Concrete independent oracle checks: Q=2 thresholds [-10,0,10], activation pair (-5,15) gives `0x00000007`; Q=4 thresholds [-7,-6,...,7], activation pair (-8,8) gives `0x00000078`. Test both slots with different tables to expose an erroneous shared-table implementation. Reject invalid bases with illegal-instruction cause 2 and no issued threshold request; base validation must use the forwarded operand once it is ready, so also test a prior instruction producing a valid/invalid base and a load-use dependency. Padding words must not be accessed as thresholds. Additional table-content validity checks apply only if the parent contract defines hardware handling; alignment/overflow checking does not imply scanning a whole table before quantizing.

Required finite directed coverage and seeded randomized work:

| Layer | Required test population and checks |
|---|---|
| Encoding/decode | Every legal op/width/signedness/vector/scalar/immediate form from the approved ISA table; every reserved selector; disable behavior; unknown custom words. Independently check mask/value overlap against existing instruction families. Compare frozen and overlay decoder outputs for all enumerated legacy selector combinations, register-zero/nonzero/alias representatives, immediate extremes and deasserted write-enable mode. New enabled words must enter only their declared path; illegal words must have no memory or register side effects. |
| Packed ALU | Exhaust all 2-bit lane operand pairs (16) and 4-bit pairs (256) per operation/mode; move lane cases through every position, vary neighboring lanes to expose carry/borrow leakage; min/max, zeros/ones, alternating bit patterns, signed compares/shifts and every immediate/broadcast boundary actually supported. Then at least 10,000 full packed random input tuples per operation/form with recorded seeds. |
| Dot/MAC | Exhaust small lane pairs as above; vary all packed lanes, signed/unsigned/mixed modes actually specified, result sign extension and 32-bit wraparound, accumulator extremes. Check accumulation with `rd=rs1`, `rd=rs2`, all-equal registers, x0 source/destination, back-to-back and load-fed dependencies. Require zero unexpected writes and one correct architectural result per nonsquashed instruction. |
| Quant arithmetic | Sweep all 65,536 possible 16-bit activation bit patterns for each selected legal threshold table; test both packed activation positions, distinct paired values and randomized pairs. Require equality to every threshold, extreme below/above values and every output level. Cover repeated/equal/unsorted thresholds only as their legality is defined in the frozen spec. Exhausting individual activations does not mean all 2^32 activation pairs are exhausted. |
| Quant protocol | Scoreboard exact required threshold values/addresses, number and ordering of accepted loads, address alignment, activation sequencing, operand capture, final packing, pointer writeback if specified, no duplicates, no stores and final completion. Hold initial operands stable per unit interface; in the core tests vary subsequent pipeline operands to expose failure to capture. |
| Core pipeline | Every new op executes in a program and is immediately consumed/stored; RAW/WAW, all meaningful aliases, preceding/following load/store, mul/div, taken/not-taken branch, branch flush of younger NN word, compressed instructions on both sides, hardware-loop boundaries, interrupts/debug around multicycle issue/completion, and repeated quant instructions with distinct thresholds. |
| Legacy regression | RV32I/M/C, CSR/exception behavior, loads/stores including byte enables and split misaligned accesses supported by this core, mul/div extremes, old XPULP 8-/16-bit SIMD/dotp, hardware loops, bit manipulation and postincrement instructions selected from the active decoder. Run identical program/data on frozen baseline, overlay extension-off and overlay extension-on. Compare complete signatures/trap records and declared allowed memory writes; compare cycle counts only when identical timing is promised. |

Illegal-instruction programs verify `mcause=2`, saved instruction PC, no destination/pointer update and no threshold/data transaction from the illegal word. Trap handlers themselves must run using the declared subset and preserve the signature/register state being tested. A decoder-unit comparison alone does not verify architectural trapping.

At least seeds 1..10 run the complete bounded OBI stress suite with independent instruction/data grant delays 0..7 and response delays 1..11; retain a deterministic zero-stall configuration for reproducible performance. Add one-at-a-time directed stress for queue-full/backpressure, last threshold response coincident with younger issue, pending ordinary load before quant, and load/store immediately after quant. Generate a coverage JSON with op × width × form × signedness, alias, threshold equality/level, LSU delay/overlap, reset phase and interrupt/debug timing bins. Mandatory unhit bins prevent suite `PASS`; randomized sample counts alone are insufficient.

## 7. Reset, interrupt, debug and the actual fault boundary

The active top has **no `instr_err_i` or `data_err_i` port**. `cv32e40p_core.sv` ties IF external error to zero (around line 454), LSU external error to zero (around line 896), and uses `USE_PMP=0` with `data_err_pmp=0` (around line 1116). `cv32e40p_load_store_unit.sv` explicitly states external/PMP errors are unsupported and asserts they remain zero (around lines 492..506). Therefore a precise bus-fault exception suite is `NOT_APPLICABLE` for this Route A interface. Inventing error pins, a PMP configuration or forced internal error wires would test a changed architecture and needs a separate design decision.

Applicable memory-failure checks are strict out-of-range/permission/unaligned-threshold address checks at the test environment boundary, no silent aliasing, bounded grant/response failure detection, and deterministic reset/recovery. An invalid program address must generate a case failure or the explicitly expected negative-test outcome; it cannot be counted as the core taking an unimplemented access-fault trap. A lost response can legitimately stall this no-error interface; the bench watchdog must report that condition accurately.

Reset tests cover before grant, after grant/before response, between quant threshold responses, final response/writeback overlap and immediately after completion. Assert reset for CPU, quant FSM, memory queues and mailbox, then reboot a fresh image or execution epoch; check no stale request/response/result survives. Save an epoch/case identifier to distinguish a replayed pre-reset result from a successful new execution.

IRQ tests enable a supported machine interrupt in software, inject it before NN issue, while ordinary load/quant memory service is delayed, and at completion. Observe ack/id, trap record and correct resume/result count. Debug tests place a valid debug entry at the configured address; inject `debug_req_i` at the same boundaries, observe halt/running, inspect saved `dpc`/debug state through a debug-handler signature, and execute `dret` to resume. Do not require a granted OBI transaction to be cancelled on interrupt/debug: finish or drain accepted traffic according to the core's precise instruction boundary contract. The design and checks must explicitly specify when the multicycle instruction is considered complete and when debug/IRQ can be acknowledged. The normal instruction tests must not tie debug entries to boot and mistake a restart for recovery.

## 8. Concrete simulator invocation shape

`run_tests.ps1` resolves manifests and writes a per-run `sources.prj` plus quoted `xelab.args`; packages precede dependent modules; selected NN modules precede top benches. Use the verified invocation shape and check every exit code:

```powershell
# Invoked inside the isolated artifact directory after image/vector generation.
& 'E:/vivado/2026.1/Vivado/bin/xvlog.bat' --sv --prj sources.prj `
  -i 'C:/Users/CEG/FYP/vendor/cv32e40p/rtl/include' `
  -i 'C:/Users/CEG/FYP/vendor/cv32e40p/rtl/vendor/pulp_platform_common_cells/include' `
  --log xvlog.log
& 'E:/vivado/2026.1/Vivado/bin/xelab.bat' `
  xil_defaultlib.tb_core_program xil_defaultlib.glbl -L unisims_ver `
  --file xelab.args --mt 2 --timescale 1ns/1ps `
  --snapshot run_core --log xelab.log
& 'E:/vivado/2026.1/Vivado/bin/xsim.bat' run_core `
  --tclbatch run.tcl --log xsim.log
```

`run.tcl` contains `run all` then `quit`; the bench reads per-run fixed filenames (`imem.hex`, `dmem.hex`, `test_config.hex`, expected vectors) and owns its cycle timeout, so no unverified simulator-specific plusarg convention is required. `xelab.args` contains quoted testbench `--generic_top` assignments rather than unquoted Windows `=` arguments. Unit suites select their unit bench top and do not accidentally elaborate/run the core program top. The original-BUFGCE and FPGA-gate simulations include `glbl.v` and `unisims_ver`; a behavioral-gate run must name its different manifest clearly.

## 9. MatMul and convolution performance

Use two deterministic kernels small enough for the proposed on-chip memory: MatMul `M=8, K=32, N=8`; valid 3×3 convolution with `H=W=8`, `Cin=8`, `Cout=8`, stride 1, no spatial padding (`Hout=Wout=6`). Test 4-bit and 2-bit data under the signedness/quantization definitions that the ISA actually supports. Convolution reduction length is `K=3*3*8=72`, already a required packing-tail case: 2-bit SIMD has 16 lanes, so its final packed block contains eight valid values and eight zero lanes. Define bounded, zero-padded reduction buffers and their physical row/channel strides explicitly; padding must never read the next logical row, channel or out-of-bounds memory, and may not change output semantics. The 4-bit path uses nine complete eight-lane blocks. Trace/report logical MAC counts separately from physical packed-lane operations and padded lanes. Add other non-multiple tails (for example MatMul K=35) as correctness cases while retaining the fixed published benchmark dimensions.

The required primary baseline is the existing 8-bit XPULP implementation, reflecting the paper's already PULP-capable 8-/16-bit starting core. Both implementations receive the same stored packed 4-/2-bit input and weight representation: the legacy path includes the necessary unpacking/sign extension into 8-bit vectors, existing 8-bit dot-product instructions and software threshold quantization; XPulpNN uses native DOT4/DOT2 and quantization instructions. Build the legacy program with `build_sw.py --isa xpulp` and raw `.insn` or `.word` instruction macros with frozen encodings, because stock GCC is not assumed to support local XPULP mnemonics. Run it on both the frozen PULP-enabled baseline and edited core; run the XPulpNN binary only with the extension enabled. A plain scalar RV32IMC implementation is an optional secondary comparison, and must never replace the required legacy 8-bit denominator.

Compute int32 accumulation in a defined order with defined wrap/saturation semantics and exactly identical output quantization. Host Python independently computes every output, and all compared implementations must produce the same full output signature before their cycle counts are accepted. Record compiler flags, disassembly/raw instruction words, input/weight representation, threshold tables, unpacking work, logical MAC counts, physical SIMD operations/padding, all output hashes and code size.

Enable mcycle/minstret explicitly (the active core's `mcountinhibit` resets counters inhibited). Read 64-bit counters with high/low/high retry or use a proven bounded 32-bit delta for a short region. Use compiler memory barriers around the measured calls. Run an empty measurement bracket for overhead, and report raw deltas plus separately stated overhead; never subtract silently. Primary kernel timing starts from the common packed representation and includes the legacy path's required unpacking/sign extension, dot-product work and software quantization, and the NN path's native dot-product work and required threshold loads/quantization. Any pre-expanded 8-bit inner-loop-only timing is an additional explicitly labeled diagnostic, not the primary denominator. Report end-to-end timing including shared input preparation/setup as a second metric. No printf/mailbox/signature comparison sits inside the measured region. Report external source-clock elapsed cycles too, so clock gating and counter enable mistakes can be detected.

Primary performance comparison uses the same deterministic memory service and RF/gate for both cores; a second fixed delay profile shows memory sensitivity. Report cycles, instructions, outputs and cycles/output; primary speedup is measured legacy 8-bit XPULP cycles / XPulpNN cycles for identical low-bit data and exact outputs. Report optional scalar cycles / XPulpNN cycles separately as a secondary metric. Do not promise the paper's speedup, ASIC area or energy result on this FPGA/toolchain. FPGA resource/timing comparison and instruction-cycle speedup are separate findings.

## 10. FPGA validation boundaries and commands

Create a separate project with `scripts/create_vivado_project.tcl`; leave `FYP.xpr` unchanged. Read resolved vendor/overlay sources, exactly one FF RF and FPGA BUFGCE gate. Part is the established `xck26-sfvc784-2LV-c`; record the board property if available, but do not infer a board clock/pin mapping from the part or board name alone.

Add `rtl/platform/fpga/fyp_nn_system.sv` as a synthesizable system top with external `clk_i`, `rst_ni`, `start_i`, `done_o`, `pass_o`, and `signature_o[31:0]` (37 signal bits total). It contains `cv32e40p_top`, 64 KiB instruction/constant BRAM, 64 KiB data BRAM, registered in-order OBI responses and the same mailbox decoder described above. All core address, instruction, data, interrupt and debug buses remain internal. `start_i` is sampled synchronously after reset and enables fetch; completion/status is captured in registers. Tie IRQ/debug inputs to zero for the normal FPGA benchmark; their functionality is covered in simulation. Check BRAM inference rather than assuming inferred arrays became memory resources. Initialize memories from a recorded fixed self-test/benchmark image and preserve its hash in the reports.

First run a wrapper-level simulation against the identical memory map/image and compare output signature with the core bench. Then two comparable flows:

1. Core out-of-context synthesis (`cv32e40p_top`) establishes logic-only area with an explicit 10 ns `create_clock` on `clk_i`, FF RF, identical gate, part and synthesis settings. Raw I/O usage is irrelevant to this OOC experiment.
2. System-wrapper out-of-context synthesis and place/route uses `fyp_nn_system`, identical on-chip memories/image, constraints and implementation settings for frozen baseline versus extension. Report core hierarchy utilization as well as total system utilization, BRAMs, DSPs, latches, BUFGs, setup/hold timing, unconstrained endpoints, DRC and clock interaction. Timing target begins at 100 MHz (10 ns) as an experiment; failure is recorded, not hidden by lowering the target on only one design. An optional 20 ns rerun must rerun **both** configurations with identical changed constraints and retain both 10 ns failures/results. Comparisons across different targets are not treated as a controlled area/timing comparison.

Planned entry points:

```powershell
& 'E:/vivado/2026.1/Vivado/bin/vivado.bat' -mode batch `
  -source 'C:/Users/CEG/FYP/scripts/create_vivado_project.tcl' `
  -tclargs 'C:/Users/CEG/FYP' 'overlay_nn1'
& './verification/scripts/run_fpga.ps1' -Config frozen_ff_pulp1 -Stage core_ooc -ClockPeriodNs 10
& './verification/scripts/run_fpga.ps1' -Config overlay_nn1 -Stage core_ooc -ClockPeriodNs 10
& './verification/scripts/run_fpga.ps1' -Config frozen_ff_pulp1 -Stage system_ooc -ClockPeriodNs 10
& './verification/scripts/run_fpga.ps1' -Config overlay_nn1 -Stage system_ooc -ClockPeriodNs 10
```

The Tcl implementation includes `synth_design -mode out_of_context -top <top> -part xck26-sfvc784-2LV-c`, explicit `create_clock -name clk_i -period 10.000 [get_ports clk_i]`, `opt_design`, `place_design`, `phys_opt_design`, `route_design`, checkpoints and named reports. Verify generated gated-clock relationships and constrain only real clock domains; do not blanket false-path NN/control/BRAM paths or asynchronous reset recovery/removal to obtain a timing pass. OOC ports must be described as module boundaries; OOC internal timing does not prove system input/output timing or board operation.

A board-ready bitstream and real hardware benchmark require a separate board harness with verified clock source, reset polarity/synchronization, package pins, I/O standards and configuration voltage plus a way to observe/load results (for example confirmed LED/UART/JTAG registers). No such XDC exists in the current project. Do not invent KV260 pins, declare unconstrained-port DRC warnings harmless for a bitstream, or call an OOC routed checkpoint a working board implementation. If board facts cannot be established, report `PASS`/`FAIL` for the completed OOC synthesis/internal-timing experiment and `NOT_RUN`/`UNRUNNABLE` for board implementation/programming, separately. This preserves useful FPGA feasibility results without overstating them.

## 11. Vivado startup-stall assessment and bounded diagnosis

Read-only findings: `baseline/checkpoint.log` says a valid Enterprise license was accepted (expiry shown as 2026-12-15), then prints startup host information for PID 27688. `checkpoint.jou` also stops at the header; no Tcl command or marker is present. The retained attempt note records over three minutes without script progress before only that explicitly identified probe process was terminated. Thus the attempted run did not establish an `open_checkpoint` hang, a DRC problem or a license failure. A process inventory during this notes task found no Vivado/xsim/xelab/xvlog process matching the targeted command lines. No user `Vivado_init.tcl` was found in the inspected project/current directory or the inspected per-user Xilinx locations; installed Tcl-store initialization exists but has not been implicated. These observations do not establish or exclude a transient GUI/profile/resource/lock issue at the earlier time. Do not claim “GUI lock” as a root cause.

After approval, `diagnose_vivado.ps1 -Mode Startup` should launch a minimal batch Tcl in a fresh artifact directory. Its first line writes/flushed `TCL_STARTED` plus timestamp, version and working directory, and it then exits. Bound startup to 180 seconds, poll logs/process state in short intervals, record PID/parent/command line/start time and only terminate that exact launched process on timeout. Do not close a user's GUI, delete locks/profile caches or change licenses. If startup works, use `-Mode Checkpoint` with markers immediately before/after `open_checkpoint`, each report and `close_design`; then retry OOC synthesis with its own phase markers. Separate tool startup failure, checkpoint-read failure, synthesis failure and timing failure in `result.json`. Keep log/journal names unique.

Use the normal installed `vivado.bat` entry point with explicit `-mode batch -source <absolute-script> -log <unique-log> -journal <unique-journal>`; do not bypass its setup/loader scripts or install a second tool as the first troubleshooting step. There is no evidence yet that a command-line flag change resolves the stall. If startup remains unrunnable, executable xsim ISA verification can continue independently, while FPGA validation remains honestly incomplete.
