.option norvc
.section .vectors,"ax"
.rept 32
  j trap_fail
.endr
.section .text,"ax"
.weak debug_entry
debug_entry:
  j trap_fail
.weak trap_fail
trap_fail:
  csrr t1,mcause
  csrr t2,mepc
  li t0,0x10000000
  sw t1,0(t0)
  sw t2,4(t0)
  li t0,0x20000000
  sw t1,12(t0)
  li t3,0x80000000
  or t1,t1,t3
  sw t1,0(t0)
1: j 1b
