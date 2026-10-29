# Run after fresh programming (initialized RAM is part of the test input).
# Usage BUILD_DIR BUILD_ID CAPTURE.json
set directory [file normalize [lindex $argv 0]]
set expected_id [string tolower [lindex $argv 1]]
set output [file normalize [lindex $argv 2]]
proc probe {vio type port} {
    set result [get_hw_probes -of_objects $vio -filter "TYPE == $type && PROBE_PORT == $port"]
    if {[llength $result] != 1} {error "Ambiguous VIO $type port $port: $result"}
    return $result
}
proc read_input {vio port} {
    # Constant buses may appear in the LTX as separate one-bit probes.
    set result 0
    set covered 0
    foreach p [get_hw_probes -of_objects $vio -filter "TYPE == vio_input && PROBE_PORT == $port"] {
        set offset [get_property PROBE_PORT_BITS $p]
        set width [get_property PROBE_PORT_BIT_COUNT $p]
        set mask [expr {((1 << $width) - 1) << $offset}]
        if {$covered & $mask} {error "Overlapping VIO input port $port"}
        set_property INPUT_VALUE_RADIX HEX $p
        set value [get_property INPUT_VALUE $p]
        set result [expr {$result | (([scan $value %x] & ((1 << $width) - 1)) << $offset)}]
        set covered [expr {$covered | $mask}]
    }
    if {$covered != 0xffffffff} {error "Incomplete VIO input port $port"}
    return $result
}
proc write_output {vio port value} {
    set p [probe $vio vio_output $port]
    set_property OUTPUT_VALUE_RADIX HEX $p
    set digits [expr {([get_property PROBE_PORT_BIT_COUNT $p] + 3) / 4}]
    set_property OUTPUT_VALUE [format %0*x $digits $value] $p
    commit_hw_vio $p
}
open_hw_manager
connect_hw_server -url localhost:3121
set targets [get_hw_targets */XFL114E3TLZIA]
if {[llength $targets] != 1} {error "Expected KV260 target not unique"}
current_hw_target [lindex $targets 0]
open_hw_target
set device [get_hw_devices xck26_0]
current_hw_device $device
set_property PROBES.FILE $directory/board.ltx $device
refresh_hw_device $device
set usr [string tolower [string range [get_property REGISTER.USR_ACCESS $device] 2 end]]
if {$usr ne $expected_id} {error "wrong bitstream identity"}
set vios [get_hw_vios -of_objects $device]
if {[llength $vios] != 1} {error "VIO not found uniquely: $vios"}
set vio [lindex $vios 0]
refresh_hw_vio $vio
set build [format %08x [read_input $vio 3]]
if {$build ne $expected_id} {error "VIO build ID mismatch"}
set heartbeat0 [read_input $vio 6]
after 20
refresh_hw_vio $vio
if {[read_input $vio 6] == $heartbeat0} {error "clock heartbeat is stopped"}
# Require a new image: completion or a nonzero capture count is stale evidence.
if {([read_input $vio 0] & 1) || [read_input $vio 5] != 0} {error "reprogram before a new trial"}
write_output $vio 1 0
write_output $vio 0 1
after 20
write_output $vio 0 0
after 20
write_output $vio 1 1
after 20
write_output $vio 1 0
set complete 0
for {set attempt 0} {$attempt < 100} {incr attempt} {
    refresh_hw_vio $vio
    if {[read_input $vio 0] & 1} {set complete 1; break}
    after 100
}
if {!$complete} {error "board timeout status=[read_input $vio 0] elapsed=[read_input $vio 2]"}
set status [read_input $vio 0]
set fold [read_input $vio 1]
set elapsed [read_input $vio 2]
set count [read_input $vio 5]
if {$count != 472} {error "expected 472 captured words, got $count"}
set words {}
for {set n 0} {$n < $count} {incr n} {
    write_output $vio 2 $n
    # The memory read is synchronous; this exceeds its two-clock settling bound.
    after 1
    refresh_hw_vio $vio
    lappend words [read_input $vio 4]
}
set fd [open $output w]
puts $fd "{\"build_id\":\"$build\",\"usr_access\":\"$usr\",\"status\":$status,\"signature\":$fold,\"elapsed_cycles\":$elapsed,\"count\":$count,\"words\":\[[join $words ,]\]}"
close $fd
puts "BOARD_CAPTURE_COMPLETE id=$build status=$status count=$count fold=[format %08x $fold] elapsed=$elapsed"
close_hw_target
disconnect_hw_server
close_hw_manager
exit
