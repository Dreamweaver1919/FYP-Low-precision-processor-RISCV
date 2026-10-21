`timescale 1ns/1ps
module tb_nn_config #(
  parameter integer TEST_PULP=1,
  parameter integer TEST_NN=0,
  parameter integer TEST_CLUSTER=0,
  parameter integer TEST_FPU=0,
  parameter integer TEST_ZFINX=0
);
  cv32e40p_top #(
    .COREV_PULP(TEST_PULP), .COREV_XPULPNN(TEST_NN),
    .COREV_CLUSTER(TEST_CLUSTER), .FPU(TEST_FPU), .ZFINX(TEST_ZFINX)
  ) dut (
    .clk_i(1'b0), .rst_ni(1'b0), .pulp_clock_en_i(1'b0), .scan_cg_en_i(1'b0),
    .boot_addr_i(32'b0), .mtvec_addr_i(32'b0), .dm_halt_addr_i(32'b0),
    .hart_id_i(32'b0), .dm_exception_addr_i(32'b0),
    .instr_gnt_i(1'b0), .instr_rvalid_i(1'b0), .instr_rdata_i(32'b0),
    .data_gnt_i(1'b0), .data_rvalid_i(1'b0), .data_rdata_i(32'b0),
    .irq_i(32'b0), .debug_req_i(1'b0), .fetch_enable_i(1'b0)
  );
  initial begin
    #1;
    $display("NN_CONFIG_PASS pulp=%0d nn=%0d cluster=%0d fpu=%0d zfinx=%0d",
             TEST_PULP,TEST_NN,TEST_CLUSTER,TEST_FPU,TEST_ZFINX);
    $finish;
  end
endmodule
