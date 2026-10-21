`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2026/10/19 15:27:06
// Design Name: 
// Module Name: cv32e40p_clock_gate
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////



module cv32e40p_clock_gate (
    input  logic clk_i,
    input  logic en_i,
    input  logic scan_cg_en_i,
    output logic clk_o
);

    wire clock_enable;

    assign clock_enable = en_i | scan_cg_en_i;

    BUFGCE #(
        .CE_TYPE("SYNC"),
        .IS_CE_INVERTED(1'b0),
        .IS_I_INVERTED(1'b0)
    ) bufgce_inst (
        .I  (clk_i),
        .CE (clock_enable),
        .O  (clk_o)
    );

endmodule

