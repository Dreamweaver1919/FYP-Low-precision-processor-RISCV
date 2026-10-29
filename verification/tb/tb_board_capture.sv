`timescale 1ns/1ps
module tb_board_capture;
  logic clk_i=0, rst_ni=0, valid_i=0;
  logic [13:0] index_i=0;
  logic [31:0] data_i=0;
  logic [8:0] address_i=0;
  logic [31:0] data_o, count_o;
  logic overflow_o;
  fyp_board_capture dut(.*);
  always #5 clk_i=~clk_i;
  initial begin
    repeat(3) @(negedge clk_i);
    rst_ni=1;
    for (integer n=0;n<472;n++) begin
      valid_i=1; index_i=n; data_i=32'h12340000+n;
      @(negedge clk_i);
      valid_i=0; @(negedge clk_i);
    end
    if(count_o!=472 || overflow_o) $fatal(1,"capture count/overflow");
    for (integer n=0;n<472;n++) begin
      address_i=n; @(negedge clk_i);
      if(data_o !== 32'h12340000+n) $fatal(1,"readback %0d",n);
    end
    index_i=512; data_i='1; valid_i=1; @(negedge clk_i); valid_i=0;
    if(!overflow_o) $fatal(1,"overflow not detected");
    address_i=0; @(negedge clk_i);
    if(data_o !== 32'h12340000) $fatal(1,"overflow corrupted memory");
    rst_ni=0; @(negedge clk_i); rst_ni=1; @(negedge clk_i);
    if(count_o!=0 || overflow_o) $fatal(1,"reset metadata");
    $display("PASS board capture 472 words, overflow and reset");
    $finish;
  end
endmodule
