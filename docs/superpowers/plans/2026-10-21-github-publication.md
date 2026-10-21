# FYP Low-Precision Processor RISC-V GitHub Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the FYP workspace into a clean public GitHub repository and publish it to `Dreamweaver1919/FYP-Low-precision-processor-RISCV`.

**Architecture:** Version source, tests, specifications and compact evidence. Exclude Vivado/XSim outputs and caches through `.gitignore`; add portable documentation, license notices and Python-only CI; publish only after a remote-empty check.

**Tech Stack:** Git, GitHub, GitHub Actions, Markdown, PowerShell, Python standard library.

**Spec:** `C:/Users/CEG/FYP/docs/superpowers/specs/2026-10-21-github-publication-design.md`

## Global Constraints

- Target remote: `https://github.com/Dreamweaver1919/FYP-Low-precision-processor-RISCV`.
- Preserve `FYP.xpr` SHA-256 `9d348bcda279dbd563006ed12d1ae816f06b0ff66022e54145c753f7af3f0e82`.
- Preserve all `vendor/cv32e40p/` license files and copyright headers; Apache-2.0 applies only to original project files.
- Do not track Vivado cache/run/simulation output, DCP/bitstream, logs, `.jou`, `.pb`, Python bytecode or normal per-run artifacts.
- Retain delivery manifest/patch/release evidence, verification/benchmark/FPGA summaries, fixed common ROM and ROM metadata.
- CI runs Python-only checks and cannot claim RTL simulation, timing, board, bitstream or power validation.
- Stop if the target remote already has heads; never force-push.

## Review Focus

1. Ignore rules must retain HDL, licenses, fixed ROM and summaries; Task 1 tests accepted and ignored paths.
2. Generated artifacts and local absolute paths must not enter Git; Task 1 audits staged paths.
3. Root Apache license must not be implied to relicense upstream CV32E40P; Task 2 tests notices and original licenses.
4. README must use repository-relative links and no `C:/Users/CEG/FYP`; Task 2 scans it.
5. CI must validate source/model integrity only; Task 3 rejects hardware tools and self-hosted runners.

## File structure

| Path | Responsibility |
|---|---|
| `.gitignore` | Publish boundary |
| `README.md` | Public overview, rebuild, results and limits |
| `LICENSE` | Apache-2.0 for original files |
| `THIRD_PARTY_NOTICES.md` | Upstream provenance/license boundary |
| `CONTRIBUTING.md` | Verification and contribution rules |
| `.github/workflows/verify.yml` | Python-only CI |
| `scripts/check_public_repository.py` | Required/forbidden tracked-path audit |
| `verification/tests/test_public_repository.py` | Publication-policy tests |

### Task 1: Define and test the publish boundary

**Files:**
- Create: `.gitignore`, `scripts/check_public_repository.py`, `verification/tests/test_public_repository.py`

**Interfaces:**
- Produces: `python scripts/check_public_repository.py [--index]`, which succeeds only if no required path is missing and no forbidden path is tracked.

- [ ] **Step 1: Write failing checker tests.** Test supplied path lists: reject `FYP.runs/run.log`, `FYP.cache/x`, `foo.dcp`, `xsim.log`, `.jou`, `.pb`, `__pycache__/x.pyc` and per-run verification files; accept RTL, upstream license, summaries and pinned `imem.hex`/`dmem.hex`.
- [ ] **Step 2: Run:** `python -m unittest verification.tests.test_public_repository -v`. Expected: FAIL because the checker is absent.
- [ ] **Step 3: Implement `.gitignore` and the checker.** Ignore the five existing generated top-level Vivado directories. Ignore broad artifact run trees and unignore only the delivery manifest/patch/release evidence, verification and benchmark summaries, fixed benchmark ROM plus metadata, and FPGA summary. Checker uses `git ls-files` under `--index`.
- [ ] **Step 4: Run:** `python -m unittest verification.tests.test_public_repository -v`; then `git check-ignore -v FYP.runs artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/xsim.log`. Expected: PASS; generated paths ignored and required files retained.
- [ ] **Step 5: Commit:** `git add .gitignore scripts/check_public_repository.py verification/tests/test_public_repository.py`; then `git commit -m "build: define public repository boundary"`.

### Task 2: Create public documentation and provenance

**Files:**
- Create: `README.md`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `CONTRIBUTING.md`
- Modify: `verification/tests/test_public_repository.py`

**Interfaces:**
- `README.md` uses repository-relative links to final reports and states 72 forms, 20 ns OOC PASS, 10 ns NN OOC failure, and no board/bitstream/power claim.
- `THIRD_PARTY_NOTICES.md` names `vendor/cv32e40p/SOURCE.json` as provenance and points to original licenses.

- [ ] **Step 1: Add failing portable-document tests.** Require root README/LICENSE/notices/contributing files, frozen manifest/license, no `C:/Users/CEG/FYP` in root README and the required result-boundary statements.
- [ ] **Step 2: Run:** `python -m unittest verification.tests.test_public_repository -v`. Expected: FAIL because root documents are absent.
- [ ] **Step 3: Write docs.** README is English with concise Chinese abstract, architecture, map, quick Python test, optional Windows Vivado/XSim commands, benchmark interpretation and limits. Add exact Apache-2.0 text. Notices distinguish original/upstream code. Contributing requires source-integrity and Python tests.
- [ ] **Step 4: Run:** `python -m unittest discover -s verification/tests -v`. Expected: PASS and frozen source/XPR remain unchanged.
- [ ] **Step 5: Commit:** `git add README.md LICENSE THIRD_PARTY_NOTICES.md CONTRIBUTING.md verification/tests/test_public_repository.py`; then `git commit -m "docs: add public repository guide and notices"`.

### Task 3: Add CI and build the initial Git history

**Files:**
- Create: `.github/workflows/verify.yml`
- Modify: `verification/tests/test_public_repository.py`

**Interfaces:**
- CI runs on `push` and `pull_request`, with `ubuntu-latest`, `actions/checkout@v4`, `actions/setup-python@v5`, Python 3.12, the existing unittest discovery command and `python scripts/check_public_repository.py --index`.

- [ ] **Step 1: Add a failing workflow test.** Require workflow/interface tokens and reject `vivado`, `xsim`, `bitstream` and `self-hosted`.
- [ ] **Step 2: Run:** `python -m unittest verification.tests.test_public_repository -v`. Expected: FAIL because workflow is absent.
- [ ] **Step 3: Implement workflow.** Name it `Verify public sources`; state FPGA tools and hardware are intentionally out of CI scope.
- [ ] **Step 4: Initialize and audit Git.** Run `git init -b main`; configure local identity only if required; stage publishable files. Run checker index mode, `git status --short`, `git diff --cached --stat` and `git diff --cached --name-only`. Expected: sources/docs/evidence/licenses/workflow only.
- [ ] **Step 5: Run release checks and commit.** Run unittest discovery, `python verification/scripts/package_delivery.py`, and checker index mode. Expected: PASS including 141 source-integrity and archive checks. Run `git add -A`; then `git commit -m "Initial public release of FYP low-precision RISC-V processor"`.

### Task 4: Publish safely to GitHub

**Files:**
- Modify: Git configuration only

**Interfaces:**
- Produces: `origin` at `https://github.com/Dreamweaver1919/FYP-Low-precision-processor-RISCV.git`; remote main equals local HEAD.

- [ ] **Step 1: Run:** `git ls-remote --heads https://github.com/Dreamweaver1919/FYP-Low-precision-processor-RISCV.git`. Expected: no heads. If heads exist, stop; do not overwrite history.
- [ ] **Step 2: Add origin and push.** Run `git remote add origin https://github.com/Dreamweaver1919/FYP-Low-precision-processor-RISCV.git`; then `git push -u origin main`. If authentication fails, preserve local commit and report the need; do not create credentials or force-push.
- [ ] **Step 3: Verify.** Run `git ls-remote origin refs/heads/main`, `git rev-parse HEAD`, and `git status --short`. Expected: matching SHA and no unintended tracked files.

## Plan self-review

- Tasks 1–4 cover publish boundary, compact evidence, documentation, licenses, CI, source integrity, local history and safe remote publication.
- Every Review Focus item has a named Task 1–3 check.
- No existing local artifact is deleted, and no hardware claim is added.
