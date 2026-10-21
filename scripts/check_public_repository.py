"""Validate the small, reproducible file set intended for public Git history."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


REQUIRED_PATHS = {
    ".gitignore",
    "README.md",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "CONTRIBUTING.md",
    ".github/workflows/verify.yml",
    "FYP.xpr",
    "rtl/nn/cv32e40p_nn_quant.sv",
    "vendor/cv32e40p/LICENSE",
    "vendor/cv32e40p/SOURCE.json",
    "artifacts/delivery/source-manifest.json",
    "artifacts/delivery/core-overlays.patch",
    "artifacts/delivery/release-evidence.json",
    "artifacts/verification/summary.json",
    "artifacts/verification/benchmark-comparison.json",
    "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/imem.hex",
    "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/dmem.hex",
    "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/benchmark.json",
    "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/expected.json",
    "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/build.json",
    "artifacts/fpga/summary.json",
}

GENERATED_TOP_LEVEL = {"FYP.cache", "FYP.hw", "FYP.ip_user_files", "FYP.runs", "FYP.sim"}
ALLOWED_ARTIFACTS = {
    path for path in REQUIRED_PATHS if path.startswith("artifacts/")
}
FORBIDDEN_SUFFIXES = {".bit", ".bin", ".dcp", ".jou", ".log", ".pb", ".pyc"}


def normalize(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def forbidden_reason(path: str) -> str | None:
    normalized = normalize(path)
    parts = PurePosixPath(normalized).parts
    if not normalized:
        return None
    if parts[0] in GENERATED_TOP_LEVEL:
        return "generated Vivado top-level directory"
    if "__pycache__" in parts:
        return "Python bytecode cache"
    if PurePosixPath(normalized).suffix.lower() in FORBIDDEN_SUFFIXES:
        return "generated tool output"
    if normalized.startswith("artifacts/") and normalized not in ALLOWED_ARTIFACTS:
        return "artifact is not part of the compact public evidence set"
    return None


def validate(paths: list[str], require_complete: bool = False) -> list[str]:
    normalized = {normalize(path) for path in paths if normalize(path)}
    errors = [f"forbidden: {path} ({reason})" for path in sorted(normalized)
              if (reason := forbidden_reason(path))]
    if require_complete:
        errors.extend(f"missing required tracked path: {path}"
                      for path in sorted(REQUIRED_PATHS - normalized))
    return errors


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return result.stdout.splitlines()


def portable_evidence_errors() -> list[str]:
    evidence_path = Path("artifacts/delivery/release-evidence.json")
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"unreadable release evidence: {error}"]
    payload = json.dumps(evidence)
    errors = []
    if re.search(r"[A-Za-z]:[\\/]", payload):
        errors.append("release evidence contains a machine-absolute path")
    if evidence.get("fpga_summary") != "artifacts/fpga/summary.json":
        errors.append("release evidence must reference the tracked FPGA summary")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--paths", help="newline-separated paths for policy testing")
    source.add_argument("--index", action="store_true", help="audit the current Git index")
    args = parser.parse_args()
    try:
        if args.paths is not None:
            errors = validate(args.paths.splitlines())
        elif args.index:
            errors = validate(tracked_paths(), require_complete=True)
            errors.extend(portable_evidence_errors())
        else:
            errors = validate(tracked_paths(), require_complete=True)
            errors.extend(portable_evidence_errors())
    except RuntimeError as error:
        print(f"public repository audit failed: {error}", file=sys.stderr)
        return 2
    if errors:
        print("public repository audit failed:", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("public repository audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
