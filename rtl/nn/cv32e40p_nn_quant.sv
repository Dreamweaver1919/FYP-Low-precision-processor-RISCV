// SPDX-License-Identifier: Apache-2.0
// Local DATE-2020-inspired quantizer ABI; no author binary compatibility implied.
module cv32e40p_nn_quant (
  input  logic        clk_i,
  input  logic        rst_ni,
  input  logic        start_valid_i,
  output logic        start_ready_o,
  input  logic [31:0] start_activations_i,
  input  logic [31:0] start_table_base_i,
  input  logic        start_q4_i,
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
  typedef enum logic [1:0] {IDLE, RUN, RESULT} state_e;
  state_e state_q, state_d;
  logic q4_q, q4_d, epoch_q, epoch_d;
  logic signed [15:0] activation_q [2], activation_d [2];
  logic [31:0] base_q [2], base_d [2];
  logic [3:0] index_q [2], index_d [2];
  logic [2:0] level_q [2], level_d [2];
  logic [3:0] rank_q [2], rank_d [2];
  logic [1:0] pending_q, pending_d, finished_q, finished_d;
  logic next_channel_q, next_channel_d;
  logic parked_q, parked_d;
  logic [31:0] parked_addr_q, parked_addr_d;
  logic [3:0] parked_tag_q, parked_tag_d;
  logic [31:0] result_q, result_d;
  logic selected_channel, selected_valid, response_channel;
  logic [1:0] eligible;
  logic [3:0] index_step;
  logic [1:0] greater_equal;
  logic signed [15:0] comparator_a [2], comparator_b [2];

  // Two independent comparison regions. Only the responding channel switches.
  for (genvar c = 0; c < 2; c++) begin : gen_compare
    assign comparator_a[c] = (state_q == RUN && mem_rsp_valid_i &&
                              mem_rsp_tag_i[2] == c) ? activation_q[c] : 16'sd0;
    assign comparator_b[c] = (state_q == RUN && mem_rsp_valid_i &&
                              mem_rsp_tag_i[2] == c) ? $signed(mem_rsp_data_i[15:0]) : 16'sd0;
    assign greater_equal[c] = comparator_a[c] >= comparator_b[c];
  end

  always_comb begin
    state_d = state_q;
    q4_d = q4_q;
    epoch_d = epoch_q;
    pending_d = pending_q;
    finished_d = finished_q;
    next_channel_d = next_channel_q;
    parked_d = parked_q;
    parked_addr_d = parked_addr_q;
    parked_tag_d = parked_tag_q;
    result_d = result_q;
    for (int c = 0; c < 2; c++) begin
      activation_d[c] = activation_q[c];
      base_d[c] = base_q[c];
      index_d[c] = index_q[c];
      level_d[c] = level_q[c];
      rank_d[c] = rank_q[c];
    end

    start_ready_o = state_q == IDLE;
    active_o = state_q != IDLE;
    done_valid_o = state_q == RESULT;
    done_result_o = result_q;
    mem_req_valid_o = 1'b0;
    mem_req_addr_o = '0;
    mem_req_tag_o = '0;
    eligible = ~pending_q & ~finished_q;
    selected_channel = next_channel_q;
    selected_valid = 1'b0;
    response_channel = mem_rsp_tag_i[2];
    index_step = '0;

    unique case (state_q)
      IDLE: begin
        if (start_valid_i) begin
          state_d = RUN;
          q4_d = start_q4_i;
          epoch_d = ~epoch_q;
          activation_d[0] = $signed(start_activations_i[15:0]);
          activation_d[1] = $signed(start_activations_i[31:16]);
          base_d[0] = start_table_base_i;
          base_d[1] = start_table_base_i + 32'd64;
          for (int c = 0; c < 2; c++) begin
            index_d[c] = start_q4_i ? 4'd7 : 4'd1;
            level_d[c] = '0;
            rank_d[c] = '0;
          end
          pending_d = '0;
          finished_d = '0;
          next_channel_d = 1'b0;
          parked_d = 1'b0;
        end
      end

      RUN: begin
        // Selection uses registered context only: no response-to-request path.
        if (parked_q) begin
          mem_req_valid_o = 1'b1;
          mem_req_addr_o = parked_addr_q;
          mem_req_tag_o = parked_tag_q;
          selected_channel = parked_tag_q[2];
        end else begin
          if (eligible[next_channel_q]) begin
            selected_channel = next_channel_q;
            selected_valid = 1'b1;
          end else if (eligible[~next_channel_q]) begin
            selected_channel = ~next_channel_q;
            selected_valid = 1'b1;
          end
          if (selected_valid) begin
            mem_req_valid_o = 1'b1;
            mem_req_addr_o = {base_q[selected_channel][31:6], index_q[selected_channel], 2'b00};
            mem_req_tag_o = {epoch_q, selected_channel, level_q[selected_channel][1:0]};
          end
        end
        if (mem_req_valid_o) begin
          if (mem_req_ready_i) begin
            pending_d[selected_channel] = 1'b1;
            next_channel_d = ~selected_channel;
            parked_d = 1'b0;
          end else begin
            parked_d = 1'b1;
            parked_addr_d = mem_req_addr_o;
            parked_tag_d = mem_req_tag_o;
          end
        end

        // Every response pulse is consumed, even while the other request stalls.
        if (mem_rsp_valid_i) begin
          pending_d[response_channel] = 1'b0;
          rank_d[response_channel] = {rank_q[response_channel][2:0], greater_equal[response_channel]};
          level_d[response_channel] = level_q[response_channel] + 3'd1;
          if (level_q[response_channel] == (q4_q ? 3'd3 : 3'd1)) begin
            finished_d[response_channel] = 1'b1;
          end else begin
            if (!q4_q) index_step = 4'd1;
            else begin
              unique case (level_q[response_channel])
                3'd0: index_step = 4'd4;
                3'd1: index_step = 4'd2;
                default: index_step = 4'd1;
              endcase
            end
            if (greater_equal[response_channel])
              index_d[response_channel] = index_q[response_channel] + index_step;
            else index_d[response_channel] = index_q[response_channel] - index_step;
          end

          if (&finished_d && !(|pending_d) && !parked_d) begin
            // Fall through for 9/5 cycles; save the same result if WB is blocked.
            done_valid_o = 1'b1;
            if (q4_q)
              done_result_o = {24'b0, (rank_d[1] ^ 4'h8), (rank_d[0] ^ 4'h8)};
            else
              done_result_o = {28'b0, (rank_d[1][1:0] ^ 2'b10), (rank_d[0][1:0] ^ 2'b10)};
            result_d = done_result_o;
            state_d = done_ready_i ? IDLE : RESULT;
          end
        end
      end

      RESULT: begin
        if (done_ready_i) state_d = IDLE;
      end
      default: state_d = IDLE;
    endcase

    // Empty after the current request/response handshakes, including the terminal
    // response. The LSU independently checks its own tag FIFO before releasing.
    mem_idle_o = !(|pending_d) && !parked_d;
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      state_q <= IDLE;
      q4_q <= 1'b0;
      epoch_q <= 1'b0;
      pending_q <= '0;
      finished_q <= '0;
      next_channel_q <= 1'b0;
      parked_q <= 1'b0;
      parked_addr_q <= '0;
      parked_tag_q <= '0;
      result_q <= '0;
      for (int c = 0; c < 2; c++) begin
        activation_q[c] <= '0;
        base_q[c] <= '0;
        index_q[c] <= '0;
        level_q[c] <= '0;
        rank_q[c] <= '0;
      end
    end else begin
      state_q <= state_d;
      q4_q <= q4_d;
      epoch_q <= epoch_d;
      pending_q <= pending_d;
      finished_q <= finished_d;
      next_channel_q <= next_channel_d;
      parked_q <= parked_d;
      parked_addr_q <= parked_addr_d;
      parked_tag_q <= parked_tag_d;
      result_q <= result_d;
      for (int c = 0; c < 2; c++) begin
        activation_q[c] <= activation_d[c];
        base_q[c] <= base_d[c];
        index_q[c] <= index_d[c];
        level_q[c] <= level_d[c];
        rank_q[c] <= rank_d[c];
      end
    end
  end

`ifndef SYNTHESIS
  always @(posedge clk_i) begin
    if (rst_ni) begin
      if (start_valid_i && start_ready_o)
        assert (start_table_base_i[5:0] == 0 && start_table_base_i <= 32'hffffff80)
          else $fatal(1, "qnt start base was not validated in ID");
      if (mem_rsp_valid_i) begin
        assert (state_q == RUN && pending_q[mem_rsp_tag_i[2]])
          else $fatal(1, "qnt response without an outstanding channel");
        assert (mem_rsp_tag_i == {epoch_q, mem_rsp_tag_i[2], level_q[mem_rsp_tag_i[2]][1:0]})
          else $fatal(1, "qnt response epoch/level mismatch");
      end
      if (mem_req_valid_o && mem_req_ready_i)
        assert (!pending_q[mem_req_tag_o[2]] && !finished_q[mem_req_tag_o[2]])
          else $fatal(1, "qnt duplicate channel request");
    end
  end
`endif
endmodule
