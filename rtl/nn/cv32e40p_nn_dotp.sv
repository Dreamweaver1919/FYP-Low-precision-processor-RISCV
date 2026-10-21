// FYP DATE 2020 XpulpNN functional reproduction; local ABI v1.
// Each precision owns an independent multiplier region and balanced tree.
module cv32e40p_nn_dotp #(parameter integer ELEM_BITS = 4) (
  input logic enable_i,
  input logic [1:0] signed_mode_i,
  input logic [31:0] operand_a_i,
  input logic [31:0] operand_b_i,
  input logic [31:0] acc_i,
  output logic [31:0] result_o
);
  localparam integer LANES = 32 / ELEM_BITS;
  localparam integer PRODUCT_BITS = 2 * (ELEM_BITS + 1);
  localparam integer TREE_BITS = PRODUCT_BITS + $clog2(LANES);
  logic signed [TREE_BITS-1:0] tree [1:2*LANES-1];
  logic [31:0] acc;
  if (ELEM_BITS != 4 && ELEM_BITS != 2) begin : gen_bad_width
    initial $fatal(1, "NN DOTP ELEM_BITS must be 4 or 2");
  end
  assign acc = enable_i ? acc_i : '0;
  for (genvar lane = 0; lane < LANES; lane++) begin : gen_product
    logic [ELEM_BITS-1:0] a, b;
    logic signed [ELEM_BITS:0] a_ext, b_ext;
    logic signed [PRODUCT_BITS-1:0] product;
    assign a = enable_i ? operand_a_i[ELEM_BITS*lane +: ELEM_BITS] : '0;
    assign b = enable_i ? operand_b_i[ELEM_BITS*lane +: ELEM_BITS] : '0;
    assign a_ext = {signed_mode_i[1] & a[ELEM_BITS-1], a};
    assign b_ext = {signed_mode_i[0] & b[ELEM_BITS-1], b};
    assign product = a_ext * b_ext;
    assign tree[LANES+lane] = {{(TREE_BITS-PRODUCT_BITS){product[PRODUCT_BITS-1]}}, product};
  end
  for (genvar node = 1; node < LANES; node++) begin : gen_sum
    assign tree[node] = tree[2*node] + tree[2*node+1];
  end
  assign result_o = enable_i ? (acc + {{(32-TREE_BITS){tree[1][TREE_BITS-1]}}, tree[1]}) : '0;
endmodule
