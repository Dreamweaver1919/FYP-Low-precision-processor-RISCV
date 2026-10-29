# Vivado: program one verified build, leave VIO reset asserted, enumerate probes.
# Usage: BUILD_DIR BUILD_ID
set directory [file normalize [lindex $argv 0]]
set expected_id [string tolower [lindex $argv 1]]
open_hw_manager
connect_hw_server -url localhost:3121
set targets [get_hw_targets */XFL114E3TLZIA]
if {[llength $targets] != 1} {error "Expected attached KV260 cable not uniquely found"}
current_hw_target [lindex $targets 0]
open_hw_target
set device [get_hw_devices xck26_0]
current_hw_device $device
set_property PROGRAM.FILE $directory/board.bit $device
set_property PROBES.FILE $directory/board.ltx $device
program_hw_devices $device
refresh_hw_device $device
set actual_id [string tolower [string range [get_property REGISTER.USR_ACCESS $device] 2 end]]
if {$actual_id ne $expected_id} {error "USR_ACCESS mismatch $actual_id != $expected_id"}
puts "BOARD_PROGRAMMED id=$actual_id"
foreach vio [get_hw_vios -of_objects $device] {
    puts "BOARD_VIO=$vio"
    foreach probe [get_hw_probes -of_objects $vio] {
        puts "BOARD_PROBE=$probe"
        report_property $probe
    }
}
close_hw_target
disconnect_hw_server
close_hw_manager
exit
