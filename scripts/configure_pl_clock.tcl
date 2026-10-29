# XSDB: bounded PL0-only configuration for the observed KV260 boot state.
# Does not change any PLL, DDR, PS processor reset or other PL clocks.
connect -url tcp:localhost:3121
targets -set -filter {name =~ "PSU"}
set pll [mrd -value 0xFF5E0020]
set frac [mrd -value 0xFF5E0028]
set status [mrd -value 0xFF5E0040]
if {$pll != 0x00015a00 || $frac != 0 || !($status & 1)} {
    error "Unexpected IOPLL state; refusing automatic PL clock change"
}
set before [mrd -value 0xFF5E00C0]
set preserved [expr {$before & ~0x013f3f07}]
mwr 0xFF5E00C0 [expr {$before & ~0x01000000}]
after 1
mwr 0xFF5E00C0 [expr {$preserved | 0x00011e00}]
after 1
mwr 0xFF5E00C0 [expr {$preserved | 0x01011e00}]
set after [mrd -value 0xFF5E00C0]
if {($after & 0x013f3f07) != 0x01011e00} {error "PL0 readback mismatch"}
puts "PL_CLOCK_CONFIGURED before=[format %08x $before] after=[format %08x $after] IOPLL=[format %08x $pll] nominal_hz=50000000"
disconnect
exit
