# Read-only final board receipt. Usage: BUILD_DIR RECEIPT.json
set directory [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
open_hw_manager
connect_hw_server -url localhost:3121
set targets [get_hw_targets */XFL114E3TLZIA]
if {[llength $targets] != 1} {error "Expected one attached KV260"}
current_hw_target [lindex $targets 0]
open_hw_target
set device [get_hw_devices xck26_0]
current_hw_device $device
set_property PROBES.FILE $directory/board.ltx $device
refresh_hw_device $device
set vio [get_hw_vios -of_objects $device]
if {[llength $vio] != 1} {error "Expected one VIO"}
proc input {vio port} {
    set result 0
    foreach p [get_hw_probes -of_objects $vio -filter "TYPE == vio_input && PROBE_PORT == $port"] {
        set_property INPUT_VALUE_RADIX HEX $p
        set result [expr {$result | ([scan [get_property INPUT_VALUE $p] %x] << [get_property PROBE_PORT_BITS $p])}]
    }
    return [expr {$result & 0xffffffff}]
}
refresh_hw_vio $vio
set heartbeat [input $vio 6]
after 20
refresh_hw_vio $vio
if {[input $vio 6] == $heartbeat} {error "Stopped heartbeat"}
if {[input $vio 0] != 19 || [input $vio 5] != 472 || [input $vio 1] != 0x39a7d0b7} {
    error "Expected final NN PASS state"
}
set usr [get_property REGISTER.USR_ACCESS $device]
set build [format 0x%08x [input $vio 3]]
if {$usr ne $build} {error "Build identity mismatch"}
set fd [open $output w]
puts $fd "{\"timestamp_utc\":\"[clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]\",\"target\":\"[current_hw_target]\",\"idcode\":\"[get_property IDCODE_HEX $device]\",\"dna\":\"[get_property REGISTER.DNA $device]\",\"usr_access\":\"$usr\",\"vio_build_id\":\"$build\",\"status\":[input $vio 0],\"signature\":[input $vio 1],\"count\":[input $vio 5],\"elapsed_cycles\":[input $vio 2],\"heartbeat_before\":$heartbeat,\"heartbeat_after\":[input $vio 6]}"
close $fd
puts "FINAL_BOARD_VERIFIED build=$build status=[input $vio 0] count=[input $vio 5]"
close_hw_target
disconnect_hw_server
close_hw_manager
exit
