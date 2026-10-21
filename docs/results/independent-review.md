# Independent RTL review — XPulpNN Route A

Reviewed 2026-10-21, read-only, against the approved design specification and implementation plan:

- `docs/superpowers/specs/2026-10-20-xpulpnn-cv32e40p-design.md`
- `docs/superpowers/plans/2026-10-20-xpulpnn-cv32e40p.md`

Scope: overlay RTL in `rtl/core` and `rtl/nn`, with emphasis on decoder legality, ID/EX forwarding and exact exceptions, qnt/LSU ownership and final writeback, controller IRQ/debug behavior, and the tests that claim to cover those paths.  No production RTL was modified by this review.

## Result

No independently reproducible functional RTL defect was found in the inspected Route-A datapath and qnt ownership protocol.  In particular, the following static properties agree with the specification:

- the decoder restricts the local custom-3 forms by funct6, bit 25, funct3, and the abs `rs2==0` condition (`rtl/core/cv32e40p_decoder.sv:2165-2240`);
- 4/2-bit ALU and dotp blocks are isolated behind the new modes and dotp uses a signed, balanced reduction tree (`rtl/nn/cv32e40p_nn_alu.sv`, `rtl/nn/cv32e40p_nn_dotp.sv`);
- qnt preserves two independent channel contexts, holds request address/tag before grant, consumes responses by tag, and preserves its terminal value under `done_ready_i` backpressure (`rtl/nn/cv32e40p_nn_quant.sv:72-182`);
- the LSU keeps threshold tags in a separate depth-two FIFO and suppresses normal response/counter paths while qnt owns the OBI channel (`rtl/core/cv32e40p_load_store_unit.sv:110-153,521-545`);
- EX exposes a write/forward only on `qnt_done_valid && qnt_done_ready`, while x0 still executes the qnt transaction (`rtl/core/cv32e40p_ex_stage.sv:200-210,253-286,536-541`).

The standalone quantizer reports PASS for seeds 1, 42, and 20261020 (2,000 random cases per Q) in `artifacts/verification/quant_unit/*/result_sv.json`.  The Python model suite also passed during this review (17 tests).

## Actionable acceptance gaps

### Resolved P1 — release-suite coverage is now composed into `all`

The earlier review found that `all` omitted disabled-ISA and parameter-matrix coverage.  This is now fixed: `verification/scripts/run_tests.py:109-120` invokes the parameter matrix and both frozen/overlay disabled-ISA cases from `all`.

The final index retains the structured all-suite result and its leaf-level source-hash provenance, including explicit current-hash replacements where required; this finding no longer blocks suite composition.

### Resolved P1 — real-core single-step/DBG_FLUSH and final-writeback tests are now runnable

The earlier review found that the runner did not select its existing single-step or phase-4/5 support.  It now creates phases 0–5 plus `single_step` and `final_wb` (`verification/scripts/run_tests.py:116-120,161-169`).  Real-core evidence is present: `artifacts/verification/overlay_nn1/single_step/1/20261021-121418-229678/result.json` passed with one qnt commit and nine DBG_FLUSH cycles, and `.../final_wb/1/20261021-121408-029884/result.json` passed with six blocked writeback cycles and one commit.

The final all-suite group run and its recursively audited leaf evidence are preserved in `artifacts/verification/summary.json`; the runner defect is resolved.

### Resolved P2 — final validation record and release evidence are complete

`README-xpulpnn.md` names `docs/results/xpulpnn-route-a-validation.md` as the final functional, cycle, and FPGA evidence record.  It is now complete and agrees with `artifacts/delivery/release-evidence.json`: functional status PASS; the latest `all` artifact (`artifacts/verification/overlay_nn1/all/1/20261021-122602-933820/result.json`) is PASS with 19 top-level groups and 42 recursively audited leaves; and the verification index reports release-current PASS.

Six historical `all` leaves retain their original paths and TB hash mismatches rather than being rewritten.  Each explicitly cites a later current-hash PASS rerun of the same config/suite/seed: frozen disabled ISA, NN-off disabled ISA, NN-on smoke, legacy ISA, legacy misc, and arithmetic ISA.  The three current OBI stress seeds (1, 42, 20261020) all have matching RTL and actual core-TB hashes.  This resolves the provenance gap without concealing the old evidence.

The eight routed OOC records have also been checked: both core and system configurations meet 20 ns, while the two NN-enabled 10 ns runs remain visible as timing failures.  The two final system-wrapper BRAM runs use identical IMEM/DMEM hashes and equal deterministic output digest (356 output words); their total-program cycles are correctly not used as an acceleration ratio.

## Evidence limitations to retain

- The unit qnt campaign has strong randomized handshake coverage, but it is not a core-execution proof by itself.
- The 1/42/20261020 OBI stress matrix is now explicitly archived with current RTL/TB hashes.  The more specialized qnt/IRQ/debug/reset programs remain directed seed-1 scenarios; their coverage is not equivalent to a randomized three-seed campaign for every interrupt/debug timing combination.
- FPGA evidence must be read from its matching routed reports and source snapshot.  The 20 ns OOC results do not establish board pins, board-clock hookup, bitstream programming, hardware execution, or power.
- Performance ratios remain measurements of the local unpacking-heavy dot8 baseline and matched kernel intervals.  They are not a claim of the DATE-paper optimized baseline or a board-measured speedup.

