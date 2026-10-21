# No board pins or bitstream: compare identical OOC flows at the requested clock.
source [file join [file dirname [info script]] create_vivado_project.tcl]
set_param general.maxThreads 4
puts "FYP_STAGE_SYNTH_BEGIN"
flush stdout
if {[info exists fyp_synth_checkpoint] && $fyp_synth_checkpoint ne ""} {
  open_checkpoint $fyp_synth_checkpoint
  puts "FYP_REUSE_SYNTH $fyp_synth_checkpoint"
} else {
  synth_design -top $fyp_top -part xck26-sfvc784-2LV-c -mode out_of_context \
      -flatten_hierarchy rebuilt -generic $fyp_generics
}
create_clock -name fyp_clk -period $fyp_clock_ns [get_ports clk_i]
if {[llength [get_clocks fyp_clk]] != 1 ||
    [get_property PERIOD [get_clocks fyp_clk]] != $fyp_clock_ns} {
  error "OOC clock period was not applied"
}
write_checkpoint -force [file join $fyp_output synth.dcp]
report_utilization -file [file join $fyp_output utilization_synth.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -file [file join $fyp_output timing_synth.rpt]
puts "FYP_STAGE_SYNTH_DONE"
flush stdout
opt_design
puts "FYP_STAGE_PLACE_BEGIN"
flush stdout
place_design
phys_opt_design
puts "FYP_STAGE_ROUTE_BEGIN"
flush stdout
route_design
write_checkpoint -force [file join $fyp_output routed.dcp]
report_utilization -file [file join $fyp_output utilization_routed.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
    -file [file join $fyp_output timing_routed.rpt]
report_drc -file [file join $fyp_output drc.rpt]
report_clocks -file [file join $fyp_output clocks.rpt]
report_clock_utilization -file [file join $fyp_output clock_utilization.rpt]
set max_paths [get_timing_paths -delay_type max -max_paths 1]
set min_paths [get_timing_paths -delay_type min -max_paths 1]
set wns "unavailable"
set whs "unavailable"
if {[llength $max_paths]} { set wns [get_property SLACK [lindex $max_paths 0]] }
if {[llength $min_paths]} { set whs [get_property SLACK [lindex $min_paths 0]] }
set f [open [file join $fyp_output metrics.json] w]
puts $f "{\"stage\":\"$fyp_stage\",\"clock_period_ns\":$fyp_clock_ns,\"wns_ns\":\"$wns\",\"whs_ns\":\"$whs\",\"board_programming\":\"NOT_RUN\"}"
close $f
puts "FYP_STAGE_ROUTE_DONE WNS=$wns WHS=$whs"
flush stdout
close_project
exit 0
