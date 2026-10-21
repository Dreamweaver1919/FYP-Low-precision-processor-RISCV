// Self-contained OOC validation system. Board clocks/pins are intentionally absent.
module fyp_nn_system #(
  parameter integer COREV_XPULPNN = 0,
  parameter integer SIGNATURE_DIGEST_WORDS = 0, // 0: all; otherwise deterministic prefix
  parameter IMEM_FILE = "imem.hex",
  parameter DMEM_FILE = "dmem.hex"
)(
  input  logic clk_i,
  input  logic rst_ni,
  input  logic start_i,
  output logic done_o,
  output logic pass_o,
  output logic [31:0] signature_o
);
  typedef enum logic [1:0] {WAIT_START, RUN_CPU, SCAN_READ, SCAN_ACCUM} state_e;
  state_e state_q;
  logic started_q, protocol_fail_q;
  (* rom_style = "block" *) logic [31:0] imem [0:16383];
  (* ram_style = "block" *) logic [31:0] dmem [0:16383];
  logic instr_req, instr_gnt, instr_rvalid;
  logic [31:0] instr_addr, instr_rdata;
  logic data_req, data_gnt, data_rvalid, data_we;
  logic [3:0] data_be;
  logic [31:0] data_addr, data_wdata, data_rdata;
  logic [31:0] rom_data_q, ram_data_q, mmio_data_q;
  logic [1:0] data_region_q;
  logic [31:0] signature_base_q, signature_words_q, status_q;
  logic [31:0] scan_index_q;
  logic [31:0] folded;
  logic data_is_rom, data_is_ram, data_is_mmio;
  logic [13:0] scan_address;
  logic [13:0] ram_address;
  logic ram_access, ram_write;
  logic signature_range_valid;

  initial begin
    $readmemh(IMEM_FILE, imem);
    $readmemh(DMEM_FILE, dmem);
  end
  assign instr_gnt = instr_req && state_q == RUN_CPU;
  assign data_gnt = data_req && state_q == RUN_CPU;
  assign data_is_rom = data_addr < 32'h00010000;
  assign data_is_ram = data_addr >= 32'h10000000 && data_addr < 32'h10010000;
  assign data_is_mmio = data_addr >= 32'h20000000 && data_addr <= 32'h20000024;
  assign scan_address = signature_base_q[15:2] + scan_index_q[13:0];
  // One physical RAM port: choose the scan/CPU address before the registered
  // read. Separate conditional array indices obstruct byte-enable BRAM inference.
  assign ram_access = (state_q == SCAN_READ && !done_o) || (data_gnt && data_is_ram);
  assign ram_address = state_q == SCAN_READ ? scan_address : data_addr[15:2];
  assign ram_write = data_gnt && data_is_ram && data_we;
  assign folded = {signature_o[26:0], signature_o[31:27]} ^ ram_data_q;
  assign signature_range_valid = signature_base_q >= 32'h10000000 &&
      signature_base_q <= 32'h10010000 && signature_base_q[1:0] == 0 &&
      signature_words_q <= 32'd16384 &&
      ((signature_base_q - 32'h10000000) >> 2) + signature_words_q <= 32'd16384;

  // Synchronous dual-read ROM supports instruction fetch and data constants.
  // BRAM data outputs have no reset; rvalid qualifies their contents.
  always_ff @(posedge clk_i) begin
    if (instr_gnt) instr_rdata <= imem[instr_addr[15:2]];
    if (data_gnt && data_is_rom) rom_data_q <= imem[data_addr[15:2]];
    if (ram_access) begin
      ram_data_q <= dmem[ram_address];
      if (ram_write)
        for (integer b = 0; b < 4; b++)
          if (data_be[b]) dmem[ram_address][8*b +: 8] <= data_wdata[8*b +: 8];
    end
  end

  always_comb begin
    case (data_region_q)
      2'd0: data_rdata = rom_data_q;
      2'd1: data_rdata = ram_data_q;
      default: data_rdata = mmio_data_q;
    endcase
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      state_q <= WAIT_START;
      started_q <= 0;
      protocol_fail_q <= 0;
      done_o <= 0;
      pass_o <= 0;
      signature_o <= 0;
      signature_base_q <= 0;
      signature_words_q <= 0;
      status_q <= 0;
      scan_index_q <= 0;
      instr_rvalid <= 0;
      data_rvalid <= 0;
      data_region_q <= 0;
      mmio_data_q <= 0;
    end else begin
      instr_rvalid <= instr_gnt;
      data_rvalid <= data_gnt;
      if (instr_gnt && (instr_addr >= 32'h10000 || instr_addr[1:0] != 0))
        protocol_fail_q <= 1;
      if (data_gnt) begin
        data_region_q <= data_is_rom ? 2'd0 : data_is_ram ? 2'd1 : 2'd2;
        mmio_data_q <= (data_addr == 32'h20000024) ? (COREV_XPULPNN ? 32'd1 : 32'd0) : 32'd0;
        if ((!data_is_rom && !data_is_ram && !data_is_mmio) ||
            (data_we && data_is_rom) || (data_we && data_addr == 32'h20000024))
          protocol_fail_q <= 1;
        if (data_we && data_is_mmio) begin
          case (data_addr)
            32'h20000004: signature_base_q <= data_wdata;
            32'h20000008: signature_words_q <= data_wdata;
            32'h20000000: begin
              status_q <= data_wdata;
              scan_index_q <= 0;
              signature_o <= 0;
              if (!signature_range_valid || signature_words_q == 0) begin
                done_o <= 1;
                pass_o <= data_wdata == 1 && !protocol_fail_q && signature_range_valid;
              end else state_q <= SCAN_READ;
            end
            default: ;
          endcase
        end
      end
      case (state_q)
        WAIT_START: if (start_i && !started_q) begin
          started_q <= 1;
          state_q <= RUN_CPU;
        end
        SCAN_READ: if (!done_o) state_q <= SCAN_ACCUM;
        SCAN_ACCUM: if (!done_o) begin
          if (SIGNATURE_DIGEST_WORDS == 0 || scan_index_q < SIGNATURE_DIGEST_WORDS)
            signature_o <= folded;
          if (scan_index_q + 1 == signature_words_q) begin
            done_o <= 1;
            pass_o <= status_q == 1 && !protocol_fail_q;
          end else begin
            scan_index_q <= scan_index_q + 1;
            state_q <= SCAN_READ;
          end
        end
        default: ;
      endcase
    end
  end

  cv32e40p_top #(
    .COREV_PULP(1),
`ifdef FYP_OVERLAY
    .COREV_XPULPNN(COREV_XPULPNN),
`endif
    .COREV_CLUSTER(0), .FPU(0), .ZFINX(0)
  ) core_i (
    .clk_i(clk_i), .rst_ni(rst_ni), .pulp_clock_en_i(1'b1), .scan_cg_en_i(1'b0),
    .boot_addr_i(32'h200), .mtvec_addr_i(32'h100), .dm_halt_addr_i(32'h400),
    .hart_id_i(32'b0), .dm_exception_addr_i(32'h480),
    .instr_req_o(instr_req), .instr_gnt_i(instr_gnt), .instr_rvalid_i(instr_rvalid),
    .instr_addr_o(instr_addr), .instr_rdata_i(instr_rdata),
    .data_req_o(data_req), .data_gnt_i(data_gnt), .data_rvalid_i(data_rvalid),
    .data_we_o(data_we), .data_be_o(data_be), .data_addr_o(data_addr),
    .data_wdata_o(data_wdata), .data_rdata_i(data_rdata),
    .irq_i(32'b0), .irq_ack_o(), .irq_id_o(), .debug_req_i(1'b0),
    .debug_havereset_o(), .debug_running_o(), .debug_halted_o(),
    .fetch_enable_i(state_q == RUN_CPU && !done_o), .core_sleep_o()
  );
endmodule
