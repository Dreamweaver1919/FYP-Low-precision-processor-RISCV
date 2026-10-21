`timescale 1ns/1ps
module tb_nn_quant;
  logic clk_i = 0;
  always #5 clk_i = ~clk_i;
  logic rst_ni = 0;
  logic start_valid_i = 0, start_ready_o;
  logic [31:0] start_activations_i = 0, start_table_base_i = 0;
  logic start_q4_i = 0;
  logic active_o, done_valid_o, done_ready_i = 1;
  logic [31:0] done_result_o;
  logic mem_req_valid_o, mem_req_ready_i = 0;
  logic [31:0] mem_req_addr_o;
  logic [3:0] mem_req_tag_o;
  logic mem_rsp_valid_i = 0;
  logic [31:0] mem_rsp_data_i = 0;
  logic [3:0] mem_rsp_tag_i = 0;
  logic mem_idle_o;
  cv32e40p_nn_quant dut (.*);

  integer signed thresholds [0:1][0:14];
  integer cycle_no = 0, started_cycle, accepted_reads, total_reads = 0;
  integer completed = 0, started = 0, operations = 0, aborted = 0;
  integer active_q, mode = 0, hold_cycles, max_latency = 0;
  integer ideal_q2_cycles = 0, ideal_q4_cycles = 0;
  integer random_q2 = 0, random_q4 = 0;
  integer simultaneous_grant_response = 0, response_while_request_stalled = 0;
  integer two_outstanding_cycles = 0, completion_blocked_cycles = 0;
  integer last_level [0:1];
  logic channel_pending [0:1];
  logic [31:0] active_base, expected_result;
  logic operation_epoch;
  integer q_count = 0, q_head = 0, q_tail = 0;
  integer q_due [0:3];
  logic [31:0] q_data [0:3];
  logic [3:0] q_tag [0:3];
  logic stalled_request = 0, held_done = 0;
  logic [31:0] stalled_address, held_result;
  logic [3:0] stalled_tag;
  integer first_blocked_cycle = -1;
  integer trace_fd, result_fd, seed = 1, random_per_q = 2000;
  integer unsigned rng_state;
  string result_path = "result_sv.json", trace_path = "transactions.csv";
  string case_name = "initial";

  function automatic integer unsigned random_word();
    rng_state = rng_state ^ (rng_state << 13);
    rng_state = rng_state ^ (rng_state >> 17);
    rng_state = rng_state ^ (rng_state << 5);
    return rng_state;
  endfunction

  // Independent scalar oracle: linear count, deliberately no search-tree logic.
  function automatic logic [31:0] oracle(input integer q, input integer a0, input integer a1);
    integer count0, count1;
    count0 = 0;
    count1 = 0;
    for (integer i = 0; i < (1 << q)-1; i++) begin
      if (thresholds[0][i] <= a0) count0++;
      if (thresholds[1][i] <= a1) count1++;
    end
    return (count0 ^ (1 << (q-1))) | ((count1 ^ (1 << (q-1))) << q);
  endfunction

  // Drive response pulses independent of the DUT's phase; no response ready exists.
  always @(negedge clk_i) begin
    mem_rsp_valid_i = 0;
    mem_req_ready_i = 0;
    if (rst_ni) begin
      mem_req_ready_i = (mode != 2) && ((mode == 0) || (mode == 3) || ((random_word() % 4) != 0));
      if (mode != 3 && q_count > 0 && q_due[q_head] <= cycle_no + 1) begin
        mem_rsp_valid_i = 1;
        mem_rsp_data_i = q_data[q_head];
        mem_rsp_tag_i = q_tag[q_head];
      end
    end
  end

  always @(posedge clk_i) begin : protocol_monitor
    integer channel, index, latency;
    cycle_no = cycle_no + 1;
    if (!rst_ni) begin
      q_count = 0;
      q_head = 0;
      q_tail = 0;
      stalled_request = 0;
      held_done = 0;
      channel_pending[0] = 0;
      channel_pending[1] = 0;
    end else begin
      if (mem_rsp_valid_i && mem_req_valid_o && mem_req_ready_i) simultaneous_grant_response++;
      if (mem_rsp_valid_i && mem_req_valid_o && !mem_req_ready_i) response_while_request_stalled++;
      if (q_count == 2) two_outstanding_cycles++;
      if (done_valid_o && !done_ready_i) completion_blocked_cycles++;
      if (stalled_request && (!mem_req_valid_o || mem_req_addr_o !== stalled_address ||
                              mem_req_tag_o !== stalled_tag))
        $fatal(1, "request changed before grant in %s", case_name);
      stalled_request = mem_req_valid_o && !mem_req_ready_i;
      stalled_address = mem_req_addr_o;
      stalled_tag = mem_req_tag_o;
      if (held_done && (!done_valid_o || done_result_o !== held_result))
        $fatal(1, "completion changed under backpressure in %s", case_name);
      held_done = done_valid_o && !done_ready_i;
      held_result = done_result_o;
      if (start_valid_i && start_ready_o) begin
        started++;
        started_cycle = cycle_no;
        accepted_reads = 0;
        last_level[0] = -1;
        last_level[1] = -1;
        first_blocked_cycle = -1;
        if (active_o || q_count != 0) $fatal(1, "start while active/traffic remains");
        $fdisplay(trace_fd, "%0d,%s,start,%08x,%08x", cycle_no, case_name,
                  start_activations_i, start_table_base_i);
      end
      if (mem_rsp_valid_i) begin
        if (q_count == 0) $fatal(1, "unsolicited response");
        channel = mem_rsp_tag_i[2];
        if (!channel_pending[channel]) $fatal(1, "response to nonpending channel");
        channel_pending[channel] = 0;
        $fdisplay(trace_fd, "%0d,%s,response,%01x,%08x", cycle_no, case_name,
                  mem_rsp_tag_i, mem_rsp_data_i);
        q_count--;
        q_head = (q_head+1) % 4;
      end
      if (mem_req_valid_o && mem_req_ready_i) begin
        channel = mem_req_tag_o[2];
        index = (mem_req_addr_o - active_base - 64*channel) >> 2;
        if (!active_o) $fatal(1, "request while inactive");
        if (channel_pending[channel]) $fatal(1, "second outstanding request for channel");
        if (mem_req_addr_o[1:0] != 0 || index < 0 || index >= (1 << active_q)-1)
          $fatal(1, "request outside channel table addr=%08x", mem_req_addr_o);
        if (mem_req_tag_o[1:0] != last_level[channel]+1)
          $fatal(1, "duplicate/skipped comparison level");
        if (accepted_reads == 0) operation_epoch = mem_req_tag_o[3];
        if (mem_req_tag_o[3] !== operation_epoch) $fatal(1, "epoch changed midoperation");
        last_level[channel]++;
        channel_pending[channel] = 1;
        accepted_reads++;
        total_reads++;
        latency = (mode == 0) ? 1 : 1 + (random_word() % 11);
        q_due[q_tail] = cycle_no + latency;
        q_data[q_tail] = thresholds[channel][index];
        q_tag[q_tail] = mem_req_tag_o;
        q_tail = (q_tail+1) % 4;
        q_count++;
        if (q_count > 2) $fatal(1, "more than two outstanding requests");
        $fdisplay(trace_fd, "%0d,%s,grant,%01x,%08x", cycle_no, case_name,
                  mem_req_tag_o, mem_req_addr_o);
      end
      if (done_valid_o) begin
        if (done_result_o !== expected_result)
          $fatal(1, "%s expected %08x got %08x", case_name, expected_result, done_result_o);
        if (accepted_reads != 2*active_q || q_count != 0 ||
            last_level[0] != active_q-1 || last_level[1] != active_q-1)
          $fatal(1, "completion has incorrect read count/pending data");
        if (!mem_idle_o) $fatal(1, "terminal completion did not expose empty memory traffic");
        if (!done_ready_i && first_blocked_cycle < 0) first_blocked_cycle = cycle_no;
        if (done_ready_i) begin
          completed++;
          if (completed+aborted != started) $fatal(1, "duplicate completion");
          latency = cycle_no-started_cycle;
          if (latency > max_latency) max_latency = latency;
          if (mode == 0 && hold_cycles == 0) begin
            if (latency != 2*active_q+1)
              $fatal(1, "ideal latency Q=%0d expected %0d got %0d", active_q, 2*active_q+1, latency);
            if (active_q == 2) ideal_q2_cycles = latency;
            else ideal_q4_cycles = latency;
          end
          $fdisplay(trace_fd, "%0d,%s,done,%0d,%08x", cycle_no, case_name, latency, done_result_o);
        end
      end
    end
  end

  task automatic canonical_tables(input integer q, input integer scale);
    for (integer c = 0; c < 2; c++)
      for (integer i = 0; i < (1 << q)-1; i++)
        thresholds[c][i] = (i-((1 << (q-1))-1))*scale;
  endtask

  task automatic reset_in_phase(input integer phase);
    integer watchdog;
    @(negedge clk_i); #1;
    case_name = "qnt_reset_each_phase";
    active_q = 4;
    active_base = 32'h1000;
    expected_result = 32'h78;
    mode = (phase == 0) ? 2 : ((phase == 1) ? 3 : 0);
    hold_cycles = (phase == 3) ? 100 : 0;
    done_ready_i = (phase != 3);
    start_q4_i = 1;
    start_activations_i = 32'h0008fff8;
    start_table_base_i = active_base;
    start_valid_i = 1;
    do begin @(posedge clk_i); #1; end while (!active_o);
    @(negedge clk_i); #1; start_valid_i = 0;
    watchdog = 0;
    while ((phase == 0 && watchdog < 3) || (phase == 1 && q_count < 2) ||
           (phase == 2 && accepted_reads < 3) || (phase == 3 && first_blocked_cycle < 0)) begin
      @(posedge clk_i); #1;
      watchdog++;
      if (watchdog > 100) $fatal(1, "reset phase not reached");
    end
    @(negedge clk_i); #1;
    aborted++;
    rst_ni = 0;
    #1;
    if (active_o || done_valid_o || mem_req_valid_o || !start_ready_o || !mem_idle_o)
      $fatal(1, "asynchronous reset did not clear active traffic/result");
    // The bus agent resets with the core, discarding accepted old transactions.
    repeat (2) @(negedge clk_i);
    #1; rst_ni = 1;
    repeat (2) @(negedge clk_i);
    #1;
    if (active_o || done_valid_o || mem_req_valid_o || q_count != 0)
      $fatal(1, "stale activity after reset");
  endtask

  task automatic execute(input string name, input integer q, input integer a0,
                         input integer a1, input integer memory_mode,
                         input integer completion_hold, input logic [31:0] literal_expected,
                         input bit use_literal, input bit keep_start_high);
    integer target, watchdog;
    target = completed+1;
    @(negedge clk_i); #1;
    case_name = name;
    active_q = q;
    active_base = 32'h1000;
    mode = memory_mode;
    hold_cycles = completion_hold;
    expected_result = oracle(q, a0, a1);
    if (use_literal && expected_result !== literal_expected)
      $fatal(1, "test oracle disagrees with literal for %s", name);
    start_q4_i = (q == 4);
    start_activations_i = {16'(a1),16'(a0)};
    start_table_base_i = active_base;
    done_ready_i = (completion_hold == 0);
    start_valid_i = 1;
    do begin @(posedge clk_i); #1; end while (!active_o);
    @(negedge clk_i); #1;
    if (!keep_start_high) start_valid_i = 0;
    // Deliberately change input payload while busy: only start may capture it.
    start_activations_i = 32'h7fff8000;
    start_table_base_i = 32'hdeadbeef;
    start_q4_i = !start_q4_i;
    watchdog = 0;
    while (completed < target) begin
      @(posedge clk_i); #1;
      watchdog++;
      if (watchdog > 500) $fatal(1, "watchdog in %s", name);
      if (first_blocked_cycle >= 0 && cycle_no-first_blocked_cycle >= completion_hold) begin
        @(negedge clk_i); #1; done_ready_i = 1;
      end
    end
    @(negedge clk_i); #1;
    start_valid_i = 0;
    if (active_o || !start_ready_o || !mem_idle_o) $fatal(1, "unit did not return to idle");
    operations++;
  endtask

  task automatic random_tables(input integer q);
    integer temporary;
    for (integer c = 0; c < 2; c++) begin
      for (integer i = 0; i < (1 << q)-1; i++) begin
        thresholds[c][i] = integer'(random_word() & 32'hffff)-32768;
        if (i > 0 && (random_word() % 4) == 0) thresholds[c][i] = thresholds[c][i-1];
      end
      for (integer i = 0; i < (1 << q)-1; i++)
        for (integer j = i+1; j < (1 << q)-1; j++)
          if (thresholds[c][j] < thresholds[c][i]) begin
            temporary = thresholds[c][j];
            thresholds[c][j] = thresholds[c][i];
            thresholds[c][i] = temporary;
          end
    end
  endtask

  initial begin : tests
    integer unused_arg, a0, a1;
    unused_arg = $value$plusargs("SEED=%d", seed);
    unused_arg = $value$plusargs("RANDOM_PER_Q=%d", random_per_q);
    unused_arg = $value$plusargs("RESULT=%s", result_path);
    unused_arg = $value$plusargs("TRACE=%s", trace_path);
    rng_state = (seed == 0) ? 32'h1 : seed;
    trace_fd = $fopen(trace_path, "w");
    if (trace_fd == 0) $fatal(1, "cannot open trace");
    $fdisplay(trace_fd, "cycle,case,event,tag_or_latency,address_or_data");
    repeat (3) @(negedge clk_i);
    #1; rst_ni = 1;
    canonical_tables(2,10);
    execute("qnt_q2_opposite_branches",2,-5,15,0,0,32'h7,1,0);
    execute("qnt_q2_equalities",2,0,10,1,0,32'h4,1,0);
    execute("qnt_q2_signed_extrema",2,-32768,32767,1,0,32'h6,1,0);
    thresholds[0][0] = -10; thresholds[0][1] = -10; thresholds[0][2] = 10;
    thresholds[1][0] = -10; thresholds[1][1] = -10; thresholds[1][2] = 10;
    execute("qnt_duplicate_thresholds",2,-10,-9,1,0,32'h0,1,0);
    canonical_tables(2,10);
    thresholds[1][0] = 100; thresholds[1][1] = 200; thresholds[1][2] = 300;
    execute("qnt_independent_channel_tables",2,15,150,1,0,32'hd,1,0);
    canonical_tables(4,10);
    execute("qnt_q4_opposite_branches",4,-5,15,0,0,32'h1f,1,0);
    execute("qnt_q4_equalities",4,0,10,1,0,32'h10,1,0);
    canonical_tables(4,1);
    execute("qnt_q4_signed_extrema",4,-8,8,0,0,32'h78,1,0);
    execute("qnt_q4_int16_extrema",4,-32768,32767,1,0,32'h78,1,0);
    execute("qnt_final_backpressure",4,-8,8,1,4,32'h78,1,0);
    execute("qnt_level_start_not_restart",4,-8,8,1,0,32'h78,1,1);
    for (integer phase = 0; phase < 4; phase++) begin
      reset_in_phase(phase);
      execute("qnt_restart_after_reset",4,-8,8,0,0,32'h78,1,0);
    end
    for (integer q = 2; q <= 4; q += 2) begin
      canonical_tables(q,10);
      for (integer i = 0; i < (1 << q)-1; i++)
        for (integer delta = -1; delta <= 1; delta++)
          execute("qnt_all_bin_edges",q,thresholds[0][i]+delta,-thresholds[0][i]-delta,
                  1,0,0,0,0);
    end
    // Alternate Q on every random operation to detect stale captured precision.
    for (integer n = 0; n < random_per_q; n++) begin
      for (integer q = 2; q <= 4; q += 2) begin
        random_tables(q);
        a0 = integer'(random_word() & 32'hffff)-32768;
        a1 = integer'(random_word() & 32'hffff)-32768;
        execute("qnt_random_tables",q,a0,a1,1,(n%97 == 0) ? 4 : 0,0,0,0);
        if (q == 2) random_q2++; else random_q4++;
      end
    end
    result_fd = $fopen(result_path, "w");
    if (result_fd == 0) $fatal(1, "cannot open structured result");
    if (aborted != 4 || simultaneous_grant_response == 0 || response_while_request_stalled == 0 ||
        two_outstanding_cycles == 0 || completion_blocked_cycles == 0)
      $fatal(1, "required protocol scenario was not exercised");
    $fdisplay(result_fd, "{\"status\":\"PASS\",\"seed\":%0d,\"operations\":%0d,\"reads\":%0d,\"random_q2\":%0d,\"random_q4\":%0d,\"ideal_q2_cycles\":%0d,\"ideal_q4_cycles\":%0d,\"max_service_cycles\":%0d,\"reset_phases\":%0d,\"simultaneous_grant_response\":%0d,\"response_while_request_stalled\":%0d,\"two_outstanding_cycles\":%0d,\"completion_blocked_cycles\":%0d}",
              seed,operations,total_reads,random_q2,random_q4,ideal_q2_cycles,ideal_q4_cycles,max_latency,
              aborted,simultaneous_grant_response,response_while_request_stalled,two_outstanding_cycles,completion_blocked_cycles);
    $fclose(result_fd);
    $fclose(trace_fd);
    $display("PASS quant_unit seed=%0d operations=%0d reads=%0d ideal_q2=5 ideal_q4=9",seed,operations,total_reads);
    $finish;
  end
  initial begin
    #100000000;
    $fatal(1, "global watchdog");
  end
endmodule
