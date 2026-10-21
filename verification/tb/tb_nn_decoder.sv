`timescale 1ns/1ps
module tb_nn_decoder;
  import cv32e40p_pkg::*;
  import cv32e40p_apu_core_pkg::*;
  import cv32e40p_fpu_pkg::*;
  logic [31:0] instr;
  logic deassert = 0;
  integer tests = 0, legal_count = 0;
  logic d_qnt_dec_o, d_qnt_q4_o, d_qnt_en_o;
  logic z_qnt_dec_o, z_qnt_q4_o, z_qnt_en_o;
  logic no_pulp_illegal;
  logic d_illegal_insn_o;
  logic d_ebrk_insn_o;
  logic d_mret_insn_o;
  logic d_uret_insn_o;
  logic d_dret_insn_o;
  logic d_mret_dec_o;
  logic d_uret_dec_o;
  logic d_dret_dec_o;
  logic d_ecall_insn_o;
  logic d_wfi_o;
  logic d_fencei_insn_o;
  logic d_rega_used_o;
  logic d_regb_used_o;
  logic d_regc_used_o;
  logic d_reg_fp_a_o;
  logic d_reg_fp_b_o;
  logic d_reg_fp_c_o;
  logic d_reg_fp_d_o;
  logic [ 0:0] d_bmask_a_mux_o;
  logic [ 1:0] d_bmask_b_mux_o;
  logic d_alu_bmask_a_mux_sel_o;
  logic d_alu_bmask_b_mux_sel_o;
  logic d_alu_en_o;
  alu_opcode_e d_alu_operator_o;
  logic [2:0] d_alu_op_a_mux_sel_o;
  logic [2:0] d_alu_op_b_mux_sel_o;
  logic [1:0] d_alu_op_c_mux_sel_o;
  logic d_alu_vec_o;
  logic [2:0] d_alu_vec_mode_o;
  logic d_scalar_replication_o;
  logic d_scalar_replication_c_o;
  logic [0:0] d_imm_a_mux_sel_o;
  logic [3:0] d_imm_b_mux_sel_o;
  logic [1:0] d_regc_mux_o;
  logic d_is_clpx_o;
  logic d_is_subrot_o;
  mul_opcode_e d_mult_operator_o;
  logic d_mult_int_en_o;
  logic d_mult_dot_en_o;
  logic [0:0] d_mult_imm_mux_o;
  logic d_mult_sel_subword_o;
  logic [1:0] d_mult_signed_mode_o;
  logic [1:0] d_mult_dot_signed_o;
  logic [cv32e40p_fpu_pkg::FP_FORMAT_BITS-1:0] d_fpu_dst_fmt_o;
  logic [cv32e40p_fpu_pkg::FP_FORMAT_BITS-1:0] d_fpu_src_fmt_o;
  logic [cv32e40p_fpu_pkg::INT_FORMAT_BITS-1:0] d_fpu_int_fmt_o;
  logic d_apu_en_o;
  logic [APU_WOP_CPU-1:0] d_apu_op_o;
  logic [1:0] d_apu_lat_o;
  logic [2:0] d_fp_rnd_mode_o;
  logic d_regfile_mem_we_o;
  logic d_regfile_alu_we_o;
  logic d_regfile_alu_we_dec_o;
  logic d_regfile_alu_waddr_sel_o;
  logic d_csr_access_o;
  logic d_csr_status_o;
  csr_opcode_e d_csr_op_o;
  logic d_data_req_o;
  logic d_data_we_o;
  logic d_prepost_useincr_o;
  logic [1:0] d_data_type_o;
  logic [1:0] d_data_sign_extension_o;
  logic [1:0] d_data_reg_offset_o;
  logic d_data_load_event_o;
  logic [5:0] d_atop_o;
  logic [2:0] d_hwlp_we_o;
  logic [1:0] d_hwlp_target_mux_sel_o;
  logic [1:0] d_hwlp_start_mux_sel_o;
  logic d_hwlp_cnt_mux_sel_o;
  logic [1:0] d_ctrl_transfer_insn_in_dec_o;
  logic [1:0] d_ctrl_transfer_insn_in_id_o;
  logic [1:0] d_ctrl_transfer_target_mux_sel_o;
  logic b_illegal_insn_o;
  logic b_ebrk_insn_o;
  logic b_mret_insn_o;
  logic b_uret_insn_o;
  logic b_dret_insn_o;
  logic b_mret_dec_o;
  logic b_uret_dec_o;
  logic b_dret_dec_o;
  logic b_ecall_insn_o;
  logic b_wfi_o;
  logic b_fencei_insn_o;
  logic b_rega_used_o;
  logic b_regb_used_o;
  logic b_regc_used_o;
  logic b_reg_fp_a_o;
  logic b_reg_fp_b_o;
  logic b_reg_fp_c_o;
  logic b_reg_fp_d_o;
  logic [ 0:0] b_bmask_a_mux_o;
  logic [ 1:0] b_bmask_b_mux_o;
  logic b_alu_bmask_a_mux_sel_o;
  logic b_alu_bmask_b_mux_sel_o;
  logic b_alu_en_o;
  alu_opcode_e b_alu_operator_o;
  logic [2:0] b_alu_op_a_mux_sel_o;
  logic [2:0] b_alu_op_b_mux_sel_o;
  logic [1:0] b_alu_op_c_mux_sel_o;
  logic b_alu_vec_o;
  logic [1:0] b_alu_vec_mode_o;
  logic b_scalar_replication_o;
  logic b_scalar_replication_c_o;
  logic [0:0] b_imm_a_mux_sel_o;
  logic [3:0] b_imm_b_mux_sel_o;
  logic [1:0] b_regc_mux_o;
  logic b_is_clpx_o;
  logic b_is_subrot_o;
  mul_opcode_e b_mult_operator_o;
  logic b_mult_int_en_o;
  logic b_mult_dot_en_o;
  logic [0:0] b_mult_imm_mux_o;
  logic b_mult_sel_subword_o;
  logic [1:0] b_mult_signed_mode_o;
  logic [1:0] b_mult_dot_signed_o;
  logic [cv32e40p_fpu_pkg::FP_FORMAT_BITS-1:0] b_fpu_dst_fmt_o;
  logic [cv32e40p_fpu_pkg::FP_FORMAT_BITS-1:0] b_fpu_src_fmt_o;
  logic [cv32e40p_fpu_pkg::INT_FORMAT_BITS-1:0] b_fpu_int_fmt_o;
  logic b_apu_en_o;
  logic [APU_WOP_CPU-1:0] b_apu_op_o;
  logic [1:0] b_apu_lat_o;
  logic [2:0] b_fp_rnd_mode_o;
  logic b_regfile_mem_we_o;
  logic b_regfile_alu_we_o;
  logic b_regfile_alu_we_dec_o;
  logic b_regfile_alu_waddr_sel_o;
  logic b_csr_access_o;
  logic b_csr_status_o;
  csr_opcode_e b_csr_op_o;
  logic b_data_req_o;
  logic b_data_we_o;
  logic b_prepost_useincr_o;
  logic [1:0] b_data_type_o;
  logic [1:0] b_data_sign_extension_o;
  logic [1:0] b_data_reg_offset_o;
  logic b_data_load_event_o;
  logic [5:0] b_atop_o;
  logic [2:0] b_hwlp_we_o;
  logic [1:0] b_hwlp_target_mux_sel_o;
  logic [1:0] b_hwlp_start_mux_sel_o;
  logic b_hwlp_cnt_mux_sel_o;
  logic [1:0] b_ctrl_transfer_insn_in_dec_o;
  logic [1:0] b_ctrl_transfer_insn_in_id_o;
  logic [1:0] b_ctrl_transfer_target_mux_sel_o;
  logic z_illegal_insn_o;
  logic z_ebrk_insn_o;
  logic z_mret_insn_o;
  logic z_uret_insn_o;
  logic z_dret_insn_o;
  logic z_mret_dec_o;
  logic z_uret_dec_o;
  logic z_dret_dec_o;
  logic z_ecall_insn_o;
  logic z_wfi_o;
  logic z_fencei_insn_o;
  logic z_rega_used_o;
  logic z_regb_used_o;
  logic z_regc_used_o;
  logic z_reg_fp_a_o;
  logic z_reg_fp_b_o;
  logic z_reg_fp_c_o;
  logic z_reg_fp_d_o;
  logic [ 0:0] z_bmask_a_mux_o;
  logic [ 1:0] z_bmask_b_mux_o;
  logic z_alu_bmask_a_mux_sel_o;
  logic z_alu_bmask_b_mux_sel_o;
  logic z_alu_en_o;
  alu_opcode_e z_alu_operator_o;
  logic [2:0] z_alu_op_a_mux_sel_o;
  logic [2:0] z_alu_op_b_mux_sel_o;
  logic [1:0] z_alu_op_c_mux_sel_o;
  logic z_alu_vec_o;
  logic [2:0] z_alu_vec_mode_o;
  logic z_scalar_replication_o;
  logic z_scalar_replication_c_o;
  logic [0:0] z_imm_a_mux_sel_o;
  logic [3:0] z_imm_b_mux_sel_o;
  logic [1:0] z_regc_mux_o;
  logic z_is_clpx_o;
  logic z_is_subrot_o;
  mul_opcode_e z_mult_operator_o;
  logic z_mult_int_en_o;
  logic z_mult_dot_en_o;
  logic [0:0] z_mult_imm_mux_o;
  logic z_mult_sel_subword_o;
  logic [1:0] z_mult_signed_mode_o;
  logic [1:0] z_mult_dot_signed_o;
  logic [cv32e40p_fpu_pkg::FP_FORMAT_BITS-1:0] z_fpu_dst_fmt_o;
  logic [cv32e40p_fpu_pkg::FP_FORMAT_BITS-1:0] z_fpu_src_fmt_o;
  logic [cv32e40p_fpu_pkg::INT_FORMAT_BITS-1:0] z_fpu_int_fmt_o;
  logic z_apu_en_o;
  logic [APU_WOP_CPU-1:0] z_apu_op_o;
  logic [1:0] z_apu_lat_o;
  logic [2:0] z_fp_rnd_mode_o;
  logic z_regfile_mem_we_o;
  logic z_regfile_alu_we_o;
  logic z_regfile_alu_we_dec_o;
  logic z_regfile_alu_waddr_sel_o;
  logic z_csr_access_o;
  logic z_csr_status_o;
  csr_opcode_e z_csr_op_o;
  logic z_data_req_o;
  logic z_data_we_o;
  logic z_prepost_useincr_o;
  logic [1:0] z_data_type_o;
  logic [1:0] z_data_sign_extension_o;
  logic [1:0] z_data_reg_offset_o;
  logic z_data_load_event_o;
  logic [5:0] z_atop_o;
  logic [2:0] z_hwlp_we_o;
  logic [1:0] z_hwlp_target_mux_sel_o;
  logic [1:0] z_hwlp_start_mux_sel_o;
  logic z_hwlp_cnt_mux_sel_o;
  logic [1:0] z_ctrl_transfer_insn_in_dec_o;
  logic [1:0] z_ctrl_transfer_insn_in_id_o;
  logic [1:0] z_ctrl_transfer_target_mux_sel_o;
`ifdef NN_BASELINE_RED
  cv32e40p_decoder_baseline #(.COREV_PULP(1)) dut (
    .deassert_we_i(deassert),
    .instr_rdata_i(instr),
    .illegal_c_insn_i(1'b0),
    .fs_off_i(1'b0),
    .frm_i(3'b0),
    .current_priv_lvl_i(PRIV_LVL_M),
    .debug_mode_i(1'b0),
    .debug_wfi_no_sleep_i(1'b0),
    .mcounteren_i(32'b0),
    .illegal_insn_o(d_illegal_insn_o),
    .ebrk_insn_o(d_ebrk_insn_o),
    .mret_insn_o(d_mret_insn_o),
    .uret_insn_o(d_uret_insn_o),
    .dret_insn_o(d_dret_insn_o),
    .mret_dec_o(d_mret_dec_o),
    .uret_dec_o(d_uret_dec_o),
    .dret_dec_o(d_dret_dec_o),
    .ecall_insn_o(d_ecall_insn_o),
    .wfi_o(d_wfi_o),
    .fencei_insn_o(d_fencei_insn_o),
    .rega_used_o(d_rega_used_o),
    .regb_used_o(d_regb_used_o),
    .regc_used_o(d_regc_used_o),
    .reg_fp_a_o(d_reg_fp_a_o),
    .reg_fp_b_o(d_reg_fp_b_o),
    .reg_fp_c_o(d_reg_fp_c_o),
    .reg_fp_d_o(d_reg_fp_d_o),
    .bmask_a_mux_o(d_bmask_a_mux_o),
    .bmask_b_mux_o(d_bmask_b_mux_o),
    .alu_bmask_a_mux_sel_o(d_alu_bmask_a_mux_sel_o),
    .alu_bmask_b_mux_sel_o(d_alu_bmask_b_mux_sel_o),
    .alu_en_o(d_alu_en_o),
    .alu_operator_o(d_alu_operator_o),
    .alu_op_a_mux_sel_o(d_alu_op_a_mux_sel_o),
    .alu_op_b_mux_sel_o(d_alu_op_b_mux_sel_o),
    .alu_op_c_mux_sel_o(d_alu_op_c_mux_sel_o),
    .alu_vec_o(d_alu_vec_o),
    .alu_vec_mode_o(d_alu_vec_mode_o),
    .scalar_replication_o(d_scalar_replication_o),
    .scalar_replication_c_o(d_scalar_replication_c_o),
    .imm_a_mux_sel_o(d_imm_a_mux_sel_o),
    .imm_b_mux_sel_o(d_imm_b_mux_sel_o),
    .regc_mux_o(d_regc_mux_o),
    .is_clpx_o(d_is_clpx_o),
    .is_subrot_o(d_is_subrot_o),
    .mult_operator_o(d_mult_operator_o),
    .mult_int_en_o(d_mult_int_en_o),
    .mult_dot_en_o(d_mult_dot_en_o),
    .mult_imm_mux_o(d_mult_imm_mux_o),
    .mult_sel_subword_o(d_mult_sel_subword_o),
    .mult_signed_mode_o(d_mult_signed_mode_o),
    .mult_dot_signed_o(d_mult_dot_signed_o),
    .fpu_dst_fmt_o(d_fpu_dst_fmt_o),
    .fpu_src_fmt_o(d_fpu_src_fmt_o),
    .fpu_int_fmt_o(d_fpu_int_fmt_o),
    .apu_en_o(d_apu_en_o),
    .apu_op_o(d_apu_op_o),
    .apu_lat_o(d_apu_lat_o),
    .fp_rnd_mode_o(d_fp_rnd_mode_o),
    .regfile_mem_we_o(d_regfile_mem_we_o),
    .regfile_alu_we_o(d_regfile_alu_we_o),
    .regfile_alu_we_dec_o(d_regfile_alu_we_dec_o),
    .regfile_alu_waddr_sel_o(d_regfile_alu_waddr_sel_o),
    .csr_access_o(d_csr_access_o),
    .csr_status_o(d_csr_status_o),
    .csr_op_o(d_csr_op_o),
    .data_req_o(d_data_req_o),
    .data_we_o(d_data_we_o),
    .prepost_useincr_o(d_prepost_useincr_o),
    .data_type_o(d_data_type_o),
    .data_sign_extension_o(d_data_sign_extension_o),
    .data_reg_offset_o(d_data_reg_offset_o),
    .data_load_event_o(d_data_load_event_o),
    .atop_o(d_atop_o),
    .hwlp_we_o(d_hwlp_we_o),
    .hwlp_target_mux_sel_o(d_hwlp_target_mux_sel_o),
    .hwlp_start_mux_sel_o(d_hwlp_start_mux_sel_o),
    .hwlp_cnt_mux_sel_o(d_hwlp_cnt_mux_sel_o),
    .ctrl_transfer_insn_in_dec_o(d_ctrl_transfer_insn_in_dec_o),
    .ctrl_transfer_insn_in_id_o(d_ctrl_transfer_insn_in_id_o),
    .ctrl_transfer_target_mux_sel_o(d_ctrl_transfer_target_mux_sel_o));
`else
  cv32e40p_decoder #(.COREV_PULP(1), .COREV_XPULPNN(1)) dut (
    .qnt_dec_o(d_qnt_dec_o), .qnt_q4_o(d_qnt_q4_o), .qnt_en_o(d_qnt_en_o),
    .deassert_we_i(deassert),
    .instr_rdata_i(instr),
    .illegal_c_insn_i(1'b0),
    .fs_off_i(1'b0),
    .frm_i(3'b0),
    .current_priv_lvl_i(PRIV_LVL_M),
    .debug_mode_i(1'b0),
    .debug_wfi_no_sleep_i(1'b0),
    .mcounteren_i(32'b0),
    .illegal_insn_o(d_illegal_insn_o),
    .ebrk_insn_o(d_ebrk_insn_o),
    .mret_insn_o(d_mret_insn_o),
    .uret_insn_o(d_uret_insn_o),
    .dret_insn_o(d_dret_insn_o),
    .mret_dec_o(d_mret_dec_o),
    .uret_dec_o(d_uret_dec_o),
    .dret_dec_o(d_dret_dec_o),
    .ecall_insn_o(d_ecall_insn_o),
    .wfi_o(d_wfi_o),
    .fencei_insn_o(d_fencei_insn_o),
    .rega_used_o(d_rega_used_o),
    .regb_used_o(d_regb_used_o),
    .regc_used_o(d_regc_used_o),
    .reg_fp_a_o(d_reg_fp_a_o),
    .reg_fp_b_o(d_reg_fp_b_o),
    .reg_fp_c_o(d_reg_fp_c_o),
    .reg_fp_d_o(d_reg_fp_d_o),
    .bmask_a_mux_o(d_bmask_a_mux_o),
    .bmask_b_mux_o(d_bmask_b_mux_o),
    .alu_bmask_a_mux_sel_o(d_alu_bmask_a_mux_sel_o),
    .alu_bmask_b_mux_sel_o(d_alu_bmask_b_mux_sel_o),
    .alu_en_o(d_alu_en_o),
    .alu_operator_o(d_alu_operator_o),
    .alu_op_a_mux_sel_o(d_alu_op_a_mux_sel_o),
    .alu_op_b_mux_sel_o(d_alu_op_b_mux_sel_o),
    .alu_op_c_mux_sel_o(d_alu_op_c_mux_sel_o),
    .alu_vec_o(d_alu_vec_o),
    .alu_vec_mode_o(d_alu_vec_mode_o),
    .scalar_replication_o(d_scalar_replication_o),
    .scalar_replication_c_o(d_scalar_replication_c_o),
    .imm_a_mux_sel_o(d_imm_a_mux_sel_o),
    .imm_b_mux_sel_o(d_imm_b_mux_sel_o),
    .regc_mux_o(d_regc_mux_o),
    .is_clpx_o(d_is_clpx_o),
    .is_subrot_o(d_is_subrot_o),
    .mult_operator_o(d_mult_operator_o),
    .mult_int_en_o(d_mult_int_en_o),
    .mult_dot_en_o(d_mult_dot_en_o),
    .mult_imm_mux_o(d_mult_imm_mux_o),
    .mult_sel_subword_o(d_mult_sel_subword_o),
    .mult_signed_mode_o(d_mult_signed_mode_o),
    .mult_dot_signed_o(d_mult_dot_signed_o),
    .fpu_dst_fmt_o(d_fpu_dst_fmt_o),
    .fpu_src_fmt_o(d_fpu_src_fmt_o),
    .fpu_int_fmt_o(d_fpu_int_fmt_o),
    .apu_en_o(d_apu_en_o),
    .apu_op_o(d_apu_op_o),
    .apu_lat_o(d_apu_lat_o),
    .fp_rnd_mode_o(d_fp_rnd_mode_o),
    .regfile_mem_we_o(d_regfile_mem_we_o),
    .regfile_alu_we_o(d_regfile_alu_we_o),
    .regfile_alu_we_dec_o(d_regfile_alu_we_dec_o),
    .regfile_alu_waddr_sel_o(d_regfile_alu_waddr_sel_o),
    .csr_access_o(d_csr_access_o),
    .csr_status_o(d_csr_status_o),
    .csr_op_o(d_csr_op_o),
    .data_req_o(d_data_req_o),
    .data_we_o(d_data_we_o),
    .prepost_useincr_o(d_prepost_useincr_o),
    .data_type_o(d_data_type_o),
    .data_sign_extension_o(d_data_sign_extension_o),
    .data_reg_offset_o(d_data_reg_offset_o),
    .data_load_event_o(d_data_load_event_o),
    .atop_o(d_atop_o),
    .hwlp_we_o(d_hwlp_we_o),
    .hwlp_target_mux_sel_o(d_hwlp_target_mux_sel_o),
    .hwlp_start_mux_sel_o(d_hwlp_start_mux_sel_o),
    .hwlp_cnt_mux_sel_o(d_hwlp_cnt_mux_sel_o),
    .ctrl_transfer_insn_in_dec_o(d_ctrl_transfer_insn_in_dec_o),
    .ctrl_transfer_insn_in_id_o(d_ctrl_transfer_insn_in_id_o),
    .ctrl_transfer_target_mux_sel_o(d_ctrl_transfer_target_mux_sel_o));
  cv32e40p_decoder_baseline #(.COREV_PULP(1)) baseline (
    .deassert_we_i(deassert),
    .instr_rdata_i(instr),
    .illegal_c_insn_i(1'b0),
    .fs_off_i(1'b0),
    .frm_i(3'b0),
    .current_priv_lvl_i(PRIV_LVL_M),
    .debug_mode_i(1'b0),
    .debug_wfi_no_sleep_i(1'b0),
    .mcounteren_i(32'b0),
    .illegal_insn_o(b_illegal_insn_o),
    .ebrk_insn_o(b_ebrk_insn_o),
    .mret_insn_o(b_mret_insn_o),
    .uret_insn_o(b_uret_insn_o),
    .dret_insn_o(b_dret_insn_o),
    .mret_dec_o(b_mret_dec_o),
    .uret_dec_o(b_uret_dec_o),
    .dret_dec_o(b_dret_dec_o),
    .ecall_insn_o(b_ecall_insn_o),
    .wfi_o(b_wfi_o),
    .fencei_insn_o(b_fencei_insn_o),
    .rega_used_o(b_rega_used_o),
    .regb_used_o(b_regb_used_o),
    .regc_used_o(b_regc_used_o),
    .reg_fp_a_o(b_reg_fp_a_o),
    .reg_fp_b_o(b_reg_fp_b_o),
    .reg_fp_c_o(b_reg_fp_c_o),
    .reg_fp_d_o(b_reg_fp_d_o),
    .bmask_a_mux_o(b_bmask_a_mux_o),
    .bmask_b_mux_o(b_bmask_b_mux_o),
    .alu_bmask_a_mux_sel_o(b_alu_bmask_a_mux_sel_o),
    .alu_bmask_b_mux_sel_o(b_alu_bmask_b_mux_sel_o),
    .alu_en_o(b_alu_en_o),
    .alu_operator_o(b_alu_operator_o),
    .alu_op_a_mux_sel_o(b_alu_op_a_mux_sel_o),
    .alu_op_b_mux_sel_o(b_alu_op_b_mux_sel_o),
    .alu_op_c_mux_sel_o(b_alu_op_c_mux_sel_o),
    .alu_vec_o(b_alu_vec_o),
    .alu_vec_mode_o(b_alu_vec_mode_o),
    .scalar_replication_o(b_scalar_replication_o),
    .scalar_replication_c_o(b_scalar_replication_c_o),
    .imm_a_mux_sel_o(b_imm_a_mux_sel_o),
    .imm_b_mux_sel_o(b_imm_b_mux_sel_o),
    .regc_mux_o(b_regc_mux_o),
    .is_clpx_o(b_is_clpx_o),
    .is_subrot_o(b_is_subrot_o),
    .mult_operator_o(b_mult_operator_o),
    .mult_int_en_o(b_mult_int_en_o),
    .mult_dot_en_o(b_mult_dot_en_o),
    .mult_imm_mux_o(b_mult_imm_mux_o),
    .mult_sel_subword_o(b_mult_sel_subword_o),
    .mult_signed_mode_o(b_mult_signed_mode_o),
    .mult_dot_signed_o(b_mult_dot_signed_o),
    .fpu_dst_fmt_o(b_fpu_dst_fmt_o),
    .fpu_src_fmt_o(b_fpu_src_fmt_o),
    .fpu_int_fmt_o(b_fpu_int_fmt_o),
    .apu_en_o(b_apu_en_o),
    .apu_op_o(b_apu_op_o),
    .apu_lat_o(b_apu_lat_o),
    .fp_rnd_mode_o(b_fp_rnd_mode_o),
    .regfile_mem_we_o(b_regfile_mem_we_o),
    .regfile_alu_we_o(b_regfile_alu_we_o),
    .regfile_alu_we_dec_o(b_regfile_alu_we_dec_o),
    .regfile_alu_waddr_sel_o(b_regfile_alu_waddr_sel_o),
    .csr_access_o(b_csr_access_o),
    .csr_status_o(b_csr_status_o),
    .csr_op_o(b_csr_op_o),
    .data_req_o(b_data_req_o),
    .data_we_o(b_data_we_o),
    .prepost_useincr_o(b_prepost_useincr_o),
    .data_type_o(b_data_type_o),
    .data_sign_extension_o(b_data_sign_extension_o),
    .data_reg_offset_o(b_data_reg_offset_o),
    .data_load_event_o(b_data_load_event_o),
    .atop_o(b_atop_o),
    .hwlp_we_o(b_hwlp_we_o),
    .hwlp_target_mux_sel_o(b_hwlp_target_mux_sel_o),
    .hwlp_start_mux_sel_o(b_hwlp_start_mux_sel_o),
    .hwlp_cnt_mux_sel_o(b_hwlp_cnt_mux_sel_o),
    .ctrl_transfer_insn_in_dec_o(b_ctrl_transfer_insn_in_dec_o),
    .ctrl_transfer_insn_in_id_o(b_ctrl_transfer_insn_in_id_o),
    .ctrl_transfer_target_mux_sel_o(b_ctrl_transfer_target_mux_sel_o));
  cv32e40p_decoder #(.COREV_PULP(1), .COREV_XPULPNN(0)) disabled_dut (
    .qnt_dec_o(z_qnt_dec_o), .qnt_q4_o(z_qnt_q4_o), .qnt_en_o(z_qnt_en_o),
    .deassert_we_i(deassert),
    .instr_rdata_i(instr),
    .illegal_c_insn_i(1'b0),
    .fs_off_i(1'b0),
    .frm_i(3'b0),
    .current_priv_lvl_i(PRIV_LVL_M),
    .debug_mode_i(1'b0),
    .debug_wfi_no_sleep_i(1'b0),
    .mcounteren_i(32'b0),
    .illegal_insn_o(z_illegal_insn_o),
    .ebrk_insn_o(z_ebrk_insn_o),
    .mret_insn_o(z_mret_insn_o),
    .uret_insn_o(z_uret_insn_o),
    .dret_insn_o(z_dret_insn_o),
    .mret_dec_o(z_mret_dec_o),
    .uret_dec_o(z_uret_dec_o),
    .dret_dec_o(z_dret_dec_o),
    .ecall_insn_o(z_ecall_insn_o),
    .wfi_o(z_wfi_o),
    .fencei_insn_o(z_fencei_insn_o),
    .rega_used_o(z_rega_used_o),
    .regb_used_o(z_regb_used_o),
    .regc_used_o(z_regc_used_o),
    .reg_fp_a_o(z_reg_fp_a_o),
    .reg_fp_b_o(z_reg_fp_b_o),
    .reg_fp_c_o(z_reg_fp_c_o),
    .reg_fp_d_o(z_reg_fp_d_o),
    .bmask_a_mux_o(z_bmask_a_mux_o),
    .bmask_b_mux_o(z_bmask_b_mux_o),
    .alu_bmask_a_mux_sel_o(z_alu_bmask_a_mux_sel_o),
    .alu_bmask_b_mux_sel_o(z_alu_bmask_b_mux_sel_o),
    .alu_en_o(z_alu_en_o),
    .alu_operator_o(z_alu_operator_o),
    .alu_op_a_mux_sel_o(z_alu_op_a_mux_sel_o),
    .alu_op_b_mux_sel_o(z_alu_op_b_mux_sel_o),
    .alu_op_c_mux_sel_o(z_alu_op_c_mux_sel_o),
    .alu_vec_o(z_alu_vec_o),
    .alu_vec_mode_o(z_alu_vec_mode_o),
    .scalar_replication_o(z_scalar_replication_o),
    .scalar_replication_c_o(z_scalar_replication_c_o),
    .imm_a_mux_sel_o(z_imm_a_mux_sel_o),
    .imm_b_mux_sel_o(z_imm_b_mux_sel_o),
    .regc_mux_o(z_regc_mux_o),
    .is_clpx_o(z_is_clpx_o),
    .is_subrot_o(z_is_subrot_o),
    .mult_operator_o(z_mult_operator_o),
    .mult_int_en_o(z_mult_int_en_o),
    .mult_dot_en_o(z_mult_dot_en_o),
    .mult_imm_mux_o(z_mult_imm_mux_o),
    .mult_sel_subword_o(z_mult_sel_subword_o),
    .mult_signed_mode_o(z_mult_signed_mode_o),
    .mult_dot_signed_o(z_mult_dot_signed_o),
    .fpu_dst_fmt_o(z_fpu_dst_fmt_o),
    .fpu_src_fmt_o(z_fpu_src_fmt_o),
    .fpu_int_fmt_o(z_fpu_int_fmt_o),
    .apu_en_o(z_apu_en_o),
    .apu_op_o(z_apu_op_o),
    .apu_lat_o(z_apu_lat_o),
    .fp_rnd_mode_o(z_fp_rnd_mode_o),
    .regfile_mem_we_o(z_regfile_mem_we_o),
    .regfile_alu_we_o(z_regfile_alu_we_o),
    .regfile_alu_we_dec_o(z_regfile_alu_we_dec_o),
    .regfile_alu_waddr_sel_o(z_regfile_alu_waddr_sel_o),
    .csr_access_o(z_csr_access_o),
    .csr_status_o(z_csr_status_o),
    .csr_op_o(z_csr_op_o),
    .data_req_o(z_data_req_o),
    .data_we_o(z_data_we_o),
    .prepost_useincr_o(z_prepost_useincr_o),
    .data_type_o(z_data_type_o),
    .data_sign_extension_o(z_data_sign_extension_o),
    .data_reg_offset_o(z_data_reg_offset_o),
    .data_load_event_o(z_data_load_event_o),
    .atop_o(z_atop_o),
    .hwlp_we_o(z_hwlp_we_o),
    .hwlp_target_mux_sel_o(z_hwlp_target_mux_sel_o),
    .hwlp_start_mux_sel_o(z_hwlp_start_mux_sel_o),
    .hwlp_cnt_mux_sel_o(z_hwlp_cnt_mux_sel_o),
    .ctrl_transfer_insn_in_dec_o(z_ctrl_transfer_insn_in_dec_o),
    .ctrl_transfer_insn_in_id_o(z_ctrl_transfer_insn_in_id_o),
    .ctrl_transfer_target_mux_sel_o(z_ctrl_transfer_target_mux_sel_o));
  cv32e40p_decoder #(.COREV_PULP(0), .COREV_XPULPNN(0)) no_pulp (
    .deassert_we_i(deassert), .instr_rdata_i(instr), .illegal_c_insn_i(1'b0),
    .fs_off_i(1'b0), .frm_i(3'b0), .current_priv_lvl_i(PRIV_LVL_M),
    .debug_mode_i(1'b0), .debug_wfi_no_sleep_i(1'b0), .mcounteren_i(32'b0),
    .illegal_insn_o(no_pulp_illegal));
`endif
  function automatic bit is_new(input integer f);
    case(f)
      30,31,33,35,37,39,41,43,44,45,47,49,51,53,55,57,58,59,61: is_new=1;
      default: is_new=0;
    endcase
  endfunction
  function automatic bit is_legacy(input integer f);
    case(f)
      30,31,33,35,37,39,41,43,44,45,47,49,51,53,55,57,58,59,61,63: is_legacy=0;
      default: is_legacy=1;
    endcase
  endfunction
  initial begin
    // This exact assertion fails on the frozen decoder before integration.
    instr=32'h7800007b; #1;
    if(d_illegal_insn_o !== 0) $fatal(1,"New pv.add.n decoded illegal: arithmetic extension missing");
`ifndef NN_BASELINE_RED
    for(integer f=0; f<64; f++) begin
      for(integer b25=0; b25<2; b25++) begin
        for(integer form=0; form<8; form++) begin
          for(integer rs2=0; rs2<32; rs2++) begin
            bit expected_legal;
            instr=(f<<26)|(b25<<25)|(rs2<<20)|(11<<15)|(form<<12)|(10<<7)|32'h7b;
            #1;
            expected_legal=is_new(f) && b25==0 && (form==0 || form==1 || form==4 || form==5);
            if(f==49) expected_legal=expected_legal && form<2 && rs2==0;
            if(f==61) expected_legal=expected_legal && form<2;
            if(no_pulp_illegal !== 1) $fatal(1,"PULP disabled accepted custom3 %h",instr);
            if(z_qnt_dec_o !== 0 || z_qnt_en_o !== 0) $fatal(1,"Disabled qnt class/enable %h",instr);
            if(d_qnt_dec_o !== (f==61 && expected_legal) || d_qnt_en_o !== (f==61 && expected_legal)) $fatal(1,"qnt classification/enable mismatch %h",instr);
            if(is_new(f) || f==61 || f==63) begin
              if(d_illegal_insn_o !== !expected_legal) $fatal(1,"Legality mismatch word=%h expected=%b",instr,expected_legal);
              if(z_illegal_insn_o !== 1) $fatal(1,"Disabled extension accepted word=%h",instr);
              if(expected_legal) begin
                legal_count++;
                if(f==61) begin
                  if(d_qnt_q4_o !== (form==0) || d_alu_en_o !== 0 || d_mult_dot_en_o !== 0 ||
                     d_rega_used_o !== 1 || d_regb_used_o !== 1 || d_scalar_replication_o !== 0)
                    $fatal(1,"qnt precision/operand/execution control mismatch %h",instr);
                end else begin
                if(d_alu_vec_mode_o !== (form%2 ? 3'b101 : 3'b100)) $fatal(1,"Mode mismatch word=%h",instr);
                if(d_scalar_replication_o !== (form>=4)) $fatal(1,"Broadcast mismatch word=%h",instr);
                if(d_rega_used_o !== 1 || d_regfile_alu_we_o !== 1) $fatal(1,"Operand/write enable mismatch word=%h",instr);
                if(d_regb_used_o !== (f!=49)) $fatal(1,"B dependency mismatch word=%h",instr);
                if(f>=51) begin
                  if(d_alu_en_o !== 0 || d_mult_dot_en_o !== 1) $fatal(1,"DOT enable mismatch %h",instr);
                  if(d_mult_operator_o !== (form%2 ? mul_opcode_e'(8) : mul_opcode_e'(7))) $fatal(1,"DOT precision mismatch %h",instr);
                  if(d_mult_dot_signed_o !== ((f==51 || f==57) ? 2'b00 : (f==53 || f==58) ? 2'b01 : 2'b11)) $fatal(1,"DOT signedness mismatch %h",instr);
                  if(d_regc_used_o !== (f>=57)) $fatal(1,"DOT accumulator dependency mismatch %h",instr);
                  if(d_regc_mux_o !== (f>=57 ? REGC_RD : REGC_ZERO)) $fatal(1,"DOT accumulator source mismatch %h",instr);
                end else begin
                  if(d_alu_en_o !== 1 || d_mult_dot_en_o !== 0) $fatal(1,"ALU enable mismatch %h",instr);
                  if(d_bmask_b_mux_o !== ((f==33 || f==35) ? BMASK_B_ONE : BMASK_B_ZERO)) $fatal(1,"Average select mismatch %h",instr);
                end
                end
              end
            end else if(is_legacy(f)) begin
              if({d_illegal_insn_o, d_ebrk_insn_o, d_mret_insn_o, d_uret_insn_o, d_dret_insn_o, d_mret_dec_o, d_uret_dec_o, d_dret_dec_o, d_ecall_insn_o, d_wfi_o, d_fencei_insn_o, d_rega_used_o, d_regb_used_o, d_regc_used_o, d_reg_fp_a_o, d_reg_fp_b_o, d_reg_fp_c_o, d_reg_fp_d_o, d_bmask_a_mux_o, d_bmask_b_mux_o, d_alu_bmask_a_mux_sel_o, d_alu_bmask_b_mux_sel_o, d_alu_en_o, d_alu_operator_o, d_alu_op_a_mux_sel_o, d_alu_op_b_mux_sel_o, d_alu_op_c_mux_sel_o, d_alu_vec_o, d_alu_vec_mode_o[1:0], d_scalar_replication_o, d_scalar_replication_c_o, d_imm_a_mux_sel_o, d_imm_b_mux_sel_o, d_regc_mux_o, d_is_clpx_o, d_is_subrot_o, d_mult_operator_o, d_mult_int_en_o, d_mult_dot_en_o, d_mult_imm_mux_o, d_mult_sel_subword_o, d_mult_signed_mode_o, d_mult_dot_signed_o, d_fpu_dst_fmt_o, d_fpu_src_fmt_o, d_fpu_int_fmt_o, d_apu_en_o, d_apu_op_o, d_apu_lat_o, d_fp_rnd_mode_o, d_regfile_mem_we_o, d_regfile_alu_we_o, d_regfile_alu_we_dec_o, d_regfile_alu_waddr_sel_o, d_csr_access_o, d_csr_status_o, d_csr_op_o, d_data_req_o, d_data_we_o, d_prepost_useincr_o, d_data_type_o, d_data_sign_extension_o, d_data_reg_offset_o, d_data_load_event_o, d_atop_o, d_hwlp_we_o, d_hwlp_target_mux_sel_o, d_hwlp_start_mux_sel_o, d_hwlp_cnt_mux_sel_o, d_ctrl_transfer_insn_in_dec_o, d_ctrl_transfer_insn_in_id_o, d_ctrl_transfer_target_mux_sel_o} !== {b_illegal_insn_o, b_ebrk_insn_o, b_mret_insn_o, b_uret_insn_o, b_dret_insn_o, b_mret_dec_o, b_uret_dec_o, b_dret_dec_o, b_ecall_insn_o, b_wfi_o, b_fencei_insn_o, b_rega_used_o, b_regb_used_o, b_regc_used_o, b_reg_fp_a_o, b_reg_fp_b_o, b_reg_fp_c_o, b_reg_fp_d_o, b_bmask_a_mux_o, b_bmask_b_mux_o, b_alu_bmask_a_mux_sel_o, b_alu_bmask_b_mux_sel_o, b_alu_en_o, b_alu_operator_o, b_alu_op_a_mux_sel_o, b_alu_op_b_mux_sel_o, b_alu_op_c_mux_sel_o, b_alu_vec_o, b_alu_vec_mode_o, b_scalar_replication_o, b_scalar_replication_c_o, b_imm_a_mux_sel_o, b_imm_b_mux_sel_o, b_regc_mux_o, b_is_clpx_o, b_is_subrot_o, b_mult_operator_o, b_mult_int_en_o, b_mult_dot_en_o, b_mult_imm_mux_o, b_mult_sel_subword_o, b_mult_signed_mode_o, b_mult_dot_signed_o, b_fpu_dst_fmt_o, b_fpu_src_fmt_o, b_fpu_int_fmt_o, b_apu_en_o, b_apu_op_o, b_apu_lat_o, b_fp_rnd_mode_o, b_regfile_mem_we_o, b_regfile_alu_we_o, b_regfile_alu_we_dec_o, b_regfile_alu_waddr_sel_o, b_csr_access_o, b_csr_status_o, b_csr_op_o, b_data_req_o, b_data_we_o, b_prepost_useincr_o, b_data_type_o, b_data_sign_extension_o, b_data_reg_offset_o, b_data_load_event_o, b_atop_o, b_hwlp_we_o, b_hwlp_target_mux_sel_o, b_hwlp_start_mux_sel_o, b_hwlp_cnt_mux_sel_o, b_ctrl_transfer_insn_in_dec_o, b_ctrl_transfer_insn_in_id_o, b_ctrl_transfer_target_mux_sel_o}) $fatal(1,"Enabled legacy control mismatch word=%h",instr);
              if({z_illegal_insn_o, z_ebrk_insn_o, z_mret_insn_o, z_uret_insn_o, z_dret_insn_o, z_mret_dec_o, z_uret_dec_o, z_dret_dec_o, z_ecall_insn_o, z_wfi_o, z_fencei_insn_o, z_rega_used_o, z_regb_used_o, z_regc_used_o, z_reg_fp_a_o, z_reg_fp_b_o, z_reg_fp_c_o, z_reg_fp_d_o, z_bmask_a_mux_o, z_bmask_b_mux_o, z_alu_bmask_a_mux_sel_o, z_alu_bmask_b_mux_sel_o, z_alu_en_o, z_alu_operator_o, z_alu_op_a_mux_sel_o, z_alu_op_b_mux_sel_o, z_alu_op_c_mux_sel_o, z_alu_vec_o, z_alu_vec_mode_o[1:0], z_scalar_replication_o, z_scalar_replication_c_o, z_imm_a_mux_sel_o, z_imm_b_mux_sel_o, z_regc_mux_o, z_is_clpx_o, z_is_subrot_o, z_mult_operator_o, z_mult_int_en_o, z_mult_dot_en_o, z_mult_imm_mux_o, z_mult_sel_subword_o, z_mult_signed_mode_o, z_mult_dot_signed_o, z_fpu_dst_fmt_o, z_fpu_src_fmt_o, z_fpu_int_fmt_o, z_apu_en_o, z_apu_op_o, z_apu_lat_o, z_fp_rnd_mode_o, z_regfile_mem_we_o, z_regfile_alu_we_o, z_regfile_alu_we_dec_o, z_regfile_alu_waddr_sel_o, z_csr_access_o, z_csr_status_o, z_csr_op_o, z_data_req_o, z_data_we_o, z_prepost_useincr_o, z_data_type_o, z_data_sign_extension_o, z_data_reg_offset_o, z_data_load_event_o, z_atop_o, z_hwlp_we_o, z_hwlp_target_mux_sel_o, z_hwlp_start_mux_sel_o, z_hwlp_cnt_mux_sel_o, z_ctrl_transfer_insn_in_dec_o, z_ctrl_transfer_insn_in_id_o, z_ctrl_transfer_target_mux_sel_o} !== {b_illegal_insn_o, b_ebrk_insn_o, b_mret_insn_o, b_uret_insn_o, b_dret_insn_o, b_mret_dec_o, b_uret_dec_o, b_dret_dec_o, b_ecall_insn_o, b_wfi_o, b_fencei_insn_o, b_rega_used_o, b_regb_used_o, b_regc_used_o, b_reg_fp_a_o, b_reg_fp_b_o, b_reg_fp_c_o, b_reg_fp_d_o, b_bmask_a_mux_o, b_bmask_b_mux_o, b_alu_bmask_a_mux_sel_o, b_alu_bmask_b_mux_sel_o, b_alu_en_o, b_alu_operator_o, b_alu_op_a_mux_sel_o, b_alu_op_b_mux_sel_o, b_alu_op_c_mux_sel_o, b_alu_vec_o, b_alu_vec_mode_o, b_scalar_replication_o, b_scalar_replication_c_o, b_imm_a_mux_sel_o, b_imm_b_mux_sel_o, b_regc_mux_o, b_is_clpx_o, b_is_subrot_o, b_mult_operator_o, b_mult_int_en_o, b_mult_dot_en_o, b_mult_imm_mux_o, b_mult_sel_subword_o, b_mult_signed_mode_o, b_mult_dot_signed_o, b_fpu_dst_fmt_o, b_fpu_src_fmt_o, b_fpu_int_fmt_o, b_apu_en_o, b_apu_op_o, b_apu_lat_o, b_fp_rnd_mode_o, b_regfile_mem_we_o, b_regfile_alu_we_o, b_regfile_alu_we_dec_o, b_regfile_alu_waddr_sel_o, b_csr_access_o, b_csr_status_o, b_csr_op_o, b_data_req_o, b_data_we_o, b_prepost_useincr_o, b_data_type_o, b_data_sign_extension_o, b_data_reg_offset_o, b_data_load_event_o, b_atop_o, b_hwlp_we_o, b_hwlp_target_mux_sel_o, b_hwlp_start_mux_sel_o, b_hwlp_cnt_mux_sel_o, b_ctrl_transfer_insn_in_dec_o, b_ctrl_transfer_insn_in_id_o, b_ctrl_transfer_target_mux_sel_o}) $fatal(1,"Disabled legacy control mismatch word=%h",instr);
            end
            tests++;
          end
        end
      end
    end
    if(tests!=32768 || legal_count!=2242) $fatal(1,"Incomplete coverage tests=%0d legal=%0d",tests,legal_count);
    // Explicit stalled decode checks the existing deasserted side effect enables.
    deassert=1; instr=32'he400007b; #1;
    if(d_alu_en_o || d_mult_dot_en_o || d_regfile_alu_we_o || d_data_req_o) $fatal(1,"Stall side effects");
    for(integer qform=0; qform<2; qform++) begin
      instr=32'hf400007b | (qform<<12); #1;
      if(d_qnt_dec_o !== 1 || d_qnt_en_o !== 0 || d_qnt_q4_o !== (qform==0))
        $fatal(1,"Stalled qnt must preserve raw class/precision and suppress enable %h",instr);
      if(d_alu_en_o || d_mult_dot_en_o || d_regfile_alu_we_o || d_data_req_o) $fatal(1,"Stalled qnt side effect");
    end
    instr=32'hf600007b; #1;
    if(d_qnt_dec_o || d_qnt_en_o) $fatal(1,"Malformed stalled qnt classified legal");
    $display("NN_DECODER_PASS count=%0d legal_selector_classes=%0d named_forms=72 legacy_compare=44",tests,legal_count);
`endif
    $finish;
  end
endmodule
