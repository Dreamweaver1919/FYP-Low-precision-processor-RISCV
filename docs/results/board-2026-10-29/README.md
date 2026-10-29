# Physical board evidence, 2026-10-29

`summary.json` is derived by `verification/scripts/summarize_board.py` from the checked build manifests and raw captures. The script validates current source/ROM hashes, identities, final timing, both repeated trials, common counters, PS clock snapshots and the final board receipt.

- `baseline/` and `nn/`: source/ROM/build identity, routed reports, normalized wrapper simulation manifests and two final physical trials each.
- `trial1`/`trial2`: published names for the final local `trial3`/`trial4`; the session excerpt records this mapping. Each has its own fresh programming, raw 472-word capture, derived metrics and exact acquisition-script hashes.
- `ps-clock-readback.txt`: snapshot during the initial validation sequence, after configuring PL0. `ps-clock-after.txt`: snapshot after the preliminary four successful runs. `ps-clock-final.txt`: snapshot after the final four runs. All show the same PLL/PL0 state.
- `final-board.json`: read-only hardware receipt after the last NN run, including USR_ACCESS, VIO status/build ID, device identity and advancing unsigned heartbeat.
- `report-provenance.json`: hashes of original and published implementation reports. Host header removed and output-path header made relative; numerical/tool results are unchanged. Wrapper simulation manifests likewise use repository-relative source paths with original byte hashes.

The final four trials use the unsigned VIO decoding fix. Earlier captures and the rejected stale-run/address-format attempts remain local and are not counted as final validation. The 356 deterministic words are checked against the pinned common ROM's expected data. The other 116 words contain counters and throughput measurements; they are captured measurements, with exact repeatability checked across the two runs, rather than fixed golden constants.

Full bitstreams, checkpoints and tool logs remain outside Git. File hashes bind the actual programmed inputs; these evidence files are execution records, not a hardware attestation or an independent physical frequency measurement. The clock is nominal 50 MHz from PS register configuration. See the [board report](../kv260-board-validation.md) for limits and reproduction commands.
