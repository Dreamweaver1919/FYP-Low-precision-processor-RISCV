# Reproducible OOC project creation. Invoke with the generated source manifest.
if {$argc < 1} { error "usage: create_vivado_project.tcl MANIFEST.tcl" }
source [lindex $argv 0]
file mkdir $fyp_project_dir
create_project -force $fyp_project_name $fyp_project_dir -part xck26-sfvc784-2LV-c
set_property target_language Verilog [current_project]
add_files -norecurse $fyp_sources
if {[info exists fyp_clock_xdc]} {
  add_files -fileset constrs_1 -norecurse $fyp_clock_xdc
}
if {[info exists fyp_memory_files] && [llength $fyp_memory_files]} {
  add_files -norecurse $fyp_memory_files
  set_property file_type {Memory Initialization Files} [get_files $fyp_memory_files]
}
set_property include_dirs $fyp_include_dirs [get_filesets sources_1]
set_property verilog_define $fyp_defines [get_filesets sources_1]
set_property top $fyp_top [get_filesets sources_1]
set_property generic $fyp_generics [get_filesets sources_1]
update_compile_order -fileset sources_1
puts "FYP_PROJECT_READY $fyp_project_dir/$fyp_project_name.xpr"
flush stdout
