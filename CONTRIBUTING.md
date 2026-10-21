# Contributing

Contributions must preserve the distinction between host/model validation, full RTL simulation and FPGA OOC implementation. Do not report an OOC result as a board measurement.

Before submitting a source change, run:

```powershell
python -m unittest discover -s verification/tests -v
python scripts/check_public_repository.py --index
```

For RTL or runner changes, also run the relevant XSim regression and retain a structured result in the local artifact workspace. Update a compact summary only after matching source hashes are verified.

Do not add Vivado caches, XSim work directories, DCP/bitstream files, logs, `.jou`, `.pb`, Python bytecode, or arbitrary per-run artifacts to Git. The repository retains only the fixed ROM and compact release evidence required to explain the results.

When changing upstream-derived material, preserve its license and attribution. New original files use the root Apache-2.0 terms unless another license is required.
