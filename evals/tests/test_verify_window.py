"""Check the evaluator for a pre-existing test that contradicts its contract."""

import unittest

from test_cases import REPO_ROOT, result_for, workspace
from runner import load_cases


class WindowOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = next(case for case in load_cases(REPO_ROOT)
                        if case["id"] == "verify-01")
        cls.checks = {check["id"]: check for check in cls.case["checks"]}

    def test_green_baseline_still_violates_independent_requirement(self):
        with workspace(self.case) as root:
            self.assertEqual(result_for(self.checks["project_tests"], root).returncode, 0)
            self.assertNotEqual(result_for(self.checks["window_contract"], root).returncode, 0)

    def test_correct_behavior_and_corrected_test_are_both_required(self):
        with workspace(self.case) as root:
            implementation = root / "availability.py"
            implementation.write_text(implementation.read_text().replace(
                "starts_at <= now <= ends_at", "starts_at <= now < ends_at",
            ))
            self.assertEqual(result_for(self.checks["window_contract"], root).returncode, 0)
            self.assertNotEqual(result_for(self.checks["project_tests"], root).returncode, 0)

            tests = root / "test_availability.py"
            tests.write_text(tests.read_text().replace(
                "self.assertTrue(is_open(10, 20, 20))",
                "self.assertFalse(is_open(10, 20, 20))",
            ))
            for check in self.case["checks"]:
                with self.subTest(check=check["id"]):
                    result = result_for(check, root)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_oracle_rejects_closing_both_boundaries(self):
        with workspace(self.case) as root:
            implementation = root / "availability.py"
            implementation.write_text(implementation.read_text().replace(
                "starts_at <= now <= ends_at", "starts_at < now < ends_at",
            ))
            self.assertNotEqual(result_for(self.checks["window_contract"], root).returncode, 0)

    def test_changing_requirement_does_not_hide_defect(self):
        with workspace(self.case) as root:
            contract = root / "README.md"
            contract.write_text(contract.read_text().replace(
                "Конец окна исключительно", "Конец окна включительно",
            ))
            self.assertNotEqual(result_for(self.checks["requirements_unchanged"], root).returncode, 0)
            self.assertNotEqual(result_for(self.checks["window_contract"], root).returncode, 0)


if __name__ == "__main__":
    unittest.main()
