// In-order OBI service; configurable accepted-request FIFO, registered responses.
module obi_memory_agent #(
  parameter bit INSTRUCTION = 0,
  parameter int NN_CAPABILITY = 0,
  parameter int GRANT_MAX = 0,
  parameter int RESPONSE_MAX = 1,
  parameter int FIRST_RESPONSE_DELAY = 0,
  parameter bit DROP_RESPONSE = 0,
  parameter int ALLOW_RESPONSES = 0,
  parameter int MAX_OUTSTANDING = 1,
  parameter bit FIXED_WAIT = 0,
  parameter int SEED = 1
)(
  input logic clk_i, rst_ni,
  input logic req_i,
  input logic [31:0] addr_i,
  input logic we_i,
  input logic [3:0] be_i,
  input logic [31:0] wdata_i,
  output logic gnt_o, rvalid_o,
  output logic [31:0] rdata_o,
  output logic [31:0] status_o, signature_base_o, signature_words_o,
  output logic protocol_fail_o,
  output int accepted_o, responded_o
);
  logic [31:0] imem[0:16383];
  logic [31:0] dmem[0:16383];
  int pending, head, tail, max_pending;
  logic [31:0] responses[0:MAX_OUTSTANDING-1];
  int delays[0:MAX_OUTSTANDING-1];
  logic [31:0] rng;
  int grant_left;
  logic held;
  logic [68:0] held_tuple;

  function automatic logic [31:0] advance(input logic [31:0] x);
    return {x[30:0],x[31]^x[21]^x[1]^x[0]};
  endfunction

  initial begin
    $readmemh("imem.hex",imem);
    $readmemh("dmem.hex",dmem);
  end
  assign gnt_o = rst_ni && req_i && pending<MAX_OUTSTANDING && grant_left==0;
  assign rvalid_o = rst_ni && pending>0 && delays[head]==0 && (!DROP_RESPONSE || responded_o<ALLOW_RESPONSES);
  assign rdata_o = responses[head];

  always @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      pending<=0;head<=0;tail<=0;max_pending<=0; rng<=SEED|1; grant_left<=0;
      for(int slot=0;slot<MAX_OUTSTANDING;slot++)begin responses[slot]<=0;delays[slot]<=0;end
      status_o<=0; signature_base_o<=0; signature_words_o<=0;
      protocol_fail_o<=0; accepted_o<=0; responded_o<=0;
      held<=0; held_tuple<=0;
    end else begin
      if (held && (!req_i || {addr_i,we_i,be_i,wdata_i} !== held_tuple)) begin
        $display("OBI_FAIL request changed before grant instruction=%0d",INSTRUCTION);
        protocol_fail_o<=1;
      end
      held <= req_i && !gnt_o;
      if (req_i && !gnt_o) held_tuple <= {addr_i,we_i,be_i,wdata_i};
      if (req_i && pending<MAX_OUTSTANDING && grant_left>0) grant_left<=grant_left-1;
      for(int slot=0;slot<MAX_OUTSTANDING;slot++) if(delays[slot]>0)delays[slot]<=delays[slot]-1;
      case({gnt_o,rvalid_o})
        2'b10:pending<=pending+1;
        2'b01:pending<=pending-1;
        default:;
      endcase
      if(pending>max_pending)max_pending<=pending;
      if (rvalid_o) begin head<=(head+1)%MAX_OUTSTANDING; responded_o<=responded_o+1; end
      if (gnt_o) begin
        accepted_o<=accepted_o+1;
        tail<=(tail+1)%MAX_OUTSTANDING;
        rng<=advance(rng);
        grant_left <= FIXED_WAIT ? GRANT_MAX : (GRANT_MAX ? (advance(rng) % (GRANT_MAX+1)) : 0);
        delays[tail] <= accepted_o==0 && FIRST_RESPONSE_DELAY>0 ? FIRST_RESPONSE_DELAY :
                        (FIXED_WAIT ? RESPONSE_MAX-1 : (RESPONSE_MAX>1 ? (rng % RESPONSE_MAX) : 0));
        if ($isunknown({addr_i,we_i,be_i,wdata_i})) begin
          protocol_fail_o<=1; $display("OBI_FAIL unknown request");
        end
        if (addr_i < 32'h00010000) begin
          responses[tail]<=imem[addr_i[15:2]];
          if (we_i) begin protocol_fail_o<=1; $display("OBI_FAIL write to ROM"); end
        end else if (!INSTRUCTION && addr_i >= 32'h10000000 && addr_i < 32'h10010000) begin
          responses[tail]<=dmem[addr_i[15:2]];
          if (we_i) for (int b=0;b<4;b++) if (be_i[b]) dmem[addr_i[15:2]][b*8+:8]<=wdata_i[b*8+:8];
        end else if (!INSTRUCTION && addr_i>=32'h20000000 && addr_i<=32'h20000024) begin
          responses[tail]<=addr_i==32'h20000024 ? NN_CAPABILITY : 0;
          if (we_i) begin
            case (addr_i)
              32'h20000000: status_o<=wdata_i;
              32'h20000004: signature_base_o<=wdata_i;
              32'h20000008: signature_words_o<=wdata_i;
              32'h20000024: begin protocol_fail_o<=1; $display("OBI_FAIL write capability"); end
              default: ;
            endcase
          end
        end else begin
          protocol_fail_o<=1; responses[tail]<=0;
          $display("OBI_FAIL unmapped address %08x instruction=%0d",addr_i,INSTRUCTION);
        end
      end
    end
  end
endmodule
