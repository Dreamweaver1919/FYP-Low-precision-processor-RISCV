`timescale 1ns/1ps
module tb_nn_lsu;
  logic clk=0, rst_n=0;
  always #5 clk=~clk;
  logic req,gnt=0,rv=0,we;
  logic [31:0] addr,wd,rd=0;
  logic [3:0] be;
  logic nreq=0,acquire=0,acqready,owned,release_owner=0,wbpend=0;
  logic qr=0,qready,qrv,busy;
  logic [31:0] qa=0,qdata,normal_data;
  logic [3:0] qt=0,rt;
  cv32e40p_load_store_unit #(.COREV_XPULPNN(1)) dut (
    .clk(clk),.rst_n(rst_n),.data_req_o(req),.data_gnt_i(gnt),.data_rvalid_i(rv),
    .data_err_i(1'b0),.data_err_pmp_i(1'b0),.data_addr_o(addr),.data_we_o(we),.data_be_o(be),.data_wdata_o(wd),.data_rdata_i(rd),
    .data_we_ex_i(1'b0),.data_type_ex_i(2'b00),.data_wdata_ex_i(32'b0),.data_reg_offset_ex_i(2'b0),
    .data_load_event_ex_i(1'b0),.data_sign_ext_ex_i(2'b0),.data_rdata_ex_o(normal_data),.data_req_ex_i(nreq),
    .operand_a_ex_i(32'h2000),.operand_b_ex_i(32'b0),.addr_useincr_ex_i(1'b0),.data_misaligned_ex_i(1'b0),
    .data_misaligned_o(),.data_atop_ex_i(6'b0),.data_atop_o(),.p_elw_start_o(),.p_elw_finish_o(),
    .lsu_ready_ex_o(),.lsu_ready_wb_o(),.busy_o(busy),
    .qnt_acquire_i(acquire),.qnt_acquire_ready_o(acqready),.normal_wb_pending_i(wbpend),.qnt_owned_o(owned),.qnt_release_i(release_owner),
    .qnt_req_valid_i(qr),.qnt_req_ready_o(qready),.qnt_req_addr_i(qa),.qnt_req_tag_i(qt),
    .qnt_rsp_valid_o(qrv),.qnt_rsp_data_o(qdata),.qnt_rsp_tag_o(rt));
  task automatic cycle; @(posedge clk); #1; @(negedge clk); endtask
  task automatic check(input logic good,input string message);
    if(good !== 1'b1) $fatal(1,"FAIL LSU: %s",message);
  endtask
  initial begin
    repeat(3) cycle(); rst_n=1; cycle();
    // A returning ordinary load and its RF writeback must drain first.
    nreq=1;gnt=1;cycle();nreq=0;acquire=1;wbpend=1;gnt=0;#1;
    check(!acqready && !owned,"older load blocks acquire");
    rv=1;rd=32'h12345678;#1;check(!qrv,"ordinary response not qnt");
    cycle();rv=0;check(!acqready,"older WB still pending");
    wbpend=0;#1;check(acqready,"drained acquire ready");cycle();acquire=0;
    check(owned && busy,"owner acquired");
    qr=1;qa=32'h1040;qt=4'h9;
    repeat(3) begin #1;check(req && addr==32'h1040 && !we && be==15,"stable stalled request");cycle();end
    gnt=1;#1;check(qready,"grant ready");cycle();
    qa=32'h1000;qt=4'h2;cycle();qr=0;gnt=0;
    rv=1;rd=32'hfffffff6;#1;check(qrv && rt==9 && qdata==32'hfffffff6,"first tag response");
    cycle();rv=0;#1;check(normal_data==32'h12345678,"qnt leaves normal data intact");
    // Pop the second response and push a new request together.
    qr=1;qa=32'h1048;qt=4'h7;gnt=1;rv=1;rd=32'd10;#1;
    check(qrv && rt==2 && qready,"simultaneous pop and grant");cycle();qr=0;gnt=0;
    rd=32'd20;#1;check(qrv && rt==7,"third tag");release_owner=1;cycle();rv=0;release_owner=0;
    check(!owned && !busy,"clean release after final response");
    $display("PASS NN LSU ownership, drain, backpressure, response isolation, tag FIFO");$finish;
  end
  initial begin #10000;$fatal(1,"LSU watchdog");end
endmodule
