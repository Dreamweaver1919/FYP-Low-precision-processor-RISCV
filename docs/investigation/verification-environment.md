# Verification environment investigation

Inspected on 2026-10-20, Windows, for `C:/Users/CEG/FYP/FYP.xpr`.

## What was actually verified

The existing core's RTL compiled with Vivado Simulator 2026.1, and the core top elaborated successfully with **both `COREV_PULP=0` and `COREV_PULP=1`**. These probes used `COREV_CLUSTER=0`, `FPU=0`, and `ZFINX=0`, matching the project's other generics. They did not execute a program or check XPulpNN instruction results. No XPulpNN extension has been verified by this investigation.

Fresh evidence is in `docs/investigation/baseline/`:

| Probe | Result | Evidence |
|---|---|---|
| RTL analysis | Exit 0; 37 selected existing RTL files plus Xilinx `glbl.v` | `xvlog.log` |
| Core elaboration, PULP disabled | Exit 0; `Built simulation snapshot baseline_pulp0` | `xelab_pulp0.log` |
| Core elaboration, PULP enabled | Exit 0; `Built simulation snapshot baseline_pulp1` | `xelab_pulp1.log` |
| Simulator executable | `Vivado Simulator v2026.1` | Executed `xsim.bat --version` |
| RISC-V compiler executable | xPack GNU RISC-V Embedded GCC 15.2.0; target `riscv-none-elf` | Executed `--version` and `-dumpmachine` |
| Python executable | Python 3.12.14 | Executed `--version` |

The baseline manifest was extracted from the source list in the existing `FYP.runs/synth_1/cv32e40p_top.tcl`, with packages ordered before modules. This preserves the active **latch register file**, the local **BUFGCE clock gate**, and the core top. It does not indiscriminately compile all auto-disabled vendor files listed in the XPR. The XPR marks `cv32e40p_register_file_ff.sv` `AutoDisabled=1`.

The local clock gate instantiates Xilinx `BUFGCE`. Elaboration therefore needs `-L unisims_ver` and Xilinx `glbl.v` as an additional top. The first probe found the missing `glbl`; adding that existing vendor dependency resolved it. Logs of the initial invocation/`glbl` failures are retained as `xelab-invocation-failed.log` and `xelab-missing-glbl.log`. No RTL was edited to obtain a pass.

## Available tools

| Tool | Actual path / observation |
|---|---|
| Vivado batch | `E:/vivado/2026.1/Vivado/bin/vivado.bat` |
| xvlog | `E:/vivado/2026.1/Vivado/bin/xvlog.bat` |
| xelab | `E:/vivado/2026.1/Vivado/bin/xelab.bat` |
| xsim | `E:/vivado/2026.1/Vivado/bin/xsim.bat` |
| Underlying executable directory | `E:/vivado/2026.1/Vivado/bin/unwrapped/win64.o/` |
| RISC-V GCC | `D:/fyp-xpulpnn/tools/xpack-riscv-none-elf-gcc-15.2.0-1/bin/riscv-none-elf-gcc.exe` |
| RISC-V assembler, objcopy, objdump | Same GCC `bin/`, with `riscv-none-elf-` prefixes |
| Bundled Python | `C:/Users/CEG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` |
| Git | `C:/Users/CEG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe` |
| ripgrep | Available on PATH through the Codex application `bin` |
| Icarus Verilog / Verilator / Yosys | Not on PATH; not found in the targeted `C:/tools`, `C:/Apps`, or existing `D:/fyp-xpulpnn/tools` trees |
| RISC-V `unknown-elf` GCC names | Not on PATH; use the discovered `riscv-none-elf-gcc.exe` instead |
| `python` / `python3` on PATH | WindowsApps aliases; use the working bundled executable above |

Vivado and simulator tools are not on PATH. No installation or system configuration was changed. No applicable `AGENTS.md` was found in the project, its checked ancestors, or the external core source tree. A WSL inventory command did not return a usable distribution listing, so no Linux/WSL verification environment is assumed.

The stock GCC/binutils installation provides a practical route to RV32 assembly programs and raw custom instruction words (`.word` / `.insn`) after encoding decisions. XPulpNN mnemonic support and compiler intrinsics were not tested or established.

## Existing project evidence

- Project top: `cv32e40p_top`; part: `xck26-sfvc784-2LV-c`; board: `xilinx.com:kv260_som:part0:2.0`.
- Project generics are already `COREV_PULP=1`, `COREV_CLUSTER=0`, `FPU=0`, `ZFINX=0` (`FYP.xpr`, sources_1 configuration). Enabling COREV_PULP alone is not an XPulpNN implementation.
- Most RTL references point outside the project to `E:/cv32e40p-master/cv32e40p-master/rtl/`. Only `FYP.srcs/sources_1/new/cv32e40p_clock_gate.sv` is a project-local RTL source. The baseline depends on both locations.
- `sim_1` has no simulation source entries and its auto-selected top is `cb_filter`, not a processor testbench. `FYP.sim/` was empty. No project-local program execution or instruction scoreboard evidence was found.
- `FYP.runs/synth_1/runme.log` records a completed Vivado 2026.1 synthesis on 2026-10-20 at 10:30:35, with `synth_design completed successfully`, 0 errors and 0 critical warnings. It also records many ordinary warnings (752 synthesis warnings; the overall summarized message count is 241 warnings). This is historical evidence, not a new synthesis run.
- The historical synthesis used `COREV_PULP=1`, `COREV_CLUSTER=0`, `FPU=0`, `ZFINX=0` and generated `FYP.runs/synth_1/cv32e40p_top.dcp`.
- Its utilization report records 6,976 LUTs, 1,590 flip-flops, 992 latches, 7 DSPs, and 33 BUFGCEs. **351 bonded IOBs are required against 189 available (185.71%).** The bare core top therefore is not a board-ready design with all current ports exposed as external pins.
- No XDC entries exist in `constrs_1`. There is no established clock target or board pin/timing constraint set in the active project. Synthesis resource utilization does not establish timing closure or a working FPGA bitstream.

The external core contains `example_tb/core/tb_top.sv`, `cv32e40p_tb_subsystem.sv`, and a Makefile aimed at ModelSim/Questa `10.7b` and a `riscv32-unknown-elf-` toolchain. They are not selected by this XPR and were not run. The unrelated `D:/fyp-xpulpnn/sim/` has prior test sources and logs; its inspected `xsim.log` ends `FAIL: 4800/4800 mismatches`. Those logs are not verification evidence for this FYP project and nothing in that tree was modified.

An optional fresh checkpoint-only DRC/timing inspection was attempted with `baseline/inspect-checkpoint.tcl`. Vivado accepted the license, but the log remained at startup host information for over three minutes without executing the Tcl or producing reports. Only the launched probe process, verified by PID 27688 and its exact command line, was terminated. `checkpoint.log` and `checkpoint-attempt.txt` retain the evidence. **No fresh DRC/timing result is available.** The existing IOB utilization and absence of XDC constraints remain the directly observed board/timing limitations.

To retry that optional read-only checkpoint inspection:

```powershell
Set-Location 'C:/Users/CEG/FYP/docs/investigation/baseline'
& 'E:/vivado/2026.1/Vivado/bin/vivado.bat' -mode batch `
  -source inspect-checkpoint.tcl -log checkpoint.log -journal checkpoint.jou
```

The Tcl opens the existing synthesized DCP and requests `report_drc`, `report_timing_summary -report_unconstrained`, and `report_clocks`; it does not run synthesis or implementation. Even if it succeeds on retry, a no-clock/unconstrained report would not establish timing closure.

## Reproduce the completed baseline

Run from PowerShell; the runner changes into its own artifact directory and checks process exit codes:

```powershell
& 'C:/Users/CEG/FYP/docs/investigation/baseline/run-baseline.ps1'
```

The commands inside the runner are equivalent to:

```powershell
Set-Location 'C:/Users/CEG/FYP/docs/investigation/baseline'
& 'E:/vivado/2026.1/Vivado/bin/xvlog.bat' --sv --prj baseline.prj `
  -i 'E:/cv32e40p-master/cv32e40p-master/rtl/include' `
  -i 'E:/cv32e40p-master/cv32e40p-master/rtl/vendor/pulp_platform_common_cells/include' `
  --log xvlog.log
& 'E:/vivado/2026.1/Vivado/bin/xelab.bat' `
  xil_defaultlib.cv32e40p_top xil_defaultlib.glbl -L unisims_ver `
  --file xelab-pulp0.args --mt 2 --timescale 1ns/1ps `
  --snapshot baseline_pulp0 --log xelab_pulp0.log
& 'E:/vivado/2026.1/Vivado/bin/xelab.bat' `
  xil_defaultlib.cv32e40p_top xil_defaultlib.glbl -L unisims_ver `
  --file xelab-pulp1.args --mt 2 --timescale 1ns/1ps `
  --snapshot baseline_pulp1 --log xelab_pulp1.log
```

The argument files hold quoted `--generic_top` assignments, avoiding Windows batch parsing of unquoted `=` arguments. These commands build snapshots only. A simulation with undriven core inputs would not establish processor correctness, so none is presented as an ISA test.

## Proposed extension verification matrix

These are required future checks, not completed claims. Encodings and exact numerical semantics must first be frozen against the supplied DATE2020 paper and the active CV32E40P ISA. The requested scope is 4-bit/2-bit SIMD and multi-cycle threshold quantization over the LSU, not the later MAC&LOAD/NN-RF design.

| Layer | Required cases | Pass evidence |
|---|---|---|
| Encoding/decode | Every new operation/width/signedness/form; reserved encodings; collisions with existing XPULP/RV32 instructions; COREV_PULP/extension disabled | Machine-readable encoding map, decoder assertions/scoreboard, illegal-instruction behavior |
| Packed arithmetic | All lanes, nibble/crumb boundaries, signed minima/maxima, unsigned maxima, scalar/immediate broadcast forms where specified, overflow/carry isolation | Independent bit-accurate reference model; exhaustive small operand cases plus reproducible randomized vectors |
| Dot product/MAC | Signed/unsigned/mixed modes if specified; accumulation wrap/sign extension; rd/rs aliases; x0 behavior; consecutive and dependent operations | RTL unit tests against independent reference results and register writeback checks |
| Threshold quantization | Exact threshold equality; below/above extreme thresholds; all output levels; two packed int16 activations; pv.qnt.n/c behavior | Reference threshold model; checked packed result and intermediate sequence |
| Quantization LSU protocol | Grant/response delays, outstanding memory interaction, address and pointer updates, interleaving of two activations, reset/interrupt/flush cases permitted by core semantics | Cycle-level request/response scoreboard; no duplicate/missing load; stable held requests; correct completion/writeback |
| Pipeline integration | RAW/WAW/rd aliases; load-use dependencies; multi-cycle backpressure; branch/exception flush; loop/interrupt interaction | Core instruction programs and transaction/reference scoreboard; bounded timeouts |
| Regression | RV32IMC and existing XPULP including 8-/16-bit SIMD, mul/div, loads/stores, hardware loops; extension off | Existing baseline suite plus differential architectural trace comparisons |
| Tool configuration | Compile/elaborate PULP 0/1; baseline latch register file; explicit FF choice only if adopted; intended FPU configurations | Reproducible manifests, elaboration logs and hashes of tested RTL/configurations |
| FPGA feasibility | Compare fixed baseline vs extension under the same part/constraints; wrapper/on-chip memory to avoid externalizing core bus; clock-gating/register-file suitability | Synthesis deltas; implemented utilization/timing/DRC; achieved clock and functional hardware test |

## Scope and artifacts

Only investigation documentation, manifests, scripts, logs and simulator build artifacts under `docs/investigation/` were created. Product RTL, `FYP.xpr`, external core sources, and unrelated projects were not edited. No full synthesis, implementation, bitstream generation, installation, or extension testbench was performed.
