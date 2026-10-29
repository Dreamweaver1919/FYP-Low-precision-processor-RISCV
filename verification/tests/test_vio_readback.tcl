# Offline Vivado Tcl test: source only helpers, with no hardware operations.
set fd [open [file join [file dirname [info script]] ../../scripts/run_board.tcl] r]
set source [read $fd]
close $fd
set start [string first {proc probe } $source]
set end [string first {open_hw_manager} $source]
eval [string range $source $start [expr {$end-1}]]
proc get_hw_probes {args} {return $::probes}
proc set_property {args} {}
proc get_property {property probe} {return [dict get $::properties $probe $property]}
set probes full
set properties [dict create full [dict create PROBE_PORT_BITS 0 PROBE_PORT_BIT_COUNT 32 INPUT_VALUE ffffffff]]
if {[read_input test 4] != 4294967295} {error "Full 32-bit unsigned readback failed"}
set probes {}
set properties {}
for {set bit 0} {$bit < 32} {incr bit} {
    lappend probes bit$bit
    dict set properties bit$bit [dict create PROBE_PORT_BITS $bit PROBE_PORT_BIT_COUNT 1 INPUT_VALUE [expr {(0xf584e920 >> $bit) & 1}]]
}
if {[read_input test 3] != 0xf584e920} {error "Split constant build ID failed"}
set probes [lrange $probes 0 30]
if {![catch {read_input test 3}]} {error "Incomplete bus should fail"}
puts {PASS VIO unsigned, split and incomplete readback}
exit
