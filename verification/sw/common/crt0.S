.option norelax
.section .text.start,"ax"
.global _start
_start:
  la sp, __stack_top
  li t0, 0x101
  csrw mtvec, t0
  csrw mcountinhibit, zero
  la t0, __bss_start
  la t1, __bss_end
1: bgeu t0,t1,2f
  sw zero,0(t0)
  addi t0,t0,4
  j 1b
2: call main
  li t0,0x20000000
  la t1,signature_start
  sw t1,4(t0)
  la t2,signature_end
  sub t2,t2,t1
  srli t2,t2,2
  sw t2,8(t0)
  bnez a0,3f
  li a0,1
3: sw a0,0(t0)
4: j 4b
.section .debug.entry,"ax"
  j debug_entry
.section .debug.exception,"ax"
  j trap_fail
