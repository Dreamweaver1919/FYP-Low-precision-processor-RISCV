import pathlib
import json
import re
import subprocess
import sys
import unittest

from scripts.check_public_repository import normalize


ROOT = pathlib.Path(__file__).resolve().parents[2]


class PublicRepositoryBoundary(unittest.TestCase):
    def test_delivery_manifest_uses_no_machine_absolute_path(self):
        """A public integrity manifest must be portable across contributors' machines."""
        manifest = json.loads((ROOT / "artifacts/delivery/source-manifest.json").read_text())
        self.assertNotRegex(json.dumps(manifest), r"[A-Za-z]:\\")

    def test_release_evidence_uses_only_tracked_portable_references(self):
        """Published evidence must not point a fresh clone to a local FPGA run directory."""
        evidence = json.loads((ROOT / "artifacts/delivery/release-evidence.json").read_text())
        payload = json.dumps(evidence)
        self.assertNotRegex(payload, r"[A-Za-z]:\\")
        self.assertEqual(evidence["fpga_summary"], "artifacts/fpga/summary.json")

    def test_published_validation_report_links_resolve_in_index(self):
        """Every relative evidence link in the public validation report survives cloning."""
        report = ROOT / "docs/results/xpulpnn-route-a-validation.md"
        tracked = set(subprocess.run(
            ["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True
        ).stdout.splitlines())
        for target in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", report.read_text(encoding="utf-8")):
            if "://" in target:
                continue
            resolved = (report.parent / target).resolve().relative_to(ROOT.resolve()).as_posix()
            self.assertIn(resolved, tracked, f"untracked report link: {target}")

    def test_normalize_preserves_dot_prefixed_repository_paths(self):
        """Stripping a relative prefix must not turn .gitignore into gitignore."""
        self.assertEqual(normalize("./.gitignore"), ".gitignore")
        self.assertEqual(normalize(".github/workflows/verify.yml"), ".github/workflows/verify.yml")

    def test_current_index_meets_complete_publication_contract(self):
        """A clone must contain every document and evidence file the README needs."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_public_repository.py"), "--index"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_checker_accepts_required_publishable_paths(self):
        """A publish boundary must preserve RTL, licenses, summaries and fixed ROM."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_public_repository.py"), "--paths", "\n".join((
                "rtl/nn/cv32e40p_nn_quant.sv",
                "vendor/cv32e40p/LICENSE",
                "artifacts/verification/summary.json",
                "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/imem.hex",
                "artifacts/verification/overlay_nn1/bench/1/20261021-114500-136671/dmem.hex",
            ))],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_checker_rejects_generated_and_run_specific_paths(self):
        """A tracked tool artifact would make the public repository non-reproducible."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_public_repository.py"), "--paths", "\n".join((
                "FYP.runs/run.log", "FYP.cache/x", "foo.dcp", "xsim.log", "a.jou", "a.pb",
                "verification/__pycache__/x.pyc",
                "artifacts/verification/overlay_nn1/bench/1/run/result.json",
            ))],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forbidden", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
