`timescale 1ns/1ps
module tb_fyp_nn_system #(
  parameter integer NN_ENABLE=0,
  parameter integer EXPECTED_WORDS=7,
  parameter integer DIGEST_WORDS=EXPECTED_WORDS,
  parameter integer MAX_CYCLES=5000000
);
  logic clk_i=0, rst_ni=0, start_i=0;
  logic done_o, pass_o;
  logic [31:0] signature_o;
  logic [31:0] expected[0:16383];
  logic [31:0] expected_mask[0:16383];
  logic [31:0] folded, observed;
  integer fd, cycles;
  fyp_nn_system #(.COREV_XPULPNN(NN_ENABLE), .SIGNATURE_DIGEST_WORDS(DIGEST_WORDS)) dut(.*);
  always #5 clk_i=~clk_i;
  initial begin
    $readmemh("expected.hex",expected);
    $readmemh("expected_mask.hex",expected_mask);
    repeat(5) @(negedge clk_i);
    rst_ni=1;
    repeat(3) @(negedge clk_i);
    if(done_o) $fatal(1,"wrapper completed before start");
    start_i=1;
    @(negedge clk_i); start_i=0;
    cycles=0;
    while(!done_o && cycles<MAX_CYCLES) begin @(negedge clk_i); cycles++; end
    if(!done_o) $fatal(1,"wrapper watchdog cycles=%0d",cycles);
    if(!pass_o) $fatal(1,"wrapper reported failure");
    if(dut.signature_words_q != EXPECTED_WORDS) $fatal(1,"signature length mismatch");
    folded=0;
    fd=$fopen("actual.hex","w");
    for(integer i=0;i<EXPECTED_WORDS;i++) begin
      observed=dut.dmem[(dut.signature_base_q-32'h10000000)/4+i];
      $fdisplay(fd,"%08x",observed);
      if($isunknown(observed) || (observed & expected_mask[i]) !== (expected[i] & expected_mask[i]))
        $fatal(1,"signature word %0d expected=%08x actual=%08x",i,expected[i],observed);
      if(i<DIGEST_WORDS) folded={folded[26:0],folded[31:27]} ^ observed;
    end
    $fclose(fd);
    if(signature_o !== folded) $fatal(1,"external signature fold mismatch");
    // A second start must not reset/replay the already completed operation.
    start_i=1;
    repeat(3) @(negedge clk_i);
    start_i=0;
    repeat(20) begin
      @(negedge clk_i);
      if(!done_o || !pass_o || signature_o !== folded) $fatal(1,"completion not stable");
    end
    fd=$fopen("result_sv.json","w");
    $fdisplay(fd,"{\"status\":\"PASS\",\"nn_enable\":%0d,\"cycles\":%0d,\"signature_words\":%0d,\"signature\":%0d}",NN_ENABLE,cycles,EXPECTED_WORDS,signature_o);
    $fclose(fd);
    $display("PASS system wrapper NN=%0d cycles=%0d signature=%08x",NN_ENABLE,cycles,signature_o);
    $finish;
  end
endmodule
