OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { IMEM (rx) : ORIGIN = 0, LENGTH = 64K
         DMEM (rw) : ORIGIN = 0x10000000, LENGTH = 64K }
SECTIONS {
  .vectors 0x100 : { KEEP(*(.vectors)) } > IMEM
  .init 0x200 : { KEEP(*(.text.start)) } > IMEM
  .debug 0x400 : { KEEP(*(.debug.entry)) } > IMEM
  .debug_exception 0x480 : { KEEP(*(.debug.exception)) } > IMEM
  .text 0x800 : { *(.text .text.*) } > IMEM
  .rodata : { *(.rodata .rodata.*) } > IMEM
  .signature 0x10000000 (NOLOAD) : { signature_start = .; *(.signature) signature_end = .; } > DMEM
  .data : { *(.data .data.*) *(.sdata .sdata.*) } > DMEM
  .bss (NOLOAD) : { __bss_start = .; *(.bss .bss.* COMMON) *(.sbss .sbss.*) __bss_end = .; } > DMEM
  __stack_top = 0x1000fff0;
  ASSERT(__bss_end <= 0x1000f000, "data overlaps reserved stack")
  ASSERT(SIZEOF(.init) <= 0x200, "startup overlaps debug entry")
  ASSERT(SIZEOF(.vectors) <= 0x100, "vectors overlap startup")
}
