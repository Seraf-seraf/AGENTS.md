"""Check the persisted-retry oracle, without claiming an agent passed it."""

import json
from pathlib import Path
import unittest

from test_cases import result_for, workspace


REPO_ROOT = Path(__file__).resolve().parents[2]


class RetryOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = json.loads(
            (REPO_ROOT / "evals/cases/verify-03.json").read_text()
        )
        cls.contract = next(
            check for check in cls.case["checks"]
            if check["id"] == "retry_contract"
        )
        cls.existing_tests = next(
            check for check in cls.case["checks"]
            if check["id"] == "existing_tests"
        )

    def repaired_source(self):
        source = (
            REPO_ROOT / self.case["fixture_dir"] / "submission.py"
        ).read_text()
        boundary = '                state = "retryable"\n'
        self.assertEqual(source.count(boundary), 1)
        return source.replace(boundary, boundary + "                attempts = 0\n")

    def test_oracle_rejects_baseline_with_green_existing_tests(self):
        with workspace(self.case) as root:
            ordinary = result_for(self.existing_tests, root)
            self.assertEqual(ordinary.returncode, 0, ordinary.stderr)
            result = result_for(self.contract, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("next client call after recovery", result.stderr)

    def test_oracle_accepts_a_per_call_budget_with_persistent_outcomes(self):
        with workspace(self.case) as root:
            (root / "submission.py").write_text(self.repaired_source())
            for check in self.case["checks"]:
                with self.subTest(check=check["id"]):
                    result = result_for(check, root)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_oracle_rejects_removing_the_attempt_limit(self):
        source = self.repaired_source().replace(
            "while attempts < MAX_ATTEMPTS_PER_CALL:", "while True:"
        )
        with workspace(self.case) as root:
            (root / "submission.py").write_text(source)
            result = result_for(self.contract, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected dependency call", result.stderr)

    def test_oracle_rejects_repeating_a_successful_effect(self):
        source = self.repaired_source().replace(
            'if state in ("succeeded", "permanent"):',
            'if state == "permanent":',
        )
        with workspace(self.case) as root:
            (root / "submission.py").write_text(source)
            result = result_for(self.contract, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected dependency call", result.stderr)

    def test_oracle_rejects_retrying_a_permanent_failure(self):
        source = self.repaired_source().replace(
            'if state in ("succeeded", "permanent"):',
            'if state == "succeeded":',
        )
        with workspace(self.case) as root:
            (root / "submission.py").write_text(source)
            result = result_for(self.contract, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected dependency call", result.stderr)


if __name__ == "__main__":
    unittest.main()
