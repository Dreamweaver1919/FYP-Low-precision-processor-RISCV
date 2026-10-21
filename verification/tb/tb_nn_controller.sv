`timescale 1ns/1ps
module tb_nn_controller;
  import cv32e40p_pkg::*;
  logic clk=0,rst_n=0,block_qnt=0;
  logic hi,hd,pc,ack,dec,saveid,saveif,saveex,savecause;
  always #5 clk=~clk;
  cv32e40p_controller #(.COREV_PULP(1),.COREV_XPULPNN(1)) dut (
    .clk(clk),.clk_ungated_i(clk),.rst_n(rst_n),.qnt_block_i(block_qnt),
    .instr_valid_i(1'b1),.branch_taken_ex_i(1'b0),.data_err_i(1'b0),.is_fetch_failed_i(1'b0),
    .debug_req_i(1'b1),.trigger_match_i(1'b0),.irq_req_ctrl_i(1'b1),.irq_id_ctrl_i(5'd7),
    .irq_sec_ctrl_i(1'b0),.id_ready_i(1'b0),.ex_valid_i(1'b0),
    .halt_if_o(hi),.halt_id_o(hd),.pc_set_o(pc),.irq_ack_o(ack),.is_decoding_o(dec),
    .csr_save_id_o(saveid),.csr_save_if_o(saveif),.csr_save_ex_o(saveex),.csr_save_cause_o(savecause));
  initial begin
    #12;rst_n=1;block_qnt=1;
    force dut.ctrl_fsm_cs=DECODE;force dut.debug_mode_q=0;
    #1;
    if(!(hi&&hd&&!pc&&!ack&&!dec&&!saveid&&!saveif&&!saveex&&!savecause))
      $fatal(1,"FAIL decode qnt must hold younger IRQ/debug");
    force dut.ctrl_fsm_cs=DECODE_HWLOOP;#1;
    if(!(hi&&hd&&!pc&&!ack&&!dec)) $fatal(1,"FAIL hwloop qnt hold");
    force dut.ctrl_fsm_cs=DBG_FLUSH;#1;
    if(dut.ctrl_fsm_ns!=DBG_FLUSH || pc || saveid || saveif || saveex || savecause)
      $fatal(1,"FAIL single-step debug must wait for qnt completion");
    release dut.ctrl_fsm_cs;release dut.debug_mode_q;
    $display("PASS NN controller hold including DBG_FLUSH");$finish;
  end
endmodule
