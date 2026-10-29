# Verification evidence index

Generated: `2026-10-21T07:01:25.045081+00:00`  
2026-10-21 release snapshot status: **PASS**.

The 2026-10-29 passive-wrapper simulation and physical KV260 trials are recorded separately in the [board validation report](kv260-board-validation.md) and [source-hashed board evidence](board-2026-10-29/summary.json). The tables below retain their original snapshot scope.

This is an evidence index, not the final validation report. It reads JSON as UTF-8 with BOM support. `NOT_RECORDED` means the historical run manifest omitted that class of source; it is not a hash match.

| Evidence | Result | Raw artifact | Current source-hash audit | Notes |
|---|---|---|---|---|
| Latest all suite | `PASS` / PASS | `artifacts/verification/overlay_nn1/all/1/20261021-122602-933820/result.json` | RTL NOT_RECORDED; TB NOT_RECORDED | Auto-discovers the newest all-suite result; rerun after all completes. |
| OBI stress seed 1 | `PASS` / PASS | `artifacts/verification/overlay_nn1/obi_stress/1/20261021-123000-699264/result.json` | RTL MATCH; TB MATCH |  |
| OBI stress seed 42 | `PASS` / PASS | `artifacts/verification/overlay_nn1/obi_stress/42/20261021-144501-828891/result.json` | RTL MATCH; TB MATCH |  |
| OBI stress seed 20261020 | `PASS` / PASS | `artifacts/verification/overlay_nn1/obi_stress/20261020/20261021-144512-007587/result.json` | RTL MATCH; TB MATCH |  |
| NN=0 regression | `PASS` / PASS | `artifacts/verification/overlay_nn0/regression/1/20261021-144941-429283/result.json` | RTL NOT_RECORDED; TB NOT_RECORDED |  |
| Frozen FF/PULP=1 regression | `PASS` / PASS | `artifacts/verification/frozen_ff_pulp1/regression/1/20261021-144941-429283/result.json` | RTL NOT_RECORDED; TB NOT_RECORDED |  |
| Original latch smoke | `PASS` / PASS | `artifacts/verification/frozen_orig_latch/smoke/1/20261020-200105-611968/result.json` | RTL MATCH; TB NOT_RECORDED |  |
| Arithmetic primary seed 1 ALU | `PASS` / PASS | `artifacts/verification/overlay_nn1/arith_unit/1/20261021-122602-934820/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic primary seed 42 ALU | `PASS` / PASS | `artifacts/verification/arithmetic/seed42/alu/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic primary seed 20261020 ALU | `PASS` / PASS | `artifacts/verification/arithmetic/seed20261020/alu/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic primary seed 1 DOTP | `PASS` / PASS | `artifacts/verification/overlay_nn1/dotp_unit/1/20261021-122614-531151/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic primary seed 42 DOTP | `PASS` / PASS | `artifacts/verification/arithmetic/seed42/dotp/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic primary seed 20261020 DOTP | `PASS` / PASS | `artifacts/verification/arithmetic/seed20261020/dotp/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic supplement seed 1 ALU | `PASS` / PASS | `artifacts/verification/arithmetic/supplement1/alu/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic supplement seed 42 ALU | `PASS` / PASS | `artifacts/verification/arithmetic/supplement42/alu/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic supplement seed 20261020 ALU | `PASS` / PASS | `artifacts/verification/arithmetic/supplement20261020/alu/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic supplement seed 1 DOTP | `PASS` / PASS | `artifacts/verification/arithmetic/supplement1/dotp/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic supplement seed 42 DOTP | `PASS` / PASS | `artifacts/verification/arithmetic/supplement42/dotp/result.json` | RTL MATCH; TB MATCH |  |
| Arithmetic supplement seed 20261020 DOTP | `PASS` / PASS | `artifacts/verification/arithmetic/supplement20261020/dotp/result.json` | RTL MATCH; TB MATCH |  |
| Quant unit seed 1 | `PASS` / PASS | `artifacts/verification/quant_unit/seed_1/result_sv.json` | RTL MATCH; TB MATCH |  |
| Quant unit seed 42 | `PASS` / PASS | `artifacts/verification/quant_unit/seed_42/result_sv.json` | RTL MATCH; TB MATCH |  |
| Quant unit seed 20261020 | `PASS` / PASS | `artifacts/verification/quant_unit/seed_20261020/result_sv.json` | RTL MATCH; TB MATCH |  |
| LSU unit | `PASS` / PASS | `artifacts/verification/lsu_unit/1/20261021-122747-619216/result.json` | RTL MATCH; TB MATCH | Timestamped structured result required; historical root logs alone are not upgraded to PASS. |
| Controller unit | `PASS` / PASS | `artifacts/verification/controller_unit/1/20261021-122801-224037/result.json` | RTL MATCH; TB MATCH | Timestamped structured result required; historical root logs alone are not upgraded to PASS. |
| 72-encoding decoder directed test | `PASS` / PASS | `artifacts/verification/arithmetic/decoder72/result.json` | RTL MATCH; TB MATCH |  |
| Latest decoder runner | `PASS` / PASS | `artifacts/verification/overlay_nn1/decode/1/20261021-122622-320952/result.json` | RTL MATCH; TB MATCH | Kept separately so an interrupted current runner cannot hide the directed 72-encoding result. |
| Configuration matrix | `PASS` / PASS | `artifacts/verification/arithmetic/parameter_matrix/20261021-122633-558983/result.json` | RTL MATCH; TB MATCH |  |
| Independent RTL review | `PRESENT` / REVIEW_ARTIFACT | `docs/results/independent-review.md` | — |  |

## Visible gaps and non-passing history

- No required index entry is currently missing or non-passing.

## Latest `all` leaf provenance

| Leaf artifact | Result | RTL/TB audit | Current evidence |
|---|---|---|---|
| `artifacts/verification/overlay_nn1/arith_unit/1/20261021-122602-934820` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/dotp_unit/1/20261021-122614-531151` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/decode/1/20261021-122622-320952` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/arithmetic/parameter_matrix/20261021-122633-558983` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/frozen_ff_pulp1/disabled_isa/1/20261021-122745-550386` | PASS | RTL MATCH; TB MISMATCH_OR_MISSING | REPLACED_BY_CURRENT_PASS; replacement `artifacts/verification/frozen_ff_pulp1/disabled_isa/1/20261021-145019-307165` |
| `artifacts/verification/overlay_nn0/disabled_isa/1/20261021-122801-162443` | PASS | RTL MATCH; TB MISMATCH_OR_MISSING | REPLACED_BY_CURRENT_PASS; replacement `artifacts/verification/overlay_nn0/disabled_isa/1/20261021-145020-434377` |
| `artifacts/verification/overlay_nn1/quant_unit/1/20261021-122810-450978` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/smoke/1/20261021-122815-460000` | PASS | RTL MATCH; TB MISMATCH_OR_MISSING | REPLACED_BY_CURRENT_PASS; replacement `artifacts/verification/overlay_nn1/smoke/1/20261021-144941-434282` |
| `artifacts/verification/overlay_nn1/legacy_isa/1/20261021-122826-370680` | PASS | RTL MATCH; TB MISMATCH_OR_MISSING | REPLACED_BY_CURRENT_PASS; replacement `artifacts/verification/overlay_nn1/legacy_isa/1/20261021-145002-380435` |
| `artifacts/verification/overlay_nn1/legacy_misc/1/20261021-122840-188172` | PASS | RTL MATCH; TB MISMATCH_OR_MISSING | REPLACED_BY_CURRENT_PASS; replacement `artifacts/verification/overlay_nn1/legacy_misc/1/20261021-145014-455618` |
| `artifacts/verification/overlay_nn1/arith_isa/1/20261021-122853-616507` | PASS | RTL MATCH; TB MISMATCH_OR_MISSING | REPLACED_BY_CURRENT_PASS; replacement `artifacts/verification/overlay_nn1/arith_isa/1/20261021-145024-578179` |
| `artifacts/verification/overlay_nn1/quant_isa/1/20261021-122904-164852` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/quant_bad_base/1/20261021-122917-922108` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/dependencies/1/20261021-122927-907654` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/wrong_path/1/20261021-122938-020281` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/hwloop/1/20261021-122947-674337` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/obi_stress/1/20261021-123000-699264` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/obi_depth2/1/20261021-123020-360030` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/irq_phase0/1/20261021-123031-638124` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/irq_phase1/1/20261021-123042-752633` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/irq_phase2/1/20261021-123056-053413` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/irq_phase3/1/20261021-123114-108982` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/irq_phase4/1/20261021-123130-535318` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/irq_phase5/1/20261021-123148-338917` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/debug_phase0/1/20261021-123220-009837` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/debug_phase1/1/20261021-123236-432139` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/debug_phase2/1/20261021-123319-071074` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/debug_phase3/1/20261021-123355-795188` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/debug_phase4/1/20261021-123409-935312` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/debug_phase5/1/20261021-123423-619508` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/reset_phase0/1/20261021-123434-315515` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/reset_phase1/1/20261021-123445-961037` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/reset_phase2/1/20261021-123456-963048` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/reset_phase3/1/20261021-123507-488008` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/reset_phase4/1/20261021-123517-735378` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/reset_phase5/1/20261021-123528-515587` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/single_step/1/20261021-123540-455000` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/final_wb/1/20261021-123553-040571` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/negative_env/1/20261021-123606-206420` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/negative_unmapped/1/20261021-123618-431332` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/bench/1/20261021-123631-656097` | PASS | RTL MATCH; TB MATCH | CURRENT |
| `artifacts/verification/overlay_nn1/bench_wait/1/20261021-124002-890552` | PASS | RTL MATCH; TB MATCH | CURRENT |

Historical non-PASS JSON artifacts (not suppressed):

| Artifact | Status | Classification |
|---|---|---|
| `artifacts/verification/arithmetic/parameter_matrix/result.json` | FAIL | FAIL_OR_INCOMPLETE |
| `artifacts/verification/frozen_ff_pulp1/bench/1/20261020-200139-472709/result.json` | FAIL | FAIL_OR_INCOMPLETE |
| `artifacts/verification/frozen_ff_pulp1/isa/1/20261020-154046-173907/result.json` | FAIL | EXPECTED_RED_HISTORICAL |
| `artifacts/verification/frozen_ff_pulp1/smoke/1/20261020-153951-542822/result.json` | UNRUNNABLE | TOOL_FAILURE |
| `artifacts/verification/overlay_nn1/all/1/20261021-121926-828162/result.json` | UNRUNNABLE | TOOL_FAILURE |
| `artifacts/verification/overlay_nn1/arith_unit/1/20261021-121926-829161/result.json` | UNRUNNABLE | TOOL_FAILURE |
| `artifacts/verification/overlay_nn1/bench/1/20261021-111910-795149/result.json` | FAIL | FAIL_OR_INCOMPLETE |
| `artifacts/verification/overlay_nn1/decode/1/20261021-121931-997141/result.json` | UNRUNNABLE | TOOL_FAILURE |
| `artifacts/verification/overlay_nn1/dotp_unit/1/20261021-121929-462274/result.json` | UNRUNNABLE | TOOL_FAILURE |
| `artifacts/verification/overlay_nn1/negative_env/1/20261021-115230-260134/result.json` | FAIL | FAIL_OR_INCOMPLETE |
| `artifacts/verification/overlay_nn1/quant_bad_base/1/20261021-114332-507654/result.json` | FAIL | FAIL_OR_INCOMPLETE |
| `artifacts/verification/overlay_nn1/quant_isa/1/20261020-194526-997153/result.json` | FAIL | FAIL_OR_INCOMPLETE |

## Interpretation

`EXPECTED_RED_HISTORICAL` identifies explicitly named historical negative/red evidence. `TOOL_FAILURE` identifies an unrunnable/tool-policy result. All other non-PASS results remain `FAIL_OR_INCOMPLETE`. The all-suite entry is selected by newest artifact mtime, so rerunning this script after a complete all-suite run refreshes the index without editing the script.
