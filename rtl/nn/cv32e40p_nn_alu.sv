// FYP DATE 2020 XpulpNN functional reproduction; local ABI v1.
// Packed lanes use the existing COREV wrap-before-shift average convention.
module cv32e40p_nn_alu
  import cv32e40p_pkg::*;
#(parameter integer ELEM_BITS = 4) (
  input logic enable_i,
  input alu_opcode_e operator_i,
  input logic average_i,
  input logic [31:0] operand_a_i,
  input logic [31:0] operand_b_i,
  output logic [31:0] result_o
);
  localparam integer LANES = 32 / ELEM_BITS;
  localparam integer SHAMT_BITS = $clog2(ELEM_BITS);
  if (ELEM_BITS != 4 && ELEM_BITS != 2) begin : gen_bad_width
    initial $fatal(1, "NN ALU ELEM_BITS must be 4 or 2");
  end
  for (genvar lane = 0; lane < LANES; lane++) begin : gen_lane
    logic [ELEM_BITS-1:0] a, b, sum, value;
    assign a = enable_i ? operand_a_i[ELEM_BITS*lane +: ELEM_BITS] : '0;
    assign b = enable_i ? operand_b_i[ELEM_BITS*lane +: ELEM_BITS] : '0;
    assign sum = a + b;
    always_comb begin
      value = '0;
      case (operator_i)
        ALU_ADD: begin
          value = sum;
          if (average_i) value = $signed(sum) >>> 1;
        end
        ALU_ADDU: value = average_i ? (sum >> 1) : sum;
        ALU_SUB: value = a - b;
        ALU_MIN: value = $signed(a) < $signed(b) ? a : b;
        ALU_MINU: value = a < b ? a : b;
        ALU_MAX: value = $signed(a) > $signed(b) ? a : b;
        ALU_MAXU: value = a > b ? a : b;
        ALU_SRL: value = a >> b[SHAMT_BITS-1:0];
        ALU_SRA: value = $signed(a) >>> b[SHAMT_BITS-1:0];
        ALU_SLL: value = a << b[SHAMT_BITS-1:0];
        ALU_ABS: value = a[ELEM_BITS-1] ? (~a + 1'b1) : a;
        default: value = '0;
      endcase
    end
    assign result_o[ELEM_BITS*lane +: ELEM_BITS] = enable_i ? value : '0;
  end
endmodule
