# Full device implementation, not OOC. No external fabric I/O is required.
source [lindex $argv 0]
set_param general.maxThreads 4
create_project board $board_out/project -part xck26-sfvc784-2LV-c
add_files -norecurse $board_sources
set_property include_dirs $board_includes [get_filesets sources_1]
set defs [list SYNTHESIS]
if {$board_nn} {lappend defs FYP_OVERLAY}
set_property verilog_define $defs [get_filesets sources_1]
add_files -norecurse [list $board_out/imem.hex $board_out/dmem.hex]
set_property file_type {Memory Initialization Files} [get_files *.hex]

create_bd_design ps_clock
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.5 ps
set_property -dict [list CONFIG.PSU__USE__M_AXI_GP0 {0} CONFIG.PSU__USE__M_AXI_GP1 {0} \
    CONFIG.PSU__USE__M_AXI_GP2 {0} CONFIG.PSU__USE__S_AXI_GP0 {0} \
    CONFIG.PSU__USE__S_AXI_GP1 {0} CONFIG.PSU__USE__S_AXI_GP2 {0} \
    CONFIG.PSU__FPGA_PL0_ENABLE {1} CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {50} \
    CONFIG.PSU__PL_CLK0_BUF {TRUE}] [get_bd_cells ps]
make_bd_pins_external [get_bd_pins ps/pl_clk0]
make_bd_pins_external [get_bd_pins ps/pl_resetn0]
validate_bd_design
save_bd_design
generate_target all [get_files ps_clock.bd]
set wrappers [make_wrapper -files [get_files ps_clock.bd] -top]
add_files -norecurse $wrappers

create_ip -name vio -vendor xilinx.com -library ip -version 3.0 -module_name board_vio
set_property -dict [list CONFIG.C_NUM_PROBE_IN {7} CONFIG.C_NUM_PROBE_OUT {3} \
    CONFIG.C_PROBE_IN0_WIDTH {32} CONFIG.C_PROBE_IN1_WIDTH {32} \
    CONFIG.C_PROBE_IN2_WIDTH {32} CONFIG.C_PROBE_IN3_WIDTH {32} \
    CONFIG.C_PROBE_IN4_WIDTH {32} CONFIG.C_PROBE_IN5_WIDTH {32} CONFIG.C_PROBE_IN6_WIDTH {32} \
    CONFIG.C_PROBE_OUT0_WIDTH {1} CONFIG.C_PROBE_OUT0_INIT_VAL {0x1} \
    CONFIG.C_PROBE_OUT1_WIDTH {1} CONFIG.C_PROBE_OUT2_WIDTH {9}] [get_ips board_vio]
generate_target all [get_ips board_vio]
set_property top fyp_board_top [get_filesets sources_1]
set_property generic [list COREV_XPULPNN=$board_nn "BUILD_ID=32'h$board_build_id" \
    "IMEM_FILE=\"$board_out/imem.hex\"" "DMEM_FILE=\"$board_out/dmem.hex\""] [get_filesets sources_1]
update_compile_order -fileset sources_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "synthesis failed"}
open_run synth_1
set_property BITSTREAM.CONFIG.USR_ACCESS 0x$board_build_id [current_design]
# Persist the build identifier into implementation through a late XDC.
set fd [open $board_out/identity.xdc w]
puts $fd "set_property BITSTREAM.CONFIG.USR_ACCESS 0x$board_build_id \[current_design\]"
close $fd
add_files -fileset constrs_1 $board_out/identity.xdc
set_property used_in_synthesis false [get_files $board_out/identity.xdc]
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "implementation failed"}
open_run impl_1
report_timing_summary -file $board_out/timing.rpt
report_utilization -file $board_out/utilization.rpt
report_drc -file $board_out/drc.rpt
report_clocks -file $board_out/clocks.rpt
set setup [get_timing_paths -delay_type max -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
if {![llength $setup] || ![llength $hold]} {error "missing timing paths"}
set wns [get_property SLACK $setup]
set whs [get_property SLACK $hold]
if {$wns < 0 || $whs < 0} {error "timing failed WNS=$wns WHS=$whs"}
set violations [get_drc_violations -quiet -filter {SEVERITY == Error}]
if {[llength $violations]} {error "DRC errors: $violations"}
set_property BITSTREAM.CONFIG.USR_ACCESS 0x$board_build_id [current_design]
write_debug_probes -force $board_out/board.ltx
write_bitstream -force $board_out/board.bit
write_checkpoint -force $board_out/routed.dcp
set fd [open $board_out/implementation.json w]
puts $fd "{\"wns_ns\":$wns,\"whs_ns\":$whs,\"drc_errors\":0,\"build_id\":\"$board_build_id\"}"
close $fd
puts "BOARD_BUILD_PASS ID=$board_build_id WNS=$wns WHS=$whs"
exit
