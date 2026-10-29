# KV260 physical validation design

The user requested programming the attached board, validating the repository design on hardware, updating the report, and synchronizing GitHub. Programming and publication are authorized. Implementation details below are engineering choices made within that request.

## Approach

Use the existing self-contained CV32E40P system and pinned common benchmark ROM on XCK26. A minimal Zynq PS supplies PL0 clock; a JTAG VIO provides reset/start and readback without external pin wiring or a Linux/DDR dependency. Compared with a PS software/AXI application or UART pin interface, this directly tests the existing ROM and memory system with fewer additional dependencies. PS clock registers will be inspected before any bounded clock configuration; do not reinitialize DDR or reset the entire PS.

## Interfaces and evidence

Extend `fyp_nn_system` with a read-only stream of the existing signature scan: valid, 14-bit index, 32-bit data, and 32-bit count. This does not arbitrate against CPU memory accesses. A board adapter captures up to 512 words in a separate readback memory, reports overflow, completion, software/protocol pass, run cycles, a heartbeat and a build identifier. VIO runs in the same clock domain. Reset asserts asynchronously and releases synchronously. Each independent trial starts from a new bitstream load to restore initialized memory.

Build frozen FF baseline and NN-enabled configurations using exactly the tracked common IMEM/DMEM. Nominal target is 50 MHz (20 ns); record the actual PS divider/PLL-derived frequency and do not claim an independent oscilloscope measurement. Fully route each design, require nonnegative setup/hold slack and no error-severity DRC before writing bitstream. Set a content-derived USR_ACCESS build identifier and preserve full source/ROM/bitstream hashes in evidence.

Read and compare all 356 deterministic output words and collect the remaining 116 metric words, including kernel mcycle/minstret. Check completion, no overflow, expected signature count, expected fold and build ID. Native speedups use per-kernel cycle counters against legacy dot8; total program duration is not a kernel speedup. Run repeated freshly programmed trials; finish with the NN-enabled image loaded. Store raw readback and compact checked summaries in Git, large tool outputs and bitstreams locally.

## Boundaries

This is volatile JTAG programming, not a persistent boot-flash installation. No power measurement or neural-network accuracy claim. Original FYP.xpr and frozen vendor RTL remain immutable. Historical OOC reports retain their original source scope and are supplemented by a new board report.
