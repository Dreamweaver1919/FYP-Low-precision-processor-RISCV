// KV260 JTAG laboratory top. The PS supplies PL0; all CPU memories are in PL.
// Apache-2.0.
module fyp_board_top #(
  parameter integer COREV_XPULPNN = 1,
  parameter logic [31:0] BUILD_ID = 0,
  parameter IMEM_FILE = "imem.hex",
  parameter DMEM_FILE = "dmem.hex"
) ();
  wire clk, ps_reset_n;
  wire soft_reset, start;
  wire [8:0] read_address;
  (* ASYNC_REG = "TRUE" *) logic [1:0] reset_sync = 0;
  wire reset_request_n = ps_reset_n && !soft_reset;
  wire rst_n = reset_sync[1];
  wire done, pass, result_valid, overflow;
  wire [13:0] result_index;
  wire [31:0] result_data, result_count, read_data, captured_count, signature;
  logic running=0;
  logic [31:0] elapsed=0, heartbeat=0;
  wire [31:0] status = {27'b0, COREV_XPULPNN[0], overflow, running, pass, done};

  ps_clock_wrapper ps_i(.pl_clk0_0(clk), .pl_resetn0_0(ps_reset_n));
  always_ff @(posedge clk or negedge reset_request_n)
    if (!reset_request_n) reset_sync <= 0;
    else reset_sync <= {reset_sync[0],1'b1};
  always_ff @(posedge clk) heartbeat <= heartbeat+1;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin running<=0; elapsed<=0; end
    else begin
      if (start && !done) running<=1;
      if (running && !done) elapsed<=elapsed+1;
      if (done) running<=0;
    end
  end
  fyp_nn_system #(.COREV_XPULPNN(COREV_XPULPNN), .SIGNATURE_DIGEST_WORDS(356),
    .IMEM_FILE(IMEM_FILE), .DMEM_FILE(DMEM_FILE)) system_i (
    .clk_i(clk), .rst_ni(rst_n), .start_i(start), .done_o(done), .pass_o(pass), .signature_o(signature),
    .result_valid_o(result_valid), .result_index_o(result_index), .result_data_o(result_data),
    .result_count_o(result_count)
  );
  fyp_board_capture capture_i (.clk_i(clk), .rst_ni(rst_n), .valid_i(result_valid),
    .index_i(result_index), .data_i(result_data), .address_i(read_address),
    .data_o(read_data), .count_o(captured_count), .overflow_o(overflow));
  board_vio vio_i (.clk(clk), .probe_in0(status), .probe_in1(signature), .probe_in2(elapsed),
    .probe_in3(BUILD_ID), .probe_in4(read_data), .probe_in5(captured_count), .probe_in6(heartbeat),
    .probe_out0(soft_reset), .probe_out1(start), .probe_out2(read_address));
endmodule
