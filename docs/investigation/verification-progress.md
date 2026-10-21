# Verification execution ledger

Historical ledger starting 2026-10-20. The intermediate status tables below are retained as dated observations; the final 2026-10-21 closure at the end supersedes their pending items.

| Check | Status | Evidence |
|---|---|---|
| Independent models/ABI tests | PASS | `verification/tests/test_models.py`: 4 tests; all72 form encode/mask checks, wrap-before-shift avg, signed/mixed dot, qnt opposite branches/equality |
| Independent ALU/dot vectors | GENERATED | `artifacts/verification/vectors/vectors.json`: seed1, 304080 vectors, exhaustive individual lane pairs plus10000 random packed operands per operation/mode; generation is not an RTL pass |
| Real frozen FF baseline smoke | PASS | `artifacts/verification/frozen_ff_pulp1/smoke/1/20261020-154025-562467/result.json`: 7 signature words,178 cycles,59 instruction requests,12 data requests,0 protocol failures |
| Frozen core new arithmetic ISA | EXPECTED RED / FAIL | `artifacts/verification/frozen_ff_pulp1/isa/1/20261020-154046-173907/result.json`: real fetched new opcode traps cause2 (status0x80000002),90cycles; legal-new-instruction expected210-word signature absent |
| Initial baseline harness finish | UNRUNNABLE (resolved) | `artifacts/verification/frozen_ff_pulp1/smoke/1/20261020-153951-542822/xsim.log`: XSim kernel error with string task argument at finish; changed outcome to integer and reran fresh successful test above |
| Edited core arithmetic/quant and full legacy regression | NOT_RUN | Waiting for integration; current `regression` entry only selects smoke and must not be reported as complete legacy coverage |
| Reset/IRQ/debug core tests, benchmark kernels, FPGA | NOT_RUN | Implementation remains in progress |

## 2026-10-21 continuation evidence

| Check | Status | Evidence |
|---|---|---|
| XSim nonzero-exit classification | PASS (host) | `verification/tests/test_build_and_results.py::test_nonzero_xsim_exit_is_a_dut_failure` proves a process failure in the simulation phase maps to `FAIL`; prepare/elaboration/tool failures remain `UNRUNNABLE`. Full host suite: 14 tests PASS. |
| qnt bad-base forwarding and trap precision | PASS | `artifacts/verification/overlay_nn1/quant_bad_base/1/20261021-114354-381392/result.json`: immediate `lw -> qnt` invalid bases, one ALU-forwarded valid base, and one ALU-forwarded unaligned base; 16 signature words, 32 data requests, one valid qnt commit, no OBI protocol failure. |
| reset/IRQ/debug phase suite | PASS, limited named coverage | `artifacts/verification/overlay_nn1/reset_irq_debug/1/20261021-111537-370366/result.json`: IRQ, debug and reset phases 0--3 each completed with one qnt commit. The current phase names do not separately prove a terminal-commit request, a final-writeback hold, or a distinct pre-issue/single-step stimulus. |
| OBI two-outstanding protocol | PASS (LSU unit), system coverage pending | `verification/tb/tb_nn_lsu.sv` checks two FIFO tags and simultaneous pop/push. The current core-memory agent deliberately permits one outstanding request per port, so an end-to-end depth-two outstanding run remains pending. |
| benchmark K=35 tail regression | PASS after one traced fix | Initial failure is retained at `artifacts/verification/overlay_nn1/bench/1/20261021-111910-795149/result.json`: q4 tail native result differed (`0x25` expected, `0xd8` actual), program status `0x102`; no protocol failure. Root cause was `prepare()` using logical K rather than padded physical row stride for tail row 2. Fresh `artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/result.json` passes all 472 words: q4/q2 MatMul, Conv and K=35 tails, scalar, legacy dot8 and native kernels. Total program cycles are not a kernel-comparison metric; use the separately recorded brackets. |
| Negative environment watchdog | NOT_RUN | No dedicated no-response/timeout artifact has been recorded; it must be reported separately from successful program execution. |

Public entry: `verification/scripts/run_tests.ps1 -Config frozen_ff_pulp1 -Suite smoke -Seed 1`. Each invocation uses an isolated artifact directory and requires a structured completion record plus full host signature comparison. OBI agents provide at least one source-clock response latency and enforce held request stability. Current agents deliberately backpressure at one outstanding request per port; deeper overlapping response coverage remains a separate required addition.

## Final closure — 2026-10-21

All pending functional items above are resolved in the [final verification index](../results/verification-index.md), whose release-current status is PASS. The final `all` has 19 top-level groups and 42 leaves, with six old-TB leaves explicitly replaced by current-hash reruns. Seeds 1/42/20261020 cover OBI stress. Directed events now include phases 0–5, real single-step/DBG_FLUSH, final-writeback backpressure and reset boundaries. The core agent supports depth two and a passing test reaches two outstanding qnt reads; the earlier one-outstanding-only limitation is historical.

Negative no-response and unmapped-threshold tests are explicitly recorded. The first expects a watchdog without a qnt commit, and the second a TB address rejection; neither is represented as a successfully completed program or an architectural memory-fault proof. Host checks total 17 PASS.

Both final system-wrapper simulations pass their 472-word checks with the same ROM. Eight core/system OOC runs establish passing baseline/NN 20 ns timing and preserve failing NN 10 ns timing. See the [final validation report](../results/xpulpnn-route-a-validation.md) for exact resources, local benchmark boundaries and NOT_RUN board/power work. The [independent review](../results/independent-review.md) is closed.
