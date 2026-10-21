.section .text,"ax"
.global main
main:
  li t0,31
  li t1,11
  la t3,signature_start
  add t2,t0,t1
  sw t2,0(t3)
  sub t2,t0,t1
  sw t2,4(t3)
  mul t2,t0,t1
  sw t2,8(t3)
  div t2,t0,t1
  sw t2,12(t3)
  rem t2,t0,t1
  sw t2,16(t3)
  li t2,0x11223344
  sw t2,20(t3)
  li t2,0xaa
  sb t2,21(t3)
  lw t2,20(t3)
  sw t2,24(t3)
  li t4,0x1122aa44
  bne t2,t4,1f
  li a0,0
  ret
1: li a0,2
  ret
.section .signature,"aw",@nobits
.space 28
