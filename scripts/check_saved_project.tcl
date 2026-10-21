# Read-only check of dependencies after reopening an XPR from another directory.
if {$argc != 1} { error "usage: check_saved_project.tcl ABS_PROJECT.xpr" }
open_project -read_only [lindex $argv 0]
set clocks [get_files -of_objects [get_filesets constrs_1] -filter {FILE_TYPE == XDC}]
if {[llength $clocks] == 0} { error "Saved project has no persistent clock XDC" }
foreach clock $clocks {
  if {![file exists $clock]} { error "Missing saved clock XDC: $clock" }
}
set top [get_property top [get_filesets sources_1]]
if {$top == "fyp_nn_system"} {
  set memory [get_files -filter {FILE_TYPE == "Memory Initialization Files"}]
  if {[llength $memory] != 2} { error "Saved system must contain both memory image assets" }
  foreach asset $memory {
    if {![file exists $asset]} { error "Missing captured memory asset: $asset" }
  }
  set generics [get_property generic [get_filesets sources_1]]
  foreach key {IMEM_FILE DMEM_FILE} {
    set found 0
    foreach setting $generics {
      if {[string first "$key=" $setting] == 0} {
        set filename [string trim [string range $setting [expr {[string length $key]+1}] end] {"}]
        if {[file pathtype $filename] != "absolute" || ![file exists $filename]} {
          error "$key is not a usable absolute captured image path: $filename"
        }
        set found 1
      }
    }
    if {!$found} { error "$key missing from saved system generics" }
  }
}
puts "FYP_SAVED_PROJECT_PASS top=$top persistent_clock_files=[llength $clocks]"
close_project
exit 0
