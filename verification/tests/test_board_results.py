import copy
import importlib.util
from pathlib import Path
import unittest
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/board_results.py'


class BoardResults(unittest.TestCase):
    def test_published_board_evidence_recomputes_from_raw_captures(self):
        root = SCRIPT.parents[2]
        result = subprocess.run([sys.executable, str(SCRIPT.with_name('summarize_board.py'))],
                                cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_kernel_counters_preserve_high_words_and_reject_baseline_native(self):
        spec = importlib.util.spec_from_file_location('board_results', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        benchmark = {'metrics_offset': 0, 'metrics_per_dataset': 16,
                     'datasets': [{'name': 'test', 'logical_macs': 1, 'nn_physical_lane_macs': 8}]}
        words = [1,1,2,0]*4
        row = module.kernel_metrics(words, benchmark, True)[0]
        self.assertEqual(row['native_cycles'], 4294967297)
        self.assertEqual(row['native_instret'], 2)
        with self.assertRaises(ValueError): module.kernel_metrics(words, benchmark, False)
        words[8:12] = [0]*4
        self.assertEqual(module.kernel_metrics(words, benchmark, False)[0]['native_cycles'], 0)

    def test_rejects_stale_identity_bad_output_and_failed_completion(self):
        self.assertTrue(SCRIPT.exists(), 'board result validator is missing')
        spec = importlib.util.spec_from_file_location('board_results', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        build = {'build_id': '1234abcd', 'config': 'overlay_nn1', 'status': 'PASS'}
        expected = [1, 2, None]
        good = {'build_id': '1234abcd', 'usr_access': '1234abcd', 'status': 19,
                'count': 3, 'signature': 34, 'elapsed_cycles': 20, 'words': [1, 2, 999]}
        self.assertEqual(module.validate_capture(build, expected, good), [])
        for key, value in [('build_id','deadbeef'), ('usr_access','deadbeef'), ('status',17),
                           ('status',27), ('count',2), ('signature',0), ('elapsed_cycles',0),
                           ('words',[1,3,999]), ('words',[1,2])]:
            bad = copy.deepcopy(good)
            bad[key] = value
            self.assertTrue(module.validate_capture(build, expected, bad), key)
        failed_build = dict(build, status='FAIL')
        self.assertTrue(module.validate_capture(failed_build, expected, good))


if __name__ == '__main__':
    unittest.main()
