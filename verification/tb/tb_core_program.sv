`timescale 1ns/1ps
module tb_core_program #(
  parameter int NN_ENABLE=0,
  parameter int GRANT_MAX=0,
  parameter int RESPONSE_MAX=1,
  parameter int SEED=1,
  parameter int EVENT_MODE=0,
  parameter int EVENT_PHASE=0,
  parameter bit NEGATIVE_ENV=0,
  parameter int DATA_DEPTH=1,
  parameter bit FINAL_WB_HOLD=0,
  parameter bit FIXED_WAIT=0,
  parameter int MAX_CYCLES=200000
);
  logic clk=0, rst_n=0, fetch=0;
  always #5 clk=~clk;
  logic ireq,ignt,irvalid,dreq,dgnt,drvalid,dwe;
  logic [31:0] ia,ird,da,dwd,drd;
  logic [3:0] dbe;
  logic [31:0] status,sigbase,sigwords;
  logic ifail,dfail;
  int iaccepted,iresponded,daccepted,dresponded;
  int cycles=0, fd, js, settle=0;
  logic irq_ack, havereset,running,halted,sleeping;
  logic [4:0] irq_id;
  logic [31:0] irq=0;
  logic debug_req=0, event_fired=0, reset_requested=0;
  int qnt_responses=0,qnt_commits=0,event_acknowledgments=0,reset_count=0;
  logic monitor_fail=0;
  int qnt_issues=0,qnt_retire_events=0,wb_hold_cycles=0,qnt_outstanding=0,max_qnt_outstanding=0;
  int trace_fd,op_responses=0,op_grants=0,step_flush_cycles=0;
  logic qnt_issue_d=0,halted_d=0,await_next_issue=0;
  initial trace_fd=$fopen("qnt_trace.jsonl","w");

  initial begin repeat(10) @(negedge clk); rst_n=1; repeat(2) @(negedge clk); fetch=1; end
  initial begin
    wait(reset_requested);
    @(negedge clk);fetch=0;rst_n=0;reset_count=reset_count+1;
    repeat(5) @(negedge clk);rst_n=1;
    repeat(2) @(negedge clk);fetch=1;
  end
  cv32e40p_top #(
    .COREV_PULP(1),.COREV_CLUSTER(0),.FPU(0),.ZFINX(0)
`ifdef FYP_OVERLAY
    ,.COREV_XPULPNN(NN_ENABLE)
`endif
  ) dut (
    .clk_i(clk),.rst_ni(rst_n),.pulp_clock_en_i(1'b1),.scan_cg_en_i(1'b0),
    .boot_addr_i(32'h200),.mtvec_addr_i(32'h100),.dm_halt_addr_i(32'h400),
    .dm_exception_addr_i(32'h480),.hart_id_i(32'b0),
    .instr_req_o(ireq),.instr_gnt_i(ignt),.instr_rvalid_i(irvalid),.instr_addr_o(ia),.instr_rdata_i(ird),
    .data_req_o(dreq),.data_gnt_i(dgnt),.data_rvalid_i(drvalid),.data_we_o(dwe),
    .data_be_o(dbe),.data_addr_o(da),.data_wdata_o(dwd),.data_rdata_i(drd),
    .irq_i(irq),.irq_ack_o(irq_ack),.irq_id_o(irq_id),.debug_req_i(debug_req),
    .debug_havereset_o(havereset),.debug_running_o(running),.debug_halted_o(halted),
    .fetch_enable_i(fetch),.core_sleep_o(sleeping)
  );
  obi_memory_agent #(.INSTRUCTION(1),.GRANT_MAX(GRANT_MAX),.RESPONSE_MAX(RESPONSE_MAX),.FIXED_WAIT(FIXED_WAIT),.SEED(SEED)) instr_mem (
    .clk_i(clk),.rst_ni(rst_n),.req_i(ireq),.addr_i(ia),.we_i(1'b0),.be_i(4'hf),.wdata_i(32'b0),
    .gnt_o(ignt),.rvalid_o(irvalid),.rdata_o(ird),.status_o(),.signature_base_o(),.signature_words_o(),
    .protocol_fail_o(ifail),.accepted_o(iaccepted),.responded_o(iresponded)
  );
  // Negative service test completes the base-pointer load, then withholds the
  // first threshold response so the watchdog observes an accepted qnt packet.
  obi_memory_agent #(.NN_CAPABILITY(NN_ENABLE),.GRANT_MAX(GRANT_MAX),.RESPONSE_MAX(RESPONSE_MAX),.FIRST_RESPONSE_DELAY(EVENT_MODE!=0 || DATA_DEPTH>1 ? 24 : 0),.DROP_RESPONSE(NEGATIVE_ENV),.ALLOW_RESPONSES(NEGATIVE_ENV ? 1 : 0),.MAX_OUTSTANDING(DATA_DEPTH),.FIXED_WAIT(FIXED_WAIT),.SEED(SEED+101)) data_mem (
    .clk_i(clk),.rst_ni(rst_n),.req_i(dreq),.addr_i(da),.we_i(dwe),.be_i(dbe),.wdata_i(dwd),
    .gnt_o(dgnt),.rvalid_o(drvalid),.rdata_o(drd),.status_o(status),.signature_base_o(sigbase),.signature_words_o(sigwords),
    .protocol_fail_o(dfail),.accepted_o(daccepted),.responded_o(dresponded)
  );

  task finish_run(input integer outcome);
    fd=$fopen("actual.hex","w");
    if (sigbase>=32'h10000000 && sigbase<32'h10010000 && sigwords<16384)
      for (int n=0;n<sigwords;n++) $fdisplay(fd,"%08x",data_mem.dmem[(sigbase-32'h10000000)/4+n]);
    $fclose(fd);
    js=$fopen("simulation.json","w");
    $fdisplay(js,"{\"outcome\":%0d,\"status\":%0d,\"cycles\":%0d,\"signature_words\":%0d,\"instruction_requests\":%0d,\"data_requests\":%0d,\"protocol_fail\":%0d,\"last_fetch\":%0d,\"nn_capability\":%0d,\"qnt_commits\":%0d,\"event_fired\":%0d,\"event_acknowledgments\":%0d,\"reset_count\":%0d,\"qnt_issues\":%0d,\"qnt_retire_events\":%0d,\"max_data_pending\":%0d,\"max_qnt_outstanding\":%0d,\"wb_hold_cycles\":%0d,\"step_flush_cycles\":%0d}",
      outcome,status,cycles,sigwords,iaccepted,daccepted,ifail|dfail|monitor_fail,ia,NN_ENABLE,qnt_commits,event_fired,event_acknowledgments,reset_count,qnt_issues,qnt_retire_events,data_mem.max_pending,max_qnt_outstanding,wb_hold_cycles,step_flush_cycles);
    $fclose(js);
    $display("CORE_PROGRAM outcome=%0d status=%08x cycles=%0d words=%0d",outcome,status,cycles,sigwords);
    $finish;
  endtask
  always @(posedge clk) if (rst_n) begin
    cycles<=cycles+1;
    if (ifail || dfail || monitor_fail) finish_run(1);
    else if (cycles>=MAX_CYCLES) begin
      if(NEGATIVE_ENV && (qnt_issues!=1 || qnt_commits!=0))begin
        monitor_fail=1;$display("NEGATIVE_ENV_FAIL did not stall an accepted qnt");
      end
      finish_run(2);
    end
    else if (status!=0) begin
      if (settle>=12 && daccepted==dresponded) finish_run(status==1 ? 0 : 3);
      settle<=settle+1;
    end
  end
`ifdef FYP_OVERLAY
  // Force only the downstream ready interface, after ordinary loads have drained.
  // Keep done blocked for six full cycles and require the final result to hold.
  initial if(FINAL_WB_HOLD)begin
    wait(rst_n && dut.core_i.ex_stage_i.qnt_start_valid);
    @(negedge clk);
    force dut.core_i.ex_stage_i.wb_ready_i=1'b0;
    wait(dut.core_i.ex_stage_i.qnt_done_valid);
    repeat(6)begin
      @(negedge clk);
      wb_hold_cycles++;
      if(dut.core_i.ex_stage_i.qnt_commit || dut.core_i.qnt_release ||
         dut.core_i.ex_stage_i.regfile_alu_we_fw_o || !dut.core_i.qnt_owned ||
         dut.core_i.ex_stage_i.qnt_result!==32'h7)begin
        monitor_fail=1;$display("CORE_HOLD_FAIL final result did not remain pending");
      end
    end
    release dut.core_i.ex_stage_i.wb_ready_i;
  end
  // Assert requests before the sampling edge so phase 5 coincides with the
  // actual terminal response/commit, not the following cycle.
  always @(negedge clk) if(rst_n)begin
    if(!event_fired && EVENT_MODE!=0 &&
        ((EVENT_PHASE==0 && dut.core_i.qnt_valid_ex && !dut.core_i.qnt_owned) ||
         (EVENT_PHASE==1 && dut.core_i.qnt_req_valid && dut.core_i.qnt_req_ready) ||
         (EVENT_PHASE==2 && dut.core_i.qnt_rsp_valid && qnt_responses==1) ||
         (EVENT_PHASE==3 && dut.core_i.qnt_req_valid && !dut.core_i.qnt_req_ready) ||
         (EVENT_PHASE==4 && dut.core_i.instr_valid_id && dut.core_i.id_stage_i.qnt_dec && !dut.core_i.qnt_valid_ex) ||
         (EVENT_PHASE==5 && dut.core_i.qnt_rsp_valid && qnt_responses==3)))begin
      event_fired=1;
      if(EVENT_MODE==1)irq=32'h800;
      if(EVENT_MODE==2 || EVENT_MODE==4)debug_req=1;
      if(EVENT_MODE==3)reset_requested=1;
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
      qnt_responses<=0;qnt_commits<=0;qnt_issues<=0;qnt_retire_events<=0;
      qnt_issue_d<=0;halted_d<=0;qnt_outstanding<=0;max_qnt_outstanding<=0;
      op_responses<=0;op_grants<=0;await_next_issue<=0;
    end
    else begin
      qnt_issue_d<=dut.core_i.id_valid && dut.core_i.is_decoding && dut.core_i.id_stage_i.qnt_en;
      if(dut.core_i.id_valid && dut.core_i.is_decoding && dut.core_i.id_stage_i.qnt_en)begin
        qnt_issues<=qnt_issues+1;
        $fdisplay(trace_fd,"{\"epoch\":%0d,\"op\":%0d,\"event\":\"id_accept\",\"cycle\":%0d,\"pc\":%0d}",reset_count,qnt_issues,cycles,dut.core_i.pc_id);
      end
      if(qnt_issue_d)begin
        if(!dut.core_i.mhpmevent_minstret)begin monitor_fail<=1;$display("CORE_RETIRE_FAIL missing qnt event");end
        else qnt_retire_events<=qnt_retire_events+1;
      end
      if(dut.core_i.ex_stage_i.qnt_start_valid && dut.core_i.ex_stage_i.qnt_start_ready)begin
        op_responses<=0;op_grants<=0;
        $fdisplay(trace_fd,"{\"event\":\"lsu_drained_unit_start\",\"cycle\":%0d}",cycles);
      end
      if(dut.core_i.qnt_req_valid && dut.core_i.qnt_req_ready)begin
        op_grants<=op_grants+1;
        if(op_grants==0)$fdisplay(trace_fd,"{\"event\":\"first_grant\",\"cycle\":%0d}",cycles);
      end
      case({dut.core_i.qnt_req_valid && dut.core_i.qnt_req_ready,dut.core_i.qnt_rsp_valid})
        2'b10:qnt_outstanding<=qnt_outstanding+1;
        2'b01:qnt_outstanding<=qnt_outstanding-1;
        default:;
      endcase
      if(qnt_outstanding>max_qnt_outstanding)max_qnt_outstanding<=qnt_outstanding;
      if(dut.core_i.qnt_rsp_valid)begin
        op_responses<=op_responses+1;
        if(op_responses==(dut.core_i.qnt_q4_ex ? 7 : 3))$fdisplay(trace_fd,"{\"event\":\"last_response\",\"cycle\":%0d}",cycles);
      end
      if(dut.core_i.ex_stage_i.qnt_commit)begin
        $fdisplay(trace_fd,"{\"event\":\"writeback\",\"cycle\":%0d}",cycles);await_next_issue<=1;
      end
      if(await_next_issue && dut.core_i.id_valid && dut.core_i.is_decoding)begin
        $fdisplay(trace_fd,"{\"event\":\"next_id_accept\",\"cycle\":%0d}",cycles);await_next_issue<=0;
      end
      if(EVENT_MODE==4 && dut.core_i.qnt_valid_ex && dut.core_i.id_stage_i.controller_i.ctrl_fsm_cs==cv32e40p_pkg::DBG_FLUSH)
        step_flush_cycles<=step_flush_cycles+1;
      if(dut.core_i.qnt_rsp_valid)qnt_responses<=qnt_responses+1;
      if(dut.core_i.ex_stage_i.qnt_commit)qnt_commits<=qnt_commits+1;
      if((irq_ack || halted) && dut.core_i.qnt_valid_ex && !dut.core_i.ex_stage_i.qnt_commit)begin
        monitor_fail<=1;$display("CORE_EVENT_FAIL interrupted accepted quantization");
      end
      halted_d<=halted;
      if(irq_ack)irq<=0;
      if(halted && debug_req)debug_req<=0;
      if(irq_ack || (halted && !halted_d))event_acknowledgments<=event_acknowledgments+1;
    end
  end
`endif
endmodule
