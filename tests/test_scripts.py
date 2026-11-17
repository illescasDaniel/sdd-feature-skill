"""Offline behavior checks for the SDD helper scripts."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills' / 'sdd-feature' / 'scripts'

class ScriptTests(unittest.TestCase):
    def test_preview_contains_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            design = Path(tmp) / 'DESIGN.md'
            design.write_text('# My design\n\nA design for safe review.\n')
            run = subprocess.run([sys.executable, str(SCRIPTS / 'design_preview.py'), str(design)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('My design', (Path(tmp) / 'preview.html').read_text())

    def test_spec_checker_rejects_incomplete_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / 'SPEC.md'
            spec.write_text('# Incomplete\n')
            run = subprocess.run([sys.executable, str(SCRIPTS / 'spec_check.py'), str(spec), '--root', tmp], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            self.assertIn('FAIL', run.stdout)

if __name__ == '__main__':
    unittest.main()
