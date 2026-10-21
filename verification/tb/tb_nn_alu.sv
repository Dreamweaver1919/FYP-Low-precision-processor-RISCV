`timescale 1ns/1ps
module tb_nn_alu;
  import cv32e40p_pkg::*;
  logic enable = 1;
  alu_opcode_e op;
  logic avg;
  logic [31:0] a, b, r4, r2, expected;
  integer fd, rc, width, op_word, avg_word, count = 0;
  string vectors;
  cv32e40p_nn_alu #(.ELEM_BITS(4)) dut4 (
      .enable_i(enable), .operator_i(op), .average_i(avg),
      .operand_a_i(a), .operand_b_i(b), .result_o(r4));
  cv32e40p_nn_alu #(.ELEM_BITS(2)) dut2 (
      .enable_i(enable), .operator_i(op), .average_i(avg),
      .operand_a_i(a), .operand_b_i(b), .result_o(r2));
  initial begin
    if (!$value$plusargs("VECTORS=%s", vectors)) $fatal(1, "VECTORS required");
    fd = $fopen(vectors, "r");
    if (!fd) $fatal(1, "Cannot open vectors %s", vectors);
    while (!$feof(fd)) begin
      rc = $fscanf(fd, "%h %h %h %h %h %h\n", op_word, avg_word, width, a, b, expected);
      if (rc != 6) $fatal(1, "Malformed vector at %0d fields=%0d", count, rc);
      op = alu_opcode_e'(op_word); avg = avg_word;
      #1;
      if ((width != 4 && width != 2) || (width == 4 ? r4 : r2) !== expected)
        $fatal(1, "ALU vector=%0d width=%0d op=%h avg=%0d a=%h b=%h expected=%h actual=%h",
               count, width, op, avg, a, b, expected, width == 4 ? r4 : r2);
      count++;
    end
    enable = 0; #1;
    if (r4 !== 0 || r2 !== 0) $fatal(1, "Disabled ALU must isolate inputs/output");
    if (!count) $fatal(1, "No vectors executed");
    $display("NN_ALU_PASS count=%0d", count);
    $fclose(fd); $finish;
  end
endmodule
