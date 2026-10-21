`timescale 1ns/1ps
module tb_nn_dotp;
  logic enable = 1;
  logic [1:0] mode;
  logic [31:0] a, b, acc, r4, r2, expected;
  integer fd, rc, width, mode_word, count = 0;
  string vectors;
  cv32e40p_nn_dotp #(.ELEM_BITS(4)) dut4 (
      .enable_i(enable), .signed_mode_i(mode), .operand_a_i(a),
      .operand_b_i(b), .acc_i(acc), .result_o(r4));
  cv32e40p_nn_dotp #(.ELEM_BITS(2)) dut2 (
      .enable_i(enable), .signed_mode_i(mode), .operand_a_i(a),
      .operand_b_i(b), .acc_i(acc), .result_o(r2));
  initial begin
    if (!$value$plusargs("VECTORS=%s", vectors)) $fatal(1, "VECTORS required");
    fd = $fopen(vectors, "r");
    if (!fd) $fatal(1, "Cannot open vectors %s", vectors);
    while (!$feof(fd)) begin
      rc = $fscanf(fd, "%h %h %h %h %h %h\n", width, mode_word, a, b, acc, expected);
      if (rc != 6) $fatal(1, "Malformed vector at %0d fields=%0d", count, rc);
      mode = mode_word;
      #1;
      if ((width != 4 && width != 2) || (width == 4 ? r4 : r2) !== expected)
        $fatal(1, "DOT vector=%0d width=%0d signed=%b a=%h b=%h acc=%h expected=%h actual=%h",
               count, width, mode, a, b, acc, expected, width == 4 ? r4 : r2);
      count++;
    end
    enable = 0; #1;
    if (r4 !== 0 || r2 !== 0) $fatal(1, "Disabled DOT must isolate inputs/output");
    if (!count) $fatal(1, "No vectors executed");
    $display("NN_DOTP_PASS count=%0d", count);
    $fclose(fd); $finish;
  end
endmodule
