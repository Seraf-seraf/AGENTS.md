"""Check the response oracle with controls, without claiming model quality."""

import json
import sys
import unittest

from test_cases import REPO_ROOT, result_for, run, workspace


DIRECT_RESPONSE = '''"""Serialize the declared artifact response."""

import json

from artifacts import build_artifacts


def list_artifacts_response(records):
    return 200, json.dumps(
        {"data": {"artifacts": build_artifacts(records)}}, ensure_ascii=False,
    )
'''

HARDCODED_RESPONSE = '''import json


def list_artifacts_response(records):
    items = [{
        "id": "document-1",
        "title": "Guide",
        "metadata": {
            "media_type": "application/pdf",
            "byte_length": 4096,
            "revision": 1,
        },
    }] if records else []
    return 200, json.dumps({"data": {"artifacts": items}})
'''


class ResponseOracleTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.case = json.loads(
            (REPO_ROOT / "evals" / "cases" / "verify-02.json").read_text(),
        )
        cls.checks = {check["id"]: check for check in cls.case["checks"]}

    def check_result(self, root, check_id):
        return result_for(self.checks[check_id], root)

    def assert_check_passes(self, root, check_id):
        result = self.check_result(root, check_id)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_response_rejected(self, root):
        result = self.check_result(root, "serialized_response_contract")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AssertionError", result.stderr)

    def test_partial_smoke_tests_pass_but_response_oracle_rejects_baseline(self):
        with workspace(self.case) as root:
            self.assert_check_passes(root, "project_tests")
            self.assert_check_passes(root, "declared_contract_preserved")
            self.assert_response_rejected(root)

    def test_minimal_serializer_fix_passes(self):
        with workspace(self.case) as root:
            path = root / "api.py"
            path.write_text(path.read_text().replace(
                '"media_type": artifact["metadata"]["media_type"],',
                '"media_type": artifact["metadata"]["media_type"],\n'
                '                "byte_length": artifact["metadata"]["byte_length"],\n'
                '                "revision": artifact["metadata"]["revision"],',
            ))
            self.assert_check_passes(root, "serialized_response_contract")
            self.assert_check_passes(root, "declared_contract_preserved")
            self.assert_check_passes(root, "project_tests")

    def test_different_correct_implementation_also_passes(self):
        with workspace(self.case) as root:
            (root / "api.py").write_text(DIRECT_RESPONSE)
            self.assert_check_passes(root, "serialized_response_contract")
            self.assert_check_passes(root, "declared_contract_preserved")
            self.assert_check_passes(root, "project_tests")

    def test_upstream_only_changes_do_not_satisfy_response_oracle(self):
        with workspace(self.case) as root:
            path = root / "artifacts.py"
            path.write_text(path.read_text().replace(
                '"title": row["title"],',
                '"title": row["title"],\n'
                '            "byte_length": row["byte_length"],\n'
                '            "revision": row["revision"],',
            ))
            self.assert_response_rejected(root)
            self.assert_check_passes(root, "declared_contract_preserved")

    def weaken_contract(self, root):
        path = root / "openapi.json"
        contract = json.loads(path.read_text())
        schemas = contract["components"]["schemas"]
        schemas["ArtifactMetadata"]["allOf"] = []
        schemas["FileMetadata"]["required"] = ["media_type"]
        path.write_text(json.dumps(contract))

    def test_contract_only_change_does_not_satisfy_the_checks(self):
        with workspace(self.case) as root:
            self.weaken_contract(root)
            self.assert_response_rejected(root)
            guard = self.check_result(root, "declared_contract_preserved")
            self.assertNotEqual(guard.returncode, 0)
            self.assertIn("AssertionError", guard.stderr)

    def test_guard_rejects_contract_weakening_even_with_correct_response(self):
        with workspace(self.case) as root:
            (root / "api.py").write_text(DIRECT_RESPONSE)
            self.weaken_contract(root)
            self.assert_check_passes(root, "serialized_response_contract")
            guard = self.check_result(root, "declared_contract_preserved")
            self.assertNotEqual(guard.returncode, 0)

    def test_guard_accepts_json_formatting_without_contract_changes(self):
        with workspace(self.case) as root:
            path = root / "openapi.json"
            path.write_text(json.dumps(json.loads(path.read_text())))
            self.assert_check_passes(root, "declared_contract_preserved")

    def test_guard_rejects_boolean_numeric_constraint(self):
        with workspace(self.case) as root:
            path = root / "openapi.json"
            contract = json.loads(path.read_text())
            properties = contract["components"]["schemas"]["FileMetadata"]["properties"]
            properties["byte_length"]["minimum"] = False
            path.write_text(json.dumps(contract))
            guard = self.check_result(root, "declared_contract_preserved")
            self.assertNotEqual(guard.returncode, 0)
            self.assertIn("AssertionError", guard.stderr)

    def test_guard_accepts_equivalent_numeric_constraint(self):
        with workspace(self.case) as root:
            path = root / "openapi.json"
            contract = json.loads(path.read_text())
            properties = contract["components"]["schemas"]["FileMetadata"]["properties"]
            properties["byte_length"]["minimum"] = 0.0
            path.write_text(json.dumps(contract))
            self.assert_check_passes(root, "declared_contract_preserved")

    def test_hardcoded_sample_passes_smoke_but_fails_independent_inputs(self):
        with workspace(self.case) as root:
            (root / "api.py").write_text(HARDCODED_RESPONSE)
            run([sys.executable, "-m", "unittest", "-v"], root)
            self.assert_response_rejected(root)

    def test_boolean_false_cannot_replace_zero_byte_length(self):
        with workspace(self.case) as root:
            (root / "api.py").write_text(
                'import json\n'
                'from artifacts import build_artifacts\n\n'
                'def list_artifacts_response(records):\n'
                '    items = build_artifacts(records)\n'
                '    for item in items:\n'
                '        metadata = item["metadata"]\n'
                '        metadata["byte_length"] = metadata["byte_length"] or False\n'
                '    return 200, json.dumps({"data": {"artifacts": items}})\n'
            )
            self.assert_response_rejected(root)

    def test_boolean_true_cannot_replace_revision_one(self):
        with workspace(self.case) as root:
            (root / "api.py").write_text(
                'import json\n'
                'from artifacts import build_artifacts\n\n'
                'def list_artifacts_response(records):\n'
                '    items = build_artifacts(records)\n'
                '    for item in items:\n'
                '        metadata = item["metadata"]\n'
                '        if metadata["revision"] == 1:\n'
                '            metadata["revision"] = True\n'
                '    return 200, json.dumps({"data": {"artifacts": items}})\n'
            )
            self.assert_response_rejected(root)

    def test_openapi_30_integer_rejects_fractional_json_notation(self):
        # OpenAPI 3.0.3 section 4.4 defines integer without a fraction/exponent.
        # https://spec.openapis.org/oas/v3.0.3.html#data-types
        with workspace(self.case) as root:
            (root / "api.py").write_text(
                'import json\n'
                'from artifacts import build_artifacts\n\n'
                'def list_artifacts_response(records):\n'
                '    items = build_artifacts(records)\n'
                '    for item in items:\n'
                '        metadata = item["metadata"]\n'
                '        for field in ("byte_length", "revision"):\n'
                '            metadata[field] = float(metadata[field])\n'
                '    return 200, json.dumps({"data": {"artifacts": items}})\n'
            )
            self.assert_response_rejected(root)
            self.assert_check_passes(root, "declared_contract_preserved")
            self.assert_check_passes(root, "project_tests")


if __name__ == "__main__":
    unittest.main()
