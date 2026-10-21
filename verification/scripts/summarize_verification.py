#!/usr/bin/env python3
"""Create a transparent, reproducible index of verification evidence.

The index deliberately treats absent structured evidence and stale source hashes as
incomplete evidence.  It never turns a historical FAIL into a PASS.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "verification"
OUT_JSON = ART / "summary.json"
OUT_MD = ROOT / "docs" / "results" / "verification-index.md"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return (value if isinstance(value, dict) else {"value": value}), None
    except Exception as exc:  # Evidence must be reported even if malformed.
        return None, f"{type(exc).__name__}: {exc}"


def newest(patterns: list[str]) -> Path | None:
    found: list[Path] = []
    for pattern in patterns:
        found.extend(ART.glob(pattern))
    found = [p for p in found if p.is_file()]
    return max(found, key=lambda p: p.stat().st_mtime) if found else None


def find_run_json(result: Path) -> Path | None:
    for parent in (result.parent, *result.parents):
        candidate = parent / "run.json"
        if candidate.is_file():
            return candidate
        if parent == ART:
            break
    return None


def source_items(run: dict[str, Any]) -> list[tuple[str, str]]:
    raw = run.get("sources", {})
    if isinstance(raw, dict):
        items = [(str(k), str(v)) for k, v in raw.items()]
    elif isinstance(raw, list):
        items = [(str(x.get("path")), str(x.get("sha256"))) for x in raw if isinstance(x, dict)]
    else:
        items = []
    # Core program manifests keep the actual compiled TB pair in verification_inputs,
    # alongside many generator/report scripts. Audit only the two compiled TB files:
    # changing compare/run_fpga/summarizers must not make core RTL evidence look stale.
    for item in run.get("verification_inputs", []):
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).replace("\\", "/").lower()
        if path.endswith("verification/tb/obi_memory_agent.sv") or path.endswith("verification/tb/tb_core_program.sv"):
            items.append((str(item.get("path")), str(item.get("sha256"))))
    return items


def hash_audit(result: Path) -> dict[str, Any]:
    run_path = find_run_json(result)
    if not run_path:
        # Small unit runners store provenance beside the PASS status in result.json.
        run_path = result
    run, err = read_json(run_path)
    if err or run is None:
        return {"provenance_json": rel(run_path), "rtl": "UNREADABLE_RUN_JSON", "tb": "UNREADABLE_RUN_JSON", "error": err, "records": []}
    records = []
    for text_path, expected in source_items(run):
        path = Path(text_path)
        if not path.is_absolute():
            path = ROOT / path
        try:
            path = path.resolve()
        except OSError:
            pass
        category = "rtl" if str(path).lower().startswith(str(ROOT / "rtl").lower()) else ("tb" if str(path).lower().startswith(str(ROOT / "verification" / "tb").lower()) else "other")
        item: dict[str, Any] = {"path": rel(path), "category": category, "recorded_sha256": expected}
        if not path.is_file():
            item["state"] = "MISSING_CURRENT_FILE"
        else:
            current = sha256(path)
            item.update(current_sha256=current, state="MATCH" if current.lower() == expected.lower() else "MISMATCH")
        records.append(item)
    def state(category: str) -> str:
        subset = [x for x in records if x["category"] == category]
        if not subset:
            return "NOT_RECORDED"
        return "MATCH" if all(x["state"] == "MATCH" for x in subset) else "MISMATCH_OR_MISSING"
    return {"provenance_json": rel(run_path), "rtl": state("rtl"), "tb": state("tb"), "records": records}


def classify_failure(path: Path, data: dict[str, Any]) -> str:
    status = str(data.get("status", "UNKNOWN")).upper()
    text = (rel(path) + " " + json.dumps(data, ensure_ascii=False)).lower()
    if status == "PASS":
        return "PASS"
    if "red" in rel(path).lower() or "frozen_ff_pulp1/isa" in rel(path).lower():
        return "EXPECTED_RED_HISTORICAL"
    if status in {"UNRUNNABLE", "ERROR"} or any(s in text for s in ("windowspowershell", "execution policy", "not recognized", "tool failure")):
        return "TOOL_FAILURE"
    return "FAIL_OR_INCOMPLETE"


def entry(label: str, patterns: list[str], required: bool = True, notes: str = "") -> dict[str, Any]:
    result = newest(patterns)
    base: dict[str, Any] = {"label": label, "required": required, "patterns": patterns, "notes": notes}
    if not result:
        return base | {"status": "MISSING", "classification": "MISSING_EVIDENCE", "artifact": None, "hash_audit": None}
    data, err = read_json(result)
    if err or data is None:
        return base | {"status": "UNREADABLE", "classification": "UNREADABLE_JSON", "artifact": rel(result), "json_error": err, "hash_audit": hash_audit(result)}
    status = str(data.get("status", "UNKNOWN")).upper()
    return base | {"status": status, "classification": classify_failure(result, data), "artifact": rel(result), "result": data, "hash_audit": hash_audit(result)}


def static_entry(label: str, path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"label": label, "required": True, "status": "MISSING", "classification": "MISSING_EVIDENCE", "artifact": rel(path)}
    return {"label": label, "required": True, "status": "PRESENT", "classification": "REVIEW_ARTIFACT", "artifact": rel(path), "sha256": sha256(path)}


def group_leaves(node: dict[str, Any], artifact: Path) -> list[tuple[dict[str, Any], Path]]:
    """Flatten nested runner result children while retaining each leaf's own artifact."""
    children = node.get("children")
    if not isinstance(children, list) or not children:
        return [(node, artifact)]
    leaves: list[tuple[dict[str, Any], Path]] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        raw_artifact = child.get("artifact")
        child_artifact = Path(raw_artifact) if raw_artifact else artifact
        result_file = child_artifact / "result.json"
        child_result, err = read_json(result_file) if result_file.is_file() else (child, None)
        if err or child_result is None:
            leaves.append((child | {"status": "UNREADABLE"}, child_artifact))
        else:
            leaves.extend(group_leaves(child_result, child_artifact))
    return leaves


def replacement_for(artifact: Path) -> tuple[Path | None, dict[str, Any] | None]:
    """Find a later PASS rerun for exactly the same config/suite/seed path."""
    try:
        parts = artifact.resolve().relative_to(ART).parts
    except ValueError:
        return None, None
    if len(parts) < 4:  # config/suite/seed/timestamp
        return None, None
    candidates = []
    for candidate in ART.glob("/".join(parts[:3]) + "/*/result.json"):
        if candidate.resolve() == (artifact / "result.json").resolve() or candidate.stat().st_mtime < (artifact / "result.json").stat().st_mtime:
            continue
        data, err = read_json(candidate)
        if not err and data and str(data.get("status", "")).upper() == "PASS":
            audit = hash_audit(candidate)
            if audit.get("rtl") in ("MATCH", "NOT_RECORDED") and audit.get("tb") in ("MATCH", "NOT_RECORDED"):
                candidates.append((candidate, audit))
    return max(candidates, key=lambda x: x[0].stat().st_mtime) if candidates else (None, None)


def audit_group(entry_data: dict[str, Any]) -> list[dict[str, Any]]:
    artifact = ROOT / entry_data["artifact"]
    leaves = []
    for node, leaf_artifact in group_leaves(entry_data["result"], artifact.parent):
        result_file = leaf_artifact / "result.json"
        audit = hash_audit(result_file) if result_file.is_file() else {"rtl": "NOT_RECORDED", "tb": "NOT_RECORDED", "records": []}
        status = str(node.get("status", "UNKNOWN")).upper()
        current = status == "PASS" and audit.get("rtl") in ("MATCH", "NOT_RECORDED") and audit.get("tb") in ("MATCH", "NOT_RECORDED")
        item = {"artifact": rel(leaf_artifact), "status": status, "hash_audit": audit,
                "current_state": "CURRENT" if current else "STALE_OR_NONPASS"}
        if not current and status == "PASS":
            repl, repl_audit = replacement_for(leaf_artifact)
            if repl:
                item.update(current_state="REPLACED_BY_CURRENT_PASS", replacement_artifact=rel(repl.parent), replacement_hash_audit=repl_audit)
        leaves.append(item)
    return leaves


def historical_nonpass() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(list(ART.rglob("result.json")) + list(ART.rglob("result_sv.json"))):
        data, err = read_json(path)
        if err:
            rows.append({"artifact": rel(path), "status": "UNREADABLE", "classification": "UNREADABLE_JSON", "error": err})
        elif data and str(data.get("status", "UNKNOWN")).upper() != "PASS":
            rows.append({"artifact": rel(path), "status": str(data.get("status", "UNKNOWN")).upper(), "classification": classify_failure(path, data)})
    return rows


def md_status(row: dict[str, Any]) -> str:
    audit = row.get("hash_audit") or {}
    hashes = f"RTL {audit.get('rtl', '—')}; TB {audit.get('tb', '—')}" if audit else "—"
    return f"| {row['label']} | `{row.get('status', '—')}` / {row.get('classification', '—')} | `{row.get('artifact') or '—'}` | {hashes} | {row.get('notes', '')} |"


def main() -> None:
    # Each requested evidence family is explicit, so an absent test is visible.
    entries = [
        entry("Latest all suite", ["overlay_nn1/all/*/*/result.json", "overlay_nn1/all/*/result.json"], notes="Auto-discovers the newest all-suite result; rerun after all completes."),
        *(entry(f"OBI stress seed {seed}", [f"overlay_nn1/obi_stress/{seed}/*/result.json"]) for seed in ("1", "42", "20261020")),
        entry("NN=0 regression", ["overlay_nn0/regression/*/*/result.json"]),
        entry("Frozen FF/PULP=1 regression", ["frozen_ff_pulp1/regression/*/*/result.json"]),
        entry("Original latch smoke", ["frozen_orig_latch/smoke/*/*/result.json"]),
        *(entry(f"Arithmetic primary seed {seed} ALU", ["overlay_nn1/arith_unit/1/*/result.json"] if seed == "1" else [f"arithmetic/seed{seed}/alu/result.json"]) for seed in ("1", "42", "20261020")),
        *(entry(f"Arithmetic primary seed {seed} DOTP", ["overlay_nn1/dotp_unit/1/*/result.json"] if seed == "1" else [f"arithmetic/seed{seed}/dotp/result.json"]) for seed in ("1", "42", "20261020")),
        *(entry(f"Arithmetic supplement seed {seed} ALU", [f"arithmetic/supplement{seed}/alu/result.json"]) for seed in ("1", "42", "20261020")),
        *(entry(f"Arithmetic supplement seed {seed} DOTP", [f"arithmetic/supplement{seed}/dotp/result.json"]) for seed in ("1", "42", "20261020")),
        *(entry(f"Quant unit seed {seed}", [f"quant_unit/seed_{seed}/result_sv.json"]) for seed in ("1", "42", "20261020")),
        entry("LSU unit", ["lsu_unit/**/result.json"], notes="Timestamped structured result required; historical root logs alone are not upgraded to PASS."),
        entry("Controller unit", ["controller_unit/**/result.json"], notes="Timestamped structured result required; historical root logs alone are not upgraded to PASS."),
        entry("72-encoding decoder directed test", ["arithmetic/decoder72/result.json"]),
        entry("Latest decoder runner", ["overlay_nn1/decode/*/*/result.json"], notes="Kept separately so an interrupted current runner cannot hide the directed 72-encoding result."),
        entry("Configuration matrix", ["arithmetic/parameter_matrix/*/result.json", "arithmetic/parameter_matrix/result.json"]),
        static_entry("Independent RTL review", ROOT / "docs" / "results" / "independent-review.md"),
    ]
    nonpass = historical_nonpass()
    all_entry = next(x for x in entries if x["label"] == "Latest all suite")
    if all_entry.get("status") == "PASS" and isinstance(all_entry.get("result"), dict):
        all_entry["leaf_audit"] = audit_group(all_entry)
    else:
        all_entry["leaf_audit"] = []
    required_bad = [x for x in entries if x.get("required") and x.get("status") not in {"PASS", "PRESENT"}]
    stale = [x for x in entries if (x.get("hash_audit") or {}).get("rtl") not in (None, "MATCH", "NOT_RECORDED")]
    stale_tb = [x for x in entries if (x.get("hash_audit") or {}).get("tb") not in (None, "MATCH", "NOT_RECORDED")]
    leaf_bad = [x for x in all_entry["leaf_audit"] if x["current_state"] == "STALE_OR_NONPASS"]
    release = "PASS" if not required_bad and not stale and not stale_tb and not leaf_bad else "INCOMPLETE"
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "release_current_status": release,
               "policy": "PASS requires every requested required artifact to be PASS/PRESENT and recorded RTL hashes to match; TB NOT_RECORDED is disclosed but not silently treated as a match.",
               "entries": entries, "historical_nonpass": nonpass,
               "blocking_entries": [{"label": x["label"], "status": x.get("status"), "artifact": x.get("artifact")} for x in required_bad],
               "stale_rtl_entries": [{"label": x["label"], "artifact": x.get("artifact")} for x in stale],
               "stale_tb_entries": [{"label": x["label"], "artifact": x.get("artifact")} for x in stale_tb],
               "all_leaf_noncurrent": leaf_bad}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# Verification evidence index", "", f"Generated: `{summary['generated_at_utc']}`  ", f"Release-current status: **{release}**.", "",
             "This is an evidence index, not the final validation report. It reads JSON as UTF-8 with BOM support. `NOT_RECORDED` means the historical run manifest omitted that class of source; it is not a hash match.", "",
             "| Evidence | Result | Raw artifact | Current source-hash audit | Notes |", "|---|---|---|---|---|"]
    lines += [md_status(x) for x in entries]
    lines += ["", "## Visible gaps and non-passing history", ""]
    if required_bad:
        lines += [f"- `{x['label']}`: **{x.get('status')}** — `{x.get('artifact') or 'no artifact found'}`." for x in required_bad]
    else:
        lines.append("- No required index entry is currently missing or non-passing.")
    if stale_tb:
        lines += ["", "Current TB hash differs from the recorded artifact (rerun required before calling that evidence current):"]
        lines += [f"- `{x['label']}`: `{x.get('artifact')}`." for x in stale_tb]
    if all_entry["leaf_audit"]:
        lines += ["", "## Latest `all` leaf provenance", "", "| Leaf artifact | Result | RTL/TB audit | Current evidence |", "|---|---|---|---|"]
        for leaf in all_entry["leaf_audit"]:
            a = leaf["hash_audit"]
            current = leaf["current_state"]
            if leaf.get("replacement_artifact"):
                current += f"; replacement `{leaf['replacement_artifact']}`"
            lines.append(f"| `{leaf['artifact']}` | {leaf['status']} | RTL {a.get('rtl')}; TB {a.get('tb')} | {current} |")
    if nonpass:
        lines += ["", "Historical non-PASS JSON artifacts (not suppressed):", "", "| Artifact | Status | Classification |", "|---|---|---|"]
        lines += [f"| `{x['artifact']}` | {x['status']} | {x['classification']} |" for x in nonpass]
    else:
        lines += ["", "No historical non-PASS JSON artifacts were found."]
    lines += ["", "## Interpretation", "", "`EXPECTED_RED_HISTORICAL` identifies explicitly named historical negative/red evidence. `TOOL_FAILURE` identifies an unrunnable/tool-policy result. All other non-PASS results remain `FAIL_OR_INCOMPLETE`. The all-suite entry is selected by newest artifact mtime, so rerunning this script after a complete all-suite run refreshes the index without editing the script.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
