"""Integration test: every number in the report must be traceable to results/.

The verifier reads report/generated/*.tex and the result files, and exits 0 only
when all checks pass. Running it as a test means a stale or hand-edited table
breaks the build instead of shipping.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VerifyReportNumbersTest(unittest.TestCase):
    def test_repository_numbers_are_traceable(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_report_numbers.py"), "--root", str(ROOT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            "verifier failed:\n" + result.stdout + result.stderr,
        )
        self.assertIn("0 failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
