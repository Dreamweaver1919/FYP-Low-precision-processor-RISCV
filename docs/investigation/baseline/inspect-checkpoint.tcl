open_checkpoint C:/Users/CEG/FYP/FYP.runs/synth_1/cv32e40p_top.dcp
report_drc -file baseline-drc.rpt
report_timing_summary -report_unconstrained -file baseline-timing.rpt
report_clocks -file baseline-clocks.rpt
puts "BASELINE_PORT_COUNT=[llength [get_ports]]"
puts "BASELINE_CLOCK_COUNT=[llength [get_clocks]]"
close_design
exit
