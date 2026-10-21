"""A cached netlist must never substitute a different benchmark ROM."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from run_fpga import validate_checkpoint_inputs


class CheckpointInputs(unittest.TestCase):
    def setUp(self):
        self.run = {'config': 'overlay_nn1', 'stage': 'system_ooc',
                    'sources': [{'original': 'core.sv', 'sha256': 'rtl'},
                                {'original': 'header.svh', 'sha256': 'header'}],
                    'imem.hex_sha256': 'instructions', 'dmem.hex_sha256': 'weights',
                    'signature_digest_words': 400}

    def test_identical_images_allow_new_period_and_paths(self):
        newer = copy.deepcopy(self.run)
        newer.update(clock_period_ns=20, output='new-directory')
        validate_checkpoint_inputs(self.run, newer)

    def test_cached_netlist_rejects_changed_rom_data_digest_or_header(self):
        for key in ('imem.hex_sha256', 'dmem.hex_sha256', 'signature_digest_words'):
            newer = copy.deepcopy(self.run)
            newer[key] = 'different'
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_checkpoint_inputs(self.run, newer)
        newer = copy.deepcopy(self.run)
        newer['sources'][1]['sha256'] = 'changed header'
        with self.assertRaises(ValueError):
            validate_checkpoint_inputs(self.run, newer)


if __name__ == '__main__':
    unittest.main()
