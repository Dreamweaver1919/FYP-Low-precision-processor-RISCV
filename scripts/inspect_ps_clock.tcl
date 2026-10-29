# XSDB read-only PS clock inspection. No resets or writes.
connect -url tcp:localhost:3121
targets
targets -set -filter {name =~ "PSU"}
foreach addr {0xFF5E0020 0xFF5E0028 0xFF5E0040 0xFF5E00C0 0xFF0A0054 0xFF0A0344 0xFF0A0348 0xFFD80110} {
    puts "PS_CLOCK_READ $addr [format 0x%08x [mrd -value $addr]]"
}
disconnect
exit
