# XPulpNN benchmark comparison

Generated: 2026-10-21T12:26:59

The primary metric is **legacy XPULP dot8 kernel cycles / native XPulpNN kernel cycles**. It excludes only work outside the measured kernel interval (preparation, mailbox, and checking); mcycle still includes all instruction-fetch and data-memory stalls inside that interval. The end-to-end metric adds the separately measured preparation interval to both sides. Counters are raw: the empty counter bracket is reported and not subtracted.

| Dataset | q | logical MACs | physical lane-MACs | padding MACs | legacy cycles | native cycles | primary speedup | end-to-end speedup | scalar/native |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| matmul_q4 | 4 | 2048 | 2048 | 0 | 346049 | 18593 | 18.612x | 4.427x | 12.778x |
| conv_q4 | 4 | 20736 | 20736 | 0 | 3336413 | 138265 | 24.131x | 4.236x | 16.183x |
| tail_q4 | 4 | 140 | 160 | 20 | 23991 | 1563 | 15.349x | 1.978x | 10.553x |
| matmul_q2 | 2 | 2048 | 2048 | 0 | 336354 | 13074 | 25.727x | 4.687x | 17.465x |
| conv_q2 | 2 | 20736 | 23040 | 2304 | 3297612 | 94302 | 34.969x | 4.452x | 23.343x |
| tail_q2 | 2 | 140 | 192 | 52 | 23487 | 1236 | 19.002x | 2.011x | 12.954x |

## Measurement conditions

- Reference artifact: `C:\Users\CEG\FYP\artifacts\verification\overlay_nn1\bench\1\20261021-114500-136671`
- Candidate artifact: `C:\Users\CEG\FYP\artifacts\verification\overlay_nn1\bench_wait\1\20261021-121801-710872`
- Build commands match after artifact-specific ELF/map paths are removed: `True`.
- Run profiles: reference `{'config': 'overlay_nn1', 'seed': 1, 'grant_max': 0, 'response_max': 1, 'fixed_wait': None}`; candidate `{'config': 'overlay_nn1', 'seed': 1, 'grant_max': 2, 'response_max': 4, 'fixed_wait': True}`; identical: `False`.
- `fixed_wait: True` means the candidate uses fixed OBI grant/response counts, not randomized delays.
- Reference ELF SHA-256: `3fac9907a4301808938536a79a92bbe536c9a68af9c0420595d68c8b3d810dd2`; candidate: `463bb92437c571d047177074db77e5d4891bf56795522962972b8b589b3c236e`.
- Reference code size: {'available': True, 'elf_bytes': 15160, 'text_bytes': 4442, 'sections': {'.vectors': 128, '.init': 102, '.debug': 4, '.debug_exception': 4, '.text': 4442, '.rodata': 6208, '.signature': 1888, '.bss': 1584, '.riscv.attributes': 67, '.comment': 51}}; candidate: {'available': True, 'elf_bytes': 15160, 'text_bytes': 4442, 'sections': {'.vectors': 128, '.init': 102, '.debug': 4, '.debug_exception': 4, '.text': 4442, '.rodata': 6208, '.signature': 1888, '.bss': 1584, '.riscv.attributes': 67, '.comment': 51}}.
- Empty measurement bracket, candidate: 84 cycles / 4 instructions; it is not subtracted.

## Dependent sdot throughput

| q | 128 legacy dot8 cycles (CPI) | 128 native sdot cycles (CPI) | native/legacy cycle ratio |
|---|---:|---:|---:|
| 4 | 987 (7.711) | 1015 (7.930) | 1.028x |
| 2 | 987 (7.711) | 994 (7.766) | 1.007x |

## Wait-profile sensitivity (not a speedup comparison)

These ratios show how each separately measured kernel interval changes with the OBI wait profile. They do not compare one profile's legacy path to another profile's native path.

| Dataset | legacy candidate/reference | native candidate/reference | primary speedup within candidate |
|---|---:|---:|---:|
| matmul_q4 | 3.485x | 3.437x | 18.612x |
| conv_q4 | 3.488x | 3.466x | 24.131x |
| tail_q4 | 3.477x | 3.347x | 15.349x |
| matmul_q2 | 3.489x | 3.521x | 25.727x |
| conv_q2 | 3.489x | 3.637x | 34.969x |
| tail_q2 | 3.477x | 3.424x | 19.002x |

## Interpretation limits

`nn_physical_lane_macs - logical_macs` is padding work. The tail datasets therefore have equal logical output work but execute 20/52 padded lane-MACs at q=4/q=2; both logical and physical work are reported alongside the same-task speedup.
The scalar result is supplemental. The stated primary denominator is the legacy 8-bit XPULP implementation, including its required unpack/sign extension and software threshold quantization.
The legacy denominator is a deliberately portable, unpacking-heavy local baseline. It is not a claim that this measurement matches an optimized XpulpNN-paper baseline or reproduces the paper's speedup.
A candidate may change memory wait settings. Each in-run primary ratio remains valid because its legacy and native paths use that run's same OBI service; cross-profile raw cycle comparisons require the run-profile field above to be identical.
