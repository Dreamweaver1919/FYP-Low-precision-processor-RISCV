# Quantization integration decisions for the Route A implementation plan

Planning notes only, prepared against the active source at `E:/cv32e40p-master/cv32e40p-master/rtl`; no RTL has been changed. The main plan owns the complete encoding table and task ordering. These notes freeze the quantizer's software contract, module interface, LSU ownership, pipeline behavior, and verification requirements.

The implementation target is `COREV_PULP=1`, `FPU=0`, `COREV_CLUSTER=0`, with a new `COREV_XPULPNN=0` parameter by default; enabling it requires `COREV_PULP=1`. Planned implementation paths are the immutable `vendor/cv32e40p/rtl` baseline, modified files in `rtl/core`, and the new `rtl/nn/cv32e40p_nn_quant.sv`. The external core ports remain unchanged. These local choices reproduce the DATE 2020 operation concept; the paper does not establish their binary or memory-layout compatibility with its implementation.

## 1. Frozen architectural contract

`pv.qnt.n rd, rs1, rs2` selects Q=4; `pv.qnt.c` selects Q=2. Both read `rs1` and `rs2`, have no register-C input and no scalar/immediate variants, and produce one integer GPR result. The main encoding table must make all other forms illegal, including when the extension is disabled.

| Item | Exact local definition |
|---|---|
| Activations | `a[0] = signed16(rs1[15:0])`, `a[1] = signed16(rs1[31:16])`. No internal clipping, conversion of 32-bit accumulators, or saturation is implied. Software supplies these int16 values. |
| Source B | `B = unsigned32(rs2)` is the **table base for channel 0**, not the address of its root threshold. |
| Channel bases | `base[0]=B`, `base[1]=B+64`. Each channel occupies exactly 64 bytes for either Q. |
| Threshold storage | `N=(1<<Q)-1` nondecreasing signed int16 values in ascending order, at `base[c]+4*i`, `i=0..N-1`. Each is stored as a sign-extended 32-bit word. Hardware compares `signed16(rdata[15:0])`; the upper half is not checked. Remaining words in the 64-byte block are padding and never read. |
| Base legality | `B[5:0]==0` and `B<=32'hffff_ff80`; the latter prevents wrap when forming the second block and its addresses. `B=0` is legal. Do not silently align/mask a bad B. |
| Equality | Branch right iff `a[c] >= threshold`; equality takes the upper bin. Therefore `rank[c] = count(i: T[c][i] <= a[c])`, in `0..(1<<Q)-1`. This is the frozen local contract, not an exact paper-compatibility claim. |
| Signed quantized value | `signed_value[c] = rank[c] - (1<<(Q-1))`. This gives the signed range -8..7 or -2..1 shown by the paper's staircase concept. |
| Code bits | The Q-bit two's-complement encoding is `code[c] = rank[c] XOR (1<<(Q-1))`. Returning raw rank would give the wrong signed output convention. |
| Result | `rd = code[0] | (code[1]<<Q)`; bits `[31:2*Q]` are zero. Two nibble results occupy one byte; two crumb results occupy four bits. Negative elements are represented within their own Q bits, not sign-extended into halfwords. |
| Memory effects | Exactly `2*Q` successful word reads per valid operation, even for `rd=x0`; no writes. Each channel independently follows its own Q comparisons. No shared-OR traversal and no combined `{threshold1,threshold0}` node format. |

The word representation trades memory for a simpler, explicitly aligned interface: Q=4 needs 60 useful bytes in a 64-byte block; Q=2 uses 12 bytes. It avoids reusing ordinary LSU halfword alignment/sign-extension metadata for interleaved channels. Tight output packing matches the downstream sub-byte SIMD layout and avoids a second halfword-to-sub-byte repack operation. Both choices are local decisions, not facts supplied by the paper.

Sortedness and sign-extended upper halves are software table-generation requirements, not conditions the hardware scans and validates. Duplicated thresholds are permitted and implement empty bins according to the `>=` upper-bin rule. Software must not mutate a table during an operation and must use readable normal data memory. Actual address-map accessibility remains a platform responsibility because the active core has no usable external error reporting.

### Search state and addresses

Initialize each channel independently:

```text
root_index = (1<<(Q-1))-1       // 7 for Q=4, 1 for Q=2
index[c] = root_index
level[c] = 0
rank[c] = 0
pending[c] = 0
finished[c] = 0
```

On the response for channel c at current level l, set `ge = signed16(a[c]) >= signed16(data[15:0])`, append `ge` to its rank, and increment its completed-comparison count. If `l<Q-1`, update its index by `+(1<<(Q-2-l))` for `ge`, or the negative of that step otherwise. The final response marks that channel finished; do not calculate a negative shift or request a child after the last level.

Each address is `{base[c][31:6], index[c][3:0], 2'b00}`. Initial channel-base derivation uses a normal 32-bit addition of 64, after the overflow check. Traversal thereafter changes only the low six bits. The two initial root addresses are `B+28`/`B+92` for Q=4 and `B+4`/`B+68` for Q=2. This explicitly distinguishes table bases, root addresses, and per-node addresses.

## 2. Invalid operands, faults, cancellation, and observable completion

### Bad-base behavior: pre-issue illegal-instruction trap

For this local custom ISA, invalid base alignment or second-block overflow is an illegal operand and raises the existing illegal-instruction exception (`mcause=2`), with `mepc` equal to the qnt instruction PC. There must be no threshold request, GPR write, or qnt retirement count for that instruction. `mtval` remains zero, matching the active CSR implementation. This is a defined local operand constraint; do not label it a standard RISC-V load-misaligned trap.

Check the actual **forwarded** register-B value in ID, not the raw RF value. Add the following local signals in `rtl/core/cv32e40p_id_stage.sv`:

```text
qnt_operand_check_ready_id = ex_ready_i &&
    !(misaligned_stall || jr_stall || load_stall || apu_stall || csr_apu_stall)
qnt_bad_operand_id = qnt_dec_raw && qnt_operand_check_ready_id &&
    ((operand_b_fw_id[5:0] != 0) || (operand_b_fw_id > 32'hffff_ff80))
illegal_insn_id = illegal_insn_dec || qnt_bad_operand_id
```

`qnt_dec_raw` is a new unmasked classification output from the decoder, independent of `deassert_we`, analogous to the existing unmasked `regfile_alu_we_dec_o`. Use the new combined illegal signal at the controller's existing `illegal_insn_i` connection (current ID line 1131) and in the ID `minstret` exclusion (current line 1639). Mask the qnt issue enable and its ALU RF write enable when `qnt_bad_operand_id` is true. Do not feed this signal back through the decoder to create a combinational loop. The readiness predicate must remain independent of `halt_id`/`is_decoding_o`, because those are controller outputs affected by illegality.

The readiness qualification matters: a preceding load may supply an aligned B while the old RF B is misaligned, or the reverse. The current controller can latch illegal state while ID is stalled. Evaluating an unavailable/stale B would therefore create a false trap even if ID had not advanced.

### Available and unavailable fault mechanisms

Source facts:

- `cv32e40p_core.sv:896` ties the LSU external `data_err_i` input to zero; the external core has no corresponding data error input. The active PMP path is disabled and supplies zero at core line 1116.
- `cv32e40p_load_store_unit.sv:492-506` states errors are unsupported and asserts they remain zero. Its OBI `resp_err` is unused.
- The controller's `data_err_i` path was designed for blocked PMP requests, not tagged interleaved qnt responses. `FLUSH_WB` at controller line 1031 even reverses the load/store `exc_cause_o` ternary compared with `csr_cause_o` at line 459. OR-ing qnt response errors into this path is not a valid integration plan.
- ID captures `pc_ex_o` for branches and ordinary `data_req_id` operations at lines 1594-1595. A qnt has `data_req_id=0`, so retain its own PC in the qnt EX packet rather than assuming this old conditional capture covers it. CSR exception-PC selection can use ID or EX, but `mtval` reads zero (`cv32e40p_cs_registers.sv:346/516`).

Therefore response bus-error injection and architectural memory access-fault tests are **N/A for this top-level configuration**, not claimed passes. This plan adds no external error port, bus timeout, PMP implementation, error interrupt, or general LSU fault repair. An unmapped address that never responds stalls indefinitely as an ordinary load can. Protocol violations such as an unsolicited/out-of-order response are verification assertion failures; they are not invented software exceptions. Any later requirement for precise external memory faults is a separate interface/exception project.

### Issue, memory start, completion, retirement, and cancellation

Use these distinct events:

1. **ID issue:** the actual legal qnt packet crosses ID to EX on `id_valid_o && is_decoding_o && instr_valid_i && qnt_issue_enable`; capture operands, precision, `rd`, and PC once. This begins pipeline blocking, including any wait for old LSU traffic to drain. An unmasked decode of a stale IF/ID instruction word is never an issue event.
2. **Quantizer start:** `start_valid_i && start_ready_o`, coupled atomically with the LSU ownership-acquire handshake. The quantizer initializes both searches and captures its operand payload once. Holding a qnt enable high is not a second start.
3. **Memory acceptance:** `mem_req_valid_o && mem_req_ready_i`. Only this event creates a pending threshold response and enqueues its tag. A request remains stable until this event.
4. **Successful completion:** `done_valid_o && done_ready_i`; this is the sole EX completion/forwarding/write event for the instruction. `rd=x0` still completes but suppresses the physical RF write. The LSU ownership release occurs on the same event only with no remaining requests/responses.
5. **Counter accounting:** retain this core's existing ID-based `minstret` convention, counting a valid qnt once at ID issue, excluding combined illegal instructions. Do not add another count at completion. This is defensible here because valid issued qnt operations cannot subsequently trap or be canceled in this configuration, and a younger counter-read CSR cannot pass the blocked EX. The event is technically issue-time accounting, as the existing ID comment says, not a new globally precise retirement mechanism.

Cancellation before ID issue follows normal older-branch/flush/exception behavior: no qnt start or memory effect occurs. Once legally issued, qnt is noninterruptible until successful completion, including the drain phase; an asynchronous debug or interrupt request does not abort/replay it. Younger traps, ebreak, mret, WFI, hardware-loop changes, and fetch failures cannot overtake it. Reset cancels all qnt state, ownership, FIFO tags, and writeback; this requires the existing system-level reset contract that also removes old bus responses. Core-only reset with independently surviving responses is not supported by the current LSU and is not added here.

## 3. Quantizer module signature and internal state

The new compute module is `rtl/nn/cv32e40p_nn_quant.sv`. EX retains destination/PC metadata; the compute module does not own the RF or controller.

```systemverilog
module cv32e40p_nn_quant (
  input  logic        clk_i,
  input  logic        rst_ni,

  input  logic        start_valid_i,
  output logic        start_ready_o,
  input  logic [31:0] start_activations_i,
  input  logic [31:0] start_table_base_i,
  input  logic        start_q4_i,       // 1: Q=4; 0: Q=2

  output logic        active_o,
  output logic        done_valid_o,
  input  logic        done_ready_i,
  output logic [31:0] done_result_o,

  output logic        mem_req_valid_o,
  input  logic        mem_req_ready_i,
  output logic [31:0] mem_req_addr_o,
  output logic [ 3:0] mem_req_tag_o,
  input  logic        mem_rsp_valid_i,
  input  logic [31:0] mem_rsp_data_i,
  input  logic [ 3:0] mem_rsp_tag_i,
  output logic        mem_idle_o
);
```

There is deliberately no cancel or error input: neither is an accepted in-flight event in this frozen core contract. Reset is the abort mechanism. A valid start is already base-validated in ID; assert that contract at the unit boundary as well.

The module needs:

- Global `IDLE`, `RUN`, and `RESULT` states; captured Q/base/activations and a 1-bit operation epoch toggled on each start.
- Per channel: its signed16 activation, 32-bit aligned block base, 4-bit index, 3-bit completed-level count (must represent 4), 4-bit accumulated rank, pending flag, finished flag. Two comparator regions receive isolated operands when their channel is inactive.
- A fall-through round-robin request selector with a parked descriptor `{valid, address[31:0], tag[3:0]}` used only when a presented request is not accepted. Once presented, hold valid/address/tag until accepted. Do not replace a stalled descriptor when an unrelated response arrives. Do not always register a freshly selected request before presenting it; that would add a dependent-read bubble.
- Tag `[3:0] = {epoch, channel, level[1:0]}`. Each channel has at most one accepted outstanding request; level in a tag is the requested comparison level, 0..Q-1. No epoch may be reused while a response from an earlier operation can exist. Release/drain rules make the 1-bit epoch sufficient; it is a consistency check, not a way to recover from stray bus responses.
- A 32-bit saved result and valid bit for completion backpressure. At the terminal response, form the candidate result from the new rank for the responding channel plus the already finished other channel. `done_valid_o` may fall through combinationally from this terminal response; if not accepted immediately, store the result and hold `done_valid_o` and result stable until acceptance.

`start_ready_o` is true only in IDLE; no same-edge RESULT-to-new-start bypass is required. Always initialize state on a start handshake, including both levels/ranks/pending/finished flags and request selection; do not require a low enable cycle between instructions. `mem_idle_o` means no parked request and neither channel pending. `active_o` covers RUN/RESULT only; the controller must use the EX packet valid to cover the earlier drain phase too.

All `mem_rsp_valid_i` pulses are consumed regardless of a global FSM request phase. Decode the tag, assert matching epoch/expected level/pending channel, and update that channel only. A response cannot wait for a special fetch state. Simultaneous request acceptance for one channel and a response for the other is legal and must update both pieces of state on the same edge.

## 4. Reuse the LSU through an exclusive transaction sideport

### Chosen boundary

Add a qnt sideport inside `rtl/core/cv32e40p_load_store_unit.sv`, immediately before the existing `cv32e40p_obi_interface` instantiation. It reuses the LSU's one external data bus and its existing OBI adapter. It does **not** drive ordinary `data_req_ex_i` for each threshold and does **not** route qnt responses through ordinary load WB metadata.

Add these LSU ports (exact names/types):

```systemverilog
input  logic        qnt_acquire_i,
output logic        qnt_acquire_ready_o,
input  logic        normal_wb_pending_i,
output logic        qnt_owned_o,
input  logic        qnt_release_i,
input  logic        qnt_req_valid_i,
output logic        qnt_req_ready_o,
input  logic [31:0] qnt_req_addr_i,
input  logic [ 3:0] qnt_req_tag_i,
output logic        qnt_rsp_valid_o,
output logic [31:0] qnt_rsp_data_o,
output logic [ 3:0] qnt_rsp_tag_o
```

The core connects these ports to the EX/quantizer handshake. EX supplies a new `normal_lsu_wb_pending_o` from its existing `regfile_we_lsu` state for `normal_wb_pending_i`; with FPU=0 there is no additional APU completion to drain. Disabled-extension generation ties qnt request/acquire/release inputs low and does not instantiate the compute module.

### Acquisition and old-load drain

Add registered LSU owner `NORMAL`/`QNT`. In NORMAL:

```text
qnt_acquire_ready_o = (normal cnt_q == 0) && !normal_trans_valid &&
                     !normal_wb_pending_i
```

No normal request may be admitted on an acquisition edge. The EX qnt packet blocks younger instructions while waiting, but ordinary old load/store responses continue through their original route and retain their original destinations. Use both outstanding-count/valid and WB emptiness, not `lsu_ready_wb_o` alone: the latter is true during a returning response and does not mean the old load has already left WB. Misaligned old transfers must finish all beats before ownership changes.

Couple starts exactly:

```text
quant.start_valid = qnt_valid_ex && !qnt_started_ex && lsu.qnt_acquire_ready
lsu.qnt_acquire   = qnt_valid_ex && !qnt_started_ex && quant.start_ready
start_fire       = quant.start_valid && quant.start_ready
```

The same `start_fire` sets owner=QNT and `qnt_started_ex=1`; the first qnt memory request occurs after this edge. This prevents a source being captured without ownership or ownership being taken without a new operation.

### Requests and responses while owned

- In QNT, select qnt address and force read controls: `we=0`, `be=4'b1111`, `wdata=0`, `atop=0`. The existing adapter is instantiated with `TRANS_STABLE=1` (LSU lines 455-456), so its transaction acceptance is the actual `data_req_o && data_gnt_i`; there is no earlier skid-buffer acceptance to confuse with grant.
- Add a separate two-entry tag FIFO and qnt outstanding count. Enqueue the 4-bit request tag only on request acceptance; return/dequeue its oldest tag on each OBI response. The active interface has no external transaction IDs, so responses must be in order. A response may coincide with a different request's grant; pop the old head and push the new tail independently.
- `qnt_req_ready_o = qnt_owned_o && (qnt_count<2) && trans_ready`; external OBI grant without a presented qnt request is not a qnt acceptance. Hold the descriptor stable under backpressure; suppress a new request once that channel is pending.
- Gate ordinary LSU `count_up`, `count_down`, `ctrl_update`, rdata/alignment capture, and normal response-valid with owner NORMAL. Qnt responses must not decrement normal `cnt_q`, overwrite old load data, update `data_type_q`, or drive an ordinary load GPR write.
- Preserve the existing normal-load/store behavior exactly in NORMAL, including `PULP_OBI`. The qnt sideport can use the normal OBI two-outstanding capability, independent of the ordinary-load `PULP_OBI` policy, because it has its own explicit pending/tag state.
- Ordinary EX/WB LSU readiness remains true while their path is empty in QNT; qnt has its own EX completion condition. Extend LSU `busy_o` to include owner QNT, qnt outstanding/presented requests, and ownership acquisition so clock/sleep gating cannot stop it.
- Define qnt response as raw OBI `rvalid && owner==QNT`, data raw OBI rdata, tag FIFO head. It has no ready input; the quantizer always consumes it. Assert nonempty FIFO on every response. The current LSU explicitly assumes responses are at least one cycle after the granted request (LSU lines 353-359); zero-cycle responses are outside this interface contract.

Release only on `done_fire`, with the last response included in the next-state emptiness calculation: no parked request, qnt count after simultaneous pop/push zero, both channel searches finished. If final completion is backpressured, retain ownership through RESULT even though no memory traffic remains. There is no NORMAL/qnt mixing on the external response channel, and no later instruction can receive a stale qnt response.

### Alternatives and why they are not selected

Passing threshold requests through the current ordinary EX load interface reuses its count and alignment logic, but its `ctrl_update`, single WB type/offset metadata, and `lsu_ready_ex_o` assume ordinary pipeline advancement. Holding `data_req_ex_i` high while stalled can issue duplicates. Fixing this by serializing reads is possible, but loses deliberate two-channel interleaving and adds cycles. Reworking all ordinary load metadata would enlarge regression scope.

A separate direct-bus qnt master after the LSU can also be correct with strict drain/ownership, but needs another arbitration/response-routing wrapper and duplicates controls already adjacent to the OBI adapter. It creates a second place to reason about normal LSU grant/response accounting. Use the internal exclusive sideport instead; do not silently add a second external bus.

## 5. Exact decoder, ID, EX, core, and controller integration work

| Planned file | Required changes |
|---|---|
| `rtl/core/cv32e40p_decoder.sv` | Gate the local qnt encodings with `COREV_XPULPNN && COREV_PULP`; produce raw `qnt_dec_o` and `qnt_q4_o`; mark A/B used and C unused; choose integer `rd`; set ordinary memory request/write enables, ALU operation enable, MUL/APU/CSR controls to zero. Mark ALU result destination/write intent for the final qnt result, with no memory-port destination. Add an issue-qualified qnt enable mask alongside existing `deassert_we_i` output masks, not a permanently high raw enable. |
| `rtl/core/cv32e40p_id_stage.sv` | Add raw qnt decode/precision wires, forwarded-B validation and combined illegal signal described above. Capture a dedicated qnt EX packet `{valid, q4, activations[31:0], table_base[31:0], rd[4:0], pc[31:0]}` under actual legal `id_valid_o` acceptance, using forwarded A/B without `.sc` replication. Do not capture qnt mode under `alu_en` (qnt sets that enable zero). Clear qnt packet valid on reset and on the ordinary EX-ready bubble path; preserve it while EX stalls. Connect the controller's new qnt-block input. Use combined illegality in `minstret`, count qnt once at ID issue, and do not add a completion counter pulse. |
| `rtl/core/cv32e40p_ex_stage.sv` | Instantiate `cv32e40p_nn_quant` under the extension parameter, add a `qnt_started_ex` flag, connect start/ownership handshakes, and expose normal LSU WB pending. Hold all qnt packet metadata until done. Add qnt to instruction-class `ex_valid_o` only on `done_fire`; use the qnt-specific ready condition so `alu_en=0` cannot prevent completion and ordinary LSU-ready cannot complete it early. Add final qnt result to the ALU write/forward mux; qualify **both** functional and power write enables with `done_fire && rd!=0`. Suppress ordinary ALU/MUL/CSR result selection and memory-port GPR write metadata for qnt. While busy, no old result is forwarded as valid. Do not reuse `mult_multicycle`'s register-C feedback. |
| `rtl/core/cv32e40p_core.sv` | Add and connect qnt packet/control/sideport wires and parameter propagation. Keep all old external ports. Feed qnt blocking from the EX packet valid, including pre-start drain. Connect `normal_lsu_wb_pending_o` to LSU. Preserve normal ID/EX/LSU signals for non-qnt instructions. Ensure sleep/clock busy includes qnt. |
| `rtl/core/cv32e40p_controller.sv` | Add `input logic qnt_block_i`. In DECODE/DECODE_HWLOOP, while this is true, halt IF/ID and set `is_decoding_o=0` before evaluating younger instruction/IRQ/debug/trap branches. Keep controller state rather than entering DBG_FLUSH, FLUSH_EX, WFI, IRQ entry or a hardware-loop update. Also hold DBG_FLUSH while qnt is blocked, as described below for same-edge single-step entry. Retain the EX qnt packet rather than clearing it. The existing `debug_req_q` latch must continue to capture debug requests. Release the guard only after the completion edge; existing debug/IRQ priority then applies to the next instruction boundary. |
| `rtl/core/cv32e40p_load_store_unit.sv` | Implement the exclusive sideport, owner, 2-entry tag FIFO and response routing described in section 4. Preserve ordinary ready equations in NORMAL and do not reuse their WB metadata for qnt. |

`ex_ready_o=1` on qnt completion may permit the ordinary bubble-clearing branch to clear the EX qnt packet on the completion edge; `halt_id=1` while `qnt_block_i` prevents a younger instruction from also entering EX on that edge. The next ID issue occurs after the packet is cleared. Back-to-back qnt instructions therefore work through fresh handshakes without an artificial requirement for an enable-low cycle; service-start spacing also includes the defined pipeline boundary/admission cycles.

The qnt destination remains visible to existing source hazard comparisons. During busy cycles the controller blocks younger issue; on completion the final ALU forwarding result is valid and the GPR write occurs once. Verify consumers on A/B/C, overlapping `rd==rs1`/`rd==rs2`, and a preceding producer on either source. Do not solve this by unconditionally clearing the destination intent while busy and losing dependency information.

Interrupt inputs are level triggered in `cv32e40p_int_controller.sv`; `irq_q` tracks the inputs each cycle. Hold `irq_ack_o=0` while qnt is blocked and service a still-asserted eligible level after completion. Do not promise sticky capture of a pulse the baseline contract does not support. Asynchronous debug requests are latched by the existing controller `debug_req_q`; service them after completion.

Single-step needs a second explicit controller guard. Existing DECODE/DECODE_HWLOOP logic enters DBG_FLUSH on the same edge that an ordinary instruction issues (controller lines 664-701 and 850-887), before the qnt EX valid is registered. Therefore merely guarding DECODE once qnt is active is insufficient. In DBG_FLUSH, if `qnt_block_i` is true, hold DBG_FLUSH with IF/ID halted, no PC redirect/CSR save/debug entry, and let the qnt EX packet complete. After completion, the existing DBG_FLUSH-to-DBG_TAKEN_IF route records the next instruction PC. Amend the current `a_dbg_flush` assertion (line 1606) so a DBG_FLUSH self-loop is permitted **only while qnt_block_i is true**. This avoids a new step-pending state/input and ensures exactly one qnt completes before debug entry. A trigger/ebreak on a younger instruction takes effect only at that later boundary. qnt executed while already in debug follows the same complete-before-next-instruction rule.

## 6. Cycle objective and its assumptions

The 9-/5-cycle objective applies to **unit start to successful EX completion**, with an already drained LSU, immediate grants, exactly one-cycle grant-to-response latency, in-order responses, a new grant and old response permitted together, and `done_ready_i=1` for the final response. The first request is presented during the cycle following the start edge. No extra threshold register is inserted before comparison: valid response data is compared and channel state is updated at the response edge; address generation uses that registered state in the next cycle. This separates comparison from next-address generation across a register.

For Q=4, with start at E0:

| Edge | Granted request | Returned/compared threshold |
|---|---|---|
| E1 | channel 0, level 0 | none |
| E2 | channel 1, level 0 | channel 0, level 0 |
| E3 | channel 0, level 1 | channel 1, level 0 |
| E4 | channel 1, level 1 | channel 0, level 1 |
| E5 | channel 0, level 2 | channel 1, level 1 |
| E6 | channel 1, level 2 | channel 0, level 2 |
| E7 | channel 0, level 3 | channel 1, level 2 |
| E8 | channel 1, level 3 | channel 0, level 3 |
| E9 | none | channel 1, level 3; fall-through final completion |

Q=2 stops after grants E1..E4 and final response/completion E5. A parked request selector must allow a newly updated eligible channel to be presented in the cycle immediately after its response edge; do not add a descriptor-fill bubble every time.

The final response-to-compare-to-packed-RF-write path must meet timing. The ready/valid fall-through plus saved-result fallback gives a concrete way to meet 9/5 without losing a final pulse if completion is blocked. If FPGA timing requires registering that final completion, report **10/6 service cycles**. If a separate threshold-capture stage is added before comparison, the alternating schedule must be redrawn and its additional dependent-read bubbles measured; it cannot still be called 9/5. Example: with otherwise identical scheduling and a response-to-next-request separation of three instead of two edges, Q=4 requires grants E1,E2,E4,E5,E7,E8,E10,E11, final response capture E12, and final comparison/fall-through RF completion E13: **13 service cycles**, or 14 if completion is separately registered too. Q=2 similarly has grants E1,E2,E4,E5, final response E6, final comparison/completion E7 (8 if separately registered).

Report (a) LSU-drain/admission cycles, (b) service cycles, (c) final completion backpressure, and (d) full core instruction/kernel cycles separately. Memory delays can overlap between channels, so do not claim that every grant/response stall adds a simple fixed number to total latency. The architecture remains correct with arbitrary finite grant/response stalls but does not promise bounded interrupt/debug latency if memory never responds.

## 7. Named tests, concrete data, and expected outcomes

These are future implementation tests, not passing-test claims. Put the unit, LSU-adapter, and core integration tests in the main plan's verification tree. The scalar oracle must use an independent linear count of `T<=a`, not the RTL tree traversal; this prevents reproducing an indexing error in both DUT and oracle.

| Test | Data and required result |
|---|---|
| `qnt_q2_opposite_branches` | Both tables `[-10,0,10]`; activations `(-5,15)` (`rs1=32'h000f_fffb`); B=`0x1000`. Channel ranks `(1,3)`, signed values `(-1,1)`, codes `(3,1)`, `rd=0x00000007`. Ideal request addresses in order `1004,1044,1000,1048` hex. Four accepted reads and one completion. This is the shared-node-OR counterexample. |
| `qnt_q4_opposite_branches` | Both tables `[-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70]`; activations `(-5,15)`; B=`0x1000`. Ranks `(7,9)`, signed `(-1,1)`, result `0x1f`. Ideal request addresses `101c,105c,100c,106c,1014,1064,1018,1060` hex. Eight accepted reads. |
| `qnt_q2_equalities` | T=`[-10,0,10]`, activations `(0,10)`; ranks `(2,3)`, codes `(0,1)`, result `0x4`. Equality increments the bin at that threshold. |
| `qnt_q4_equalities` | The Q4 table above, activations `(0,10)`; ranks `(8,9)`, codes `(0,1)`, result `0x10`. |
| `qnt_signed_extrema` | Q2 table above, activations `(-32768,32767)` => `0x6`; Q4 table above and same activations => `0x78`. Every comparison uses signed16, including negative threshold words such as `fffffff6`. |
| `qnt_duplicate_thresholds` | Q2 T=`[-10,-10,10]`, activations `(-10,-9)` => ranks `(2,2)`, codes `(0,0)`, result `0x0`. Equality skips all duplicate-threshold empty bins. |
| `qnt_independent_channel_tables` | Q2 channel0 T=`[-10,0,10]`, channel1 T=`[100,200,300]`; activations `(15,150)` => codes `(1,3)`, result `0xd`. Verify the fixed 64-byte second base and independent addresses. |
| `qnt_all_bin_edges` | For each Q and channel table above, sweep every threshold at `t-1,t,t+1`, clipped to int16, and both int16 extrema against the linear oracle. Include every possible rank, opposite directions, and unequal channel tables. |
| `qnt_random_tables` | Seeded nondecreasing signed16 tables including duplicates, random signed16 activation pairs, Q alternating each operation. Result equals the linear oracle; upper bits above `2*Q` remain zero. |
| `qnt_precision_capture` | Execute Q4 then Q2 then Q4 with no intervening ALU operation, also after unrelated SIMD mode settings; expect their correct 8/4/8 read counts and the above packed results. Detect mode capture erroneously gated by `alu_en`. |
| `qnt_back_to_back` | Two distinct qnt instructions with enable potentially continuously high; first example result `7`, second unequal-table result `d`; exactly two starts/completions, all search state freshly initialized, and no reuse of the first result. |
| `qnt_x0_memory_effects` | Run both canonical examples with `rd=x0`. Exactly 4/8 threshold reads, one successful completion and one ID count, zero physical RF writes; memory requests cannot be optimized away. |
| `qnt_forward_and_alias` | Preceding ALU/load produces rs1 or B; `rd==rs1`, `rd==rs2`, and dependent following ADD, SIMD or accumulating-dot source A/B/C. Canonical Q2 result is `7`, so `addi consumer,rd,1` yields `8`; no intermediate result is forwarded/written. |
| `qnt_old_load_drain` | An older `lw x9` returns `12345678` hex after a 7-cycle response delay, followed by canonical qnt writing x9. Observe the old load write once, then final x9=`7` once. No qnt grant before old count, request valid, and WB pending are all clear. Also test old load destination differs from qnt and remains `12345678`. |
| `qnt_old_store_and_misaligned_drain` | Older store held without grant for 3 cycles, with response delayed further, then qnt: store occurs once before qnt ownership. Repeat with an old misaligned load that uses two beats; qnt cannot consume either beat as a threshold. |
| `qnt_bad_base_alignment` | Actual B=`0x1004` and `0x1020`: illegal-operand trap2, `mepc=qnt PC`, `mtval=0`, no threshold request, GPR unchanged, qnt not counted. B=`0x1000` remains legal. |
| `qnt_bad_base_overflow` | B=`0xffffffc0`: trap2 with no request. Unit/adapter synthetic-memory test at B=`0xffffff80` is valid and uses Q2 addresses `ffffff84,ffffffc4,ffffff80,ffffffc8`; no wrap. B=0 must also be accepted when TB maps it. |
| `qnt_bad_base_after_load` | Case A: old RF B=`0x1004`, a preceding load returns valid B=`0x1000` after delay: no early trap and final result `7`. Case B: old RF B=`0x1000`, load returns `0x1004`: trap2 at qnt PC, no threshold reads. Check across the entire load stall, not only the eventual issue edge. |
| `qnt_request_backpressure` | Delay root grant 3 cycles and later-node grants by different lengths. Request/address/tag/control remain stable until grant; counts advance only on acceptance; exactly 2Q requests, correct final result. |
| `qnt_response_every_phase` | Return one-cycle rvalid pulses during cycles where the other channel's request is stalled, while selecting a new request, and while one channel has finished. No pulse lost. Give each response distinct data to detect wrong-tag routing. |
| `qnt_simultaneous_grant_response` | In-order one-cycle memory: grant the next channel while responding to the previous one on E2..E8. FIFO count/pointers, channel pending bits and levels all remain correct; qnt count never exceeds2. |
| `qnt_unequal_latency` | In-order replies with 1,4,2,7-cycle gaps, delayed grants, and both outstanding slots exercised; canonical packed result unchanged. No response-order-independent claim: OBI has no response IDs. |
| `qnt_final_backpressure` | Hold `done_ready=0` for 4 cycles at the final pulse. Save final result (`7`/`1f`), assert stable done_valid/data, retain ownership, issue no new request/start, and complete once when ready rises. |
| `qnt_irq_deferred` | Assert an enabled level IRQ during WAIT_DRAIN and at each comparison level; hold it to ack. No IRQ ack/PC redirect before completion; qnt RF result correct once; then service at next instruction PC. Pulse-only IRQ behavior remains baseline level-triggered behavior. |
| `qnt_debug_and_single_step` | Pulse debug_req during each phase and ensure its existing latch retains it until completion; then enter debug at next instruction boundary. With single-step, one complete qnt executes and no younger instruction changes state before debug entry. Include a younger ebreak and instruction trigger. |
| `qnt_reset_each_phase` | Apply system reset during WAIT_DRAIN, grant wait, response wait and RESULT. No result write after reset; owner/count/FIFO/pending/valid clear. The reset memory model must discard earlier requests/responses. |
| `qnt_no_speculative_effect` | A taken older branch, an older exception, or disabled/illegal qnt encoding prevents ID issue: no start, no ownership and no threshold read. |
| `qnt_ideal_latency` | Under precisely section6 memory assumptions assert start-to-done 9(Q4)/5(Q2), and record first/last request, last response and RF-write edges. If final completion is deliberately registered, expected measured adaptation is10/6 and the report must state that. |
| `qnt_baseline_regression` | With extension disabled, full baseline decode/LSU tests retain existing results and qnt encodings trap. With it enabled, ordinary aligned/misaligned loads/stores, postincrement, 8/16-bit SIMD, MUL/MULH, interrupts, debug and counters preserve baseline behavior. |

Assertions to accompany the tests: no qnt request without ownership; no mixed normal/qnt response owner; no pop on an empty FIFO; no request from a pending/finished channel; response epoch/level/channel match; `qnt_count<=2`; request stable while unaccepted; only one completion per start; no RF write/valid forwarding before completion; no ordinary LSU WB from qnt responses; release implies empty next-state traffic; and no younger architectural update while the EX qnt packet is valid. Assert protocol minimum response latency; do not present a zero-latency negative protocol test as an architectural corner case.

## 8. Self-review / execution boundary

The main implementation tasks should separate (1) software oracle/table helpers and contract tests, (2) quantizer compute/state tests, (3) exclusive LSU adapter tests, and (4) whole-core issue/forwarding/interrupt/debug/counter integration. Each task first demonstrates the specified failure against the baseline, then adds only the implementation needed for its tests, runs the named tests, and runs baseline regressions for touched behavior. Keep concrete simulation commands in the main plan after its toolchain preflight; these notes do not claim an installed simulator or fabricate a working command.

Review the full plan against the facts in `docs/investigation/paper-analysis.md` and `docs/investigation/core-audit.md`: Q comparisons per independent channel, signed-value mapping, fixed second-channel stride, LSU stable-request/in-order/minimum-latency assumptions, disabled bus errors, actual PC capture, ID-based counter accounting, and delayed IRQ/debug behavior are all explicit here. No product RTL, software scaffolding, source copy, simulator installation, or synthesis run is authorized by this notes-only subtask.
