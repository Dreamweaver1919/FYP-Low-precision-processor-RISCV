# Tighten generated PS clock constraint to the actual configured nominal 50 MHz.
# Reuse the routed design only if it meets this stricter constraint.
set out [file normalize [lindex $argv 0]]
open_project $out/project/board.xpr
open_run impl_1
set clocks [get_clocks -filter {NAME =~ *clk_pl_0*}]
if {[llength $clocks] != 1} {error "Expected exactly one PS PL0 clock: $clocks"}
set name [get_property NAME $clocks]
set pins [get_property SOURCE_PINS $clocks]
if {[llength $pins] != 1} {error "Ambiguous PS clock source: $pins"}
create_clock -name $name -period 20.000 [get_pins $pins]
report_timing_summary -file $out/timing_50mhz.rpt
report_clocks -file $out/clocks_50mhz.rpt
report_drc -file $out/drc_50mhz.rpt
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set whs [get_property SLACK [get_timing_paths -delay_type min -max_paths 1]]
if {$wns < 0 || $whs < 0} {error "50 MHz timing failed: WNS=$wns WHS=$whs"}
if {[llength [get_drc_violations -quiet -filter {SEVERITY == Error}]]} {error "DRC errors"}
set fd [open $out/clock_50mhz.xdc w]
puts $fd "create_clock -name {$name} -period 20.000 \[get_pins {$pins}\]"
close $fd
add_files -fileset constrs_1 $out/clock_50mhz.xdc
set_property used_in_synthesis false [get_files $out/clock_50mhz.xdc]
set_property PROCESSING_ORDER LATE [get_files $out/clock_50mhz.xdc]
write_bitstream -force $out/board.bit
write_debug_probes -force $out/board.ltx
write_checkpoint -force $out/routed_50mhz.dcp
set fd [open $out/implementation_50mhz.json w]
puts $fd "{\"period_ns\":20.000,\"wns_ns\":$wns,\"whs_ns\":$whs,\"drc_errors\":0}"
close $fd
puts "BOARD_50MHZ_PASS WNS=$wns WHS=$whs"
close_project
exit
