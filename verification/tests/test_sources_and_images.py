import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


class FrozenSources(unittest.TestCase):
    def test_snapshot_is_complete_and_immutable(self):
        manifest = json.loads((ROOT / 'vendor/cv32e40p/SOURCE.json').read_text())
        self.assertGreater(len(manifest['files']), 100)
        for entry in manifest['files']:
            path = ROOT / entry['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'], str(path))

    def test_original_project_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT / 'FYP.xpr').read_bytes()).hexdigest(),
                         '9d348bcda279dbd563006ed12d1ae816f06b0ff66022e54145c753f7af3f0e82')


if __name__ == '__main__':
    unittest.main()
