import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


class PublicRepositoryBoundary(unittest.TestCase):
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
