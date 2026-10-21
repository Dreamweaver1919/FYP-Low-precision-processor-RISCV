"""Compare two PASS Route-A benchmark artifacts without using program wall time.

The benchmark binary records separate mcycle/minstret intervals for preparation,
legacy XPULP dot8, native XPulpNN, scalar, an empty counter bracket, and 128
dependent sdot instructions.  This tool consumes those intervals only; the
testbench's total simulation cycles are intentionally excluded from speedups.
"""
import argparse
import json
import pathlib
import subprocess
from datetime import datetime


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE = ROOT / "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671"
OUT_JSON = ROOT / "artifacts/verification/benchmark-comparison.json"
OUT_MD = ROOT / "docs/results/benchmark-comparison.md"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifact(directory):
    directory = pathlib.Path(directory).resolve()
    result = read_json(directory / "benchmark_results.json")
    build = read_json(directory / "build.json")
    run = read_json(directory / "run.json") if (directory / "run.json").exists() else {}
    if result.get("status") != "PASS":
        raise ValueError(f"{directory}: benchmark_results.json is not PASS")
    if build.get("test") != "bench_common":
        raise ValueError(f"{directory}: not a bench_common build")
    if result.get("overhead_subtracted") is not False:
        raise ValueError(f"{directory}: expected raw, unsubtracted counters")
    return {"directory": str(directory), "result": result, "build": build, "run": run}


def normalize_command(command):
    """Retain build choices while discarding artifact-specific output paths."""
    omitted_prefixes = ("-Wl,-Map=",)
    normalized = []
    for item in command:
        text = str(item).replace("\\", "/")
        if text.startswith(omitted_prefixes) or text.endswith("/test.elf"):
            continue
        # Generated benchmark_data.h is deliberately included from each unique
        # artifact directory, so its parent path is not a build-input change.
        if "/artifacts/verification/" in text and ("/bench/" in text or "/bench_wait/" in text):
            normalized.append("<generated-benchmark-include>")
            continue
        normalized.append(text)
    return normalized


def text_size(directory):
    elf = pathlib.Path(directory) / "test.elf"
    size = pathlib.Path(r"D:/fyp-xpulpnn/tools/xpack-riscv-none-elf-gcc-15.2.0-1/bin/riscv-none-elf-size.exe")
    if not elf.exists():
        return {"available": False, "reason": "test.elf missing"}
    if not size.exists():
        return {"available": False, "reason": "riscv-none-elf-size.exe missing", "elf_bytes": elf.stat().st_size}
    completed = subprocess.run([str(size), "-A", str(elf)], capture_output=True, text=True, check=True)
    sections = {}
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0].startswith(".") and fields[1].isdigit():
            sections[fields[0]] = int(fields[1])
    return {"available": True, "elf_bytes": elf.stat().st_size,
            "text_bytes": sections.get(".text"), "sections": sections}


def per_dataset(artifact):
    rows = {}
    for dataset in artifact["result"]["datasets"]:
        name = dataset["name"]
        legacy = dataset["legacy_dot8"]
        native = dataset["native_nn"]
        scalar = dataset.get("scalar")
        preparation = dataset["preparation"]
        if not native["cycles"] or not legacy["cycles"]:
            raise ValueError(f"{name}: zero primary interval")
        rows[name] = {
            "shape": {key: dataset[key] for key in ("m", "k", "n", "q", "stride_words", "output_words")},
            "logical_macs": dataset["logical_macs"],
            "physical_lane_macs": dataset["nn_physical_lane_macs"],
            "padding_macs": dataset["nn_physical_lane_macs"] - dataset["logical_macs"],
            "preparation": preparation,
            "legacy_dot8": legacy,
            "native_nn": native,
            "scalar": scalar,
            "primary_speedup": legacy["cycles"] / native["cycles"],
            "end_to_end_speedup": (preparation["cycles"] + legacy["cycles"]) /
                                (preparation["cycles"] + native["cycles"]),
            "scalar_vs_native": scalar["cycles"] / native["cycles"] if scalar and native["cycles"] else None,
        }
    return rows


def cpi(entry):
    return entry["cycles"] / 128.0


def markdown(report):
    reference, candidate = report["reference"], report["candidate"]
    lines = [
        "# XPulpNN benchmark comparison",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "The primary metric is **legacy XPULP dot8 kernel cycles / native XPulpNN kernel cycles**. "
        "It excludes only work outside the measured kernel interval (preparation, mailbox, and checking); "
        "mcycle still includes all instruction-fetch and data-memory stalls inside that interval. "
        "The end-to-end metric adds the separately measured preparation interval to both sides. "
        "Counters are raw: the empty counter bracket is reported and not subtracted.",
        "",
        "| Dataset | q | logical MACs | physical lane-MACs | padding MACs | legacy cycles | native cycles | primary speedup | end-to-end speedup | scalar/native |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in candidate["datasets"].items():
        lines.append("| {name} | {q} | {logical} | {physical} | {padding} | {legacy} | {native} | {primary:.3f}x | {e2e:.3f}x | {scalar:.3f}x |".format(
            name=name, q=row["shape"]["q"], logical=row["logical_macs"], physical=row["physical_lane_macs"], padding=row["padding_macs"],
            legacy=row["legacy_dot8"]["cycles"], native=row["native_nn"]["cycles"],
            primary=row["primary_speedup"], e2e=row["end_to_end_speedup"], scalar=row["scalar_vs_native"]))
    lines += ["", "## Measurement conditions", "",
              f"- Reference artifact: `{reference['directory']}`",
              f"- Candidate artifact: `{candidate['directory']}`",
              f"- Build commands match after artifact-specific ELF/map paths are removed: `{report['same_build_command']}`.",
              f"- Run profiles: reference `{report['reference_profile']}`; candidate `{report['candidate_profile']}`; identical: `{report['same_run_profile']}`.",
              "- `fixed_wait: True` means the candidate uses fixed OBI grant/response counts, not randomized delays.",
              f"- Reference ELF SHA-256: `{reference['build']['elf_sha256']}`; candidate: `{candidate['build']['elf_sha256']}`.",
              f"- Reference code size: {report['code_size']['reference']}; candidate: {report['code_size']['candidate']}.",
              f"- Empty measurement bracket, candidate: {candidate['empty_bracket']['cycles']} cycles / {candidate['empty_bracket']['instructions']} instructions; it is not subtracted.",
              "",
              "## Dependent sdot throughput", "",
              "| q | 128 legacy dot8 cycles (CPI) | 128 native sdot cycles (CPI) | native/legacy cycle ratio |",
              "|---|---:|---:|---:|"]
    for item in candidate["throughput"]:
        legacy, native = item["legacy_dot8"], item["native_nn"]
        lines.append(f"| {item['q']} | {legacy['cycles']} ({cpi(legacy):.3f}) | {native['cycles']} ({cpi(native):.3f}) | {native['cycles']/legacy['cycles']:.3f}x |")
    if not report["same_run_profile"]:
        lines += ["", "## Wait-profile sensitivity (not a speedup comparison)", "",
                  "These ratios show how each separately measured kernel interval changes with the OBI wait profile. They do not compare one profile's legacy path to another profile's native path.",
                  "", "| Dataset | legacy candidate/reference | native candidate/reference | primary speedup within candidate |",
                  "|---|---:|---:|---:|"]
        for name, row in candidate["datasets"].items():
            prior = reference["datasets"][name]
            lines.append(f"| {name} | {row['legacy_dot8']['cycles']/prior['legacy_dot8']['cycles']:.3f}x | "
                         f"{row['native_nn']['cycles']/prior['native_nn']['cycles']:.3f}x | {row['primary_speedup']:.3f}x |")
    lines += ["", "## Interpretation limits", "",
              "`nn_physical_lane_macs - logical_macs` is padding work. The tail datasets therefore have equal logical output work but execute 20/52 padded lane-MACs at q=4/q=2; both logical and physical work are reported alongside the same-task speedup.",
              "The scalar result is supplemental. The stated primary denominator is the legacy 8-bit XPULP implementation, including its required unpack/sign extension and software threshold quantization.",
              "The legacy denominator is a deliberately portable, unpacking-heavy local baseline. It is not a claim that this measurement matches an optimized XpulpNN-paper baseline or reproduces the paper's speedup.",
              "A candidate may change memory wait settings. Each in-run primary ratio remains valid because its legacy and native paths use that run's same OBI service; cross-profile raw cycle comparisons require the run-profile field above to be identical.",
              ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=pathlib.Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--candidate", type=pathlib.Path, required=True,
                        help="PASS bench artifact produced with the fixed wait profile")
    parser.add_argument("--out-json", type=pathlib.Path, default=OUT_JSON)
    parser.add_argument("--out-md", type=pathlib.Path, default=OUT_MD)
    args = parser.parse_args()

    ref_raw, cand_raw = load_artifact(args.reference), load_artifact(args.candidate)
    reference = {**ref_raw, "datasets": per_dataset(ref_raw),
                 "empty_bracket": ref_raw["result"]["empty_bracket"], "throughput": ref_raw["result"]["throughput"]}
    candidate = {**cand_raw, "datasets": per_dataset(cand_raw),
                 "empty_bracket": cand_raw["result"]["empty_bracket"], "throughput": cand_raw["result"]["throughput"]}
    if set(reference["datasets"]) != set(candidate["datasets"]):
        raise ValueError("dataset names differ")
    for name in reference["datasets"]:
        for key in ("shape", "logical_macs", "physical_lane_macs"):
            if reference["datasets"][name][key] != candidate["datasets"][name][key]:
                raise ValueError(f"{name}: incompatible {key}")
    report = {
        "status": "PASS",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reference": reference,
        "candidate": candidate,
        "same_build_command": normalize_command(ref_raw["build"]["command"]) == normalize_command(cand_raw["build"]["command"]),
        "reference_profile": {key: ref_raw["run"].get(key) for key in ("config", "seed", "grant_max", "response_max", "fixed_wait")},
        "candidate_profile": {key: cand_raw["run"].get(key) for key in ("config", "seed", "grant_max", "response_max", "fixed_wait")},
        "code_size": {"reference": text_size(ref_raw["directory"]), "candidate": text_size(cand_raw["directory"])},
        "method": {"primary_denominator": "legacy_dot8 kernel interval", "primary_numerator": "native_nn kernel interval",
                   "total_program_cycles_used": False, "empty_bracket_subtracted": False},
    }
    report["same_run_profile"] = report["reference_profile"] == report["candidate_profile"]
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": "PASS", "json": str(args.out_json), "markdown": str(args.out_md)}, indent=2))


if __name__ == "__main__":
    main()
