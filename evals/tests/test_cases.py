"""Corpus integrity and behavioral-oracle checks, without claiming model quality."""

import contextlib
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "evals"))
from runner import load_cases, validate_case, validate_cases  # noqa: E402


ANALYZE_SOURCE = ".agents/skills/analyze-change/references/calibration-scenarios.md"
PLAN_SOURCE = ".agents/skills/write-implementation-plan/references/calibration-scenarios.md"
VERIFY_SOURCE = ".agents/skills/verify-change/references/calibration-scenarios.md"


def run(argv, cwd, expected_exit=0):
    result = subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, timeout=15,
    )
    if result.returncode != expected_exit:
        raise AssertionError(
            f"{argv!r}: expected {expected_exit}, got {result.returncode}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


@contextlib.contextmanager
def workspace(case):
    """Use a real disposable Git repository for state/ownership assertions."""
    with tempfile.TemporaryDirectory(prefix="agent-eval-case-test-") as directory:
        root = Path(directory) / "workspace"
        shutil.copytree(REPO_ROOT / case["fixture_dir"], root)
        run(["git", "init", "-q"], root)
        run(["git", "config", "user.name", "Fixture Test"], root)
        run(["git", "config", "user.email", "fixture@example.invalid"], root)
        run(["git", "add", "."], root)
        run(["git", "commit", "-qm", "Fixture baseline"], root)
        yield root


def result_for(check, root):
    return subprocess.run(
        check["argv"], cwd=root / check.get("cwd", "."),
        text=True, capture_output=True, timeout=check.get("timeout_seconds", 10),
    )


class CaseCorpusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(REPO_ROOT)
        cls.by_id = {case["id"]: case for case in cls.cases}

    def test_one_case_per_calibration_scenario(self):
        expected_ids = {f"analyze-{number:02d}" for number in range(1, 17)}
        expected_ids.update(f"plan-{number:02d}" for number in range(1, 11))
        expected_ids.update(f"verify-{number:02d}" for number in range(1, 4))
        self.assertEqual(set(self.by_id), expected_ids)
        sources = {"analyze": ANALYZE_SOURCE, "plan": PLAN_SOURCE, "verify": VERIFY_SOURCE}
        mappings = set()
        for case in self.cases:
            with self.subTest(case=case["id"]):
                source = case["source"]
                expected_source = sources[case["id"].split("-")[0]]
                self.assertEqual(source["path"], expected_source)
                self.assertEqual(source["scenario"], int(case["id"].split("-")[1]))
                key = (source["path"], source["scenario"])
                self.assertNotIn(key, mappings)
                mappings.add(key)
                lines = (REPO_ROOT / source["path"]).read_text().splitlines()
                original = lines[source["line_start"] - 1]
                self.assertEqual(source["line_end"], source["line_start"])
                self.assertTrue(original.startswith("| "))
                self.assertEqual(original.split("|")[1].strip(), source["condition"])

    def test_fixtures_and_trusted_commands_are_parseable(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                fixture = REPO_ROOT / case["fixture_dir"]
                self.assertTrue(any(path.is_file() for path in fixture.rglob("*")))
                self.assertIn("__pycache__/", (fixture / ".gitignore").read_text())
                self.assertFalse(list(fixture.rglob("calibration-scenarios.md")))
                self.assertFalse((fixture / ".git").exists())
                for path in fixture.rglob("*.py"):
                    compile(path.read_text(), str(path), "exec")
                commands = case.get("checks", []) + case.get("setup", [])
                for stage in case.get("stages", []):
                    commands += stage.get("checks", []) + stage.get("setup", [])
                for command in commands:
                    self.assertTrue((fixture / command.get("cwd", ".")).is_dir())
                    if command["argv"][:2] == ["python3", "-c"]:
                        compile(command["argv"][2], case["id"] + ":" + command["id"], "exec")

    def test_existing_fixture_tests_run_without_external_dependencies(self):
        for case in self.cases:
            with self.subTest(case=case["id"]), workspace(case) as root:
                if list(root.glob("test_*.py")):
                    run([sys.executable, "-m", "unittest", "discover", "-v"], root)
                elif case["id"] == "analyze-08":
                    run([sys.executable, "smoke.py"], root)

    def test_planner_and_executor_are_distinct_stages(self):
        for number in range(1, 11):
            case = self.by_id[f"plan-{number:02d}"]
            with self.subTest(case=case["id"]):
                self.assertGreaterEqual(len(case["stages"]), 2)
                first = case["stages"][0]
                self.assertEqual(first["id"], "plan")
                self.assertTrue(first.get("checks"))
                self.assertTrue(any("{plan}" in stage["prompt"] or "{previous_output}" in stage["prompt"]
                                    for stage in case["stages"][1:]))

    def test_judgment_has_external_semantic_criteria(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                criteria = case["rubric"]["criteria"]
                self.assertTrue(criteria)
                self.assertTrue(all(item["expectation"].strip() for item in criteria))
                self.assertNotIn("keywords", case["rubric"])
                self.assertNotIn("contains", case["rubric"])
                # The complete hidden criterion is never installed as fixture content.
                for path in (REPO_ROOT / case["fixture_dir"]).rglob("*"):
                    if path.is_file():
                        content = path.read_bytes()
                        for criterion in criteria:
                            self.assertNotIn(criterion["expectation"].encode("utf-8"), content)

    def test_readonly_cases_accept_baseline_and_reject_source_edits(self):
        for case_id in ["analyze-03", "analyze-16"]:
            case = self.by_id[case_id]
            check = next(item for item in case["checks"] if item["id"] == "fixture_files_unchanged")
            with self.subTest(case=case_id), workspace(case) as root:
                self.assertEqual(result_for(check, root).returncode, 0)
                source = next(root.glob("*.py"))
                source.write_text(source.read_text() + "\nUNREQUESTED = True\n")
                self.assertNotEqual(result_for(check, root).returncode, 0)

    def test_filter_oracle_rejects_unimplemented_and_wrong_selection(self):
        case = self.by_id["analyze-13"]
        check = case["checks"][0]
        with workspace(case) as root:
            self.assertNotEqual(result_for(check, root).returncode, 0)
            (root / "orders.py").write_text(
                "def list_orders(rows, status=None):\n"
                "    return [dict(row) for row in rows if status is None or row['status'] == status]\n"
            )
            self.assertEqual(result_for(check, root).returncode, 0)
            (root / "orders.py").write_text(
                "def list_orders(rows, status=None):\n"
                "    return [dict(row) for row in rows]\n"
            )
            self.assertNotEqual(result_for(check, root).returncode, 0)

    def test_existing_service_oracle_rejects_duplicate_service(self):
        case = self.by_id["plan-04"]
        check = case["checks"][0]
        with workspace(case) as root:
            self.assertNotEqual(result_for(check, root).returncode, 0)
            (root / "orders.py").write_text(
                "def submit(order, store, services):\n"
                "    store.append(dict(order))\n"
                "    services.notifications.send('order_created', {'order_id': order['id']})\n"
                "    return order['id']\n"
            )
            self.assertEqual(result_for(check, root).returncode, 0)
            (root / "orders.py").write_text(
                "from services import Services\n"
                "def submit(order, store, services):\n"
                "    store.append(dict(order))\n"
                "    Services().notifications.send('order_created', {'order_id': order['id']})\n"
                "    return order['id']\n"
            )
            self.assertNotEqual(result_for(check, root).returncode, 0)

    def test_mixed_file_oracle_distinguishes_own_commit_from_whole_file(self):
        from runner import snapshot

        case = self.by_id["plan-08"]
        check = case["checks"][0]
        own_version = (
            'APP_TITLE = "orders"\n'
            'APP_LOCALE = "en"\n\n\n'
            'def format_total(cents):\n'
            '    sign = "-" if cents < 0 else ""\n'
            '    major, minor = divmod(abs(cents), 100)\n'
            '    return f"USD {sign}{major}.{minor:02d}"\n'
        )
        indexed_version = own_version.replace('"en"', '"ru"')
        working_version = indexed_version.replace('"orders"', '"warehouse"')
        variants = {
            "preserved": (own_version, indexed_version, working_version),
            "commit_staged": (indexed_version, indexed_version, working_version),
            "erase_staged": (
                own_version, own_version, working_version.replace('"ru"', '"en"'),
            ),
            "unstage_foreign": (own_version, own_version, working_version),
            "commit_unstaged": (
                own_version.replace('"orders"', '"warehouse"'), working_version, working_version,
            ),
            "erase_unstaged": (own_version, indexed_version, indexed_version),
            "stage_foreign_unstaged": (own_version, working_version, working_version),
            "commit_whole_file": (working_version, working_version, working_version),
        }

        def write_index(root, content):
            blob = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"], cwd=root,
                input=content, text=True, capture_output=True, check=True,
            ).stdout.strip()
            run(["git", "update-index", "--cacheinfo", f"100644,{blob},app.py"], root)

        for variant, (committed, indexed, working) in variants.items():
            with self.subTest(variant=variant), workspace(case) as root:
                for setup in case["setup"]:
                    result = result_for(setup, root)
                    self.assertEqual(result.returncode, 0, result.stderr)
                head = run(["git", "show", "HEAD:app.py"], root).stdout
                initial_index = run(["git", "show", ":app.py"], root).stdout
                initial_working = (root / "app.py").read_text()
                self.assertIn('APP_TITLE = "orders"', head)
                self.assertIn('APP_LOCALE = "en"', head)
                self.assertIn('APP_TITLE = "orders"', initial_index)
                self.assertIn('APP_LOCALE = "ru"', initial_index)
                self.assertIn('APP_TITLE = "warehouse"', initial_working)
                self.assertIn('APP_LOCALE = "ru"', initial_working)

                baseline = root.parent / "baseline"
                snapshot(root, baseline)
                planning_checks = copy.deepcopy(case["stages"][0]["checks"])
                for planning_check in planning_checks:
                    planning_check["argv"] = [
                        argument.replace("{baseline_dir}", str(baseline))
                        for argument in planning_check["argv"]
                    ]
                    result = result_for(planning_check, root)
                    self.assertEqual(result.returncode, 0, result.stderr)
                index_check = next(
                    item for item in planning_checks if item["id"] == "planning_kept_index"
                )
                write_index(root, head)
                self.assertNotEqual(result_for(index_check, root).returncode, 0)
                write_index(root, initial_index)

                write_index(root, committed)
                run(["git", "commit", "-qm", "Format assigned amount"], root)
                write_index(root, indexed)
                (root / "app.py").write_text(working)
                result = result_for(check, root)
                self.assertEqual(result.returncode == 0, variant == "preserved", result.stderr)


class CaseValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.valid = load_cases(REPO_ROOT)[0]

    def assert_invalid(self, transform):
        case = copy.deepcopy(self.valid)
        transform(case)
        with self.assertRaises(ValueError):
            validate_case(case, REPO_ROOT)

    def test_invalid_core_fields_and_paths(self):
        mutations = [
            lambda case: case.update(id="../escape"),
            lambda case: case.update(kind="anything"),
            lambda case: case.update(prompt="  "),
            lambda case: case.update(schema_version=99),
            lambda case: case.update(fixture_dir="/tmp"),
            lambda case: case.update(fixture_dir="evals/fixtures/../cases"),
            lambda case: case.update(fixture_dir="evals/fixtures/missing-case"),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_invalid(mutation)

    def test_invalid_commands(self):
        invalid = [
            {"argv": "python3 -c pass"},
            {"argv": []},
            {"argv": ["python3", 3]},
            {"argv": ["python3", "\0"]},
            {"argv": ["true"], "cwd": "../outside"},
            {"argv": ["true"], "timeout_seconds": 0},
            {"argv": ["true"], "timeout_seconds": "fast"},
            {"argv": ["true"], "timeout_seconds": True},
            {"argv": ["true"], "expected_exit": "0"},
            {"argv": ["true"], "expected_exit": True},
        ]
        for command in invalid:
            with self.subTest(command=command):
                self.assert_invalid(lambda case: case.update(checks=[command]))

    def test_duplicate_and_malformed_stages_criteria_and_limits(self):
        stage = {"id": "same", "prompt": "A normal task"}
        criterion = {"id": "same", "expectation": "A semantic outcome"}
        mutations = [
            lambda case: case.update(stages=[stage, stage]),
            lambda case: case.update(stages="invalid"),
            lambda case: case.update(stages=[{"id": "empty", "prompt": ""}]),
            lambda case: case.update(rubric={"criteria": [criterion, criterion]}),
            lambda case: case.update(rubric={"criteria": "invalid"}),
            lambda case: case.update(rubric=[]),
            lambda case: case.update(limits=[]),
            lambda case: case.update(limits={"timeout_seconds": True}),
            lambda case: case.update(limits={"max_output_bytes": 0}),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_invalid(mutation)

    def test_duplicate_case_ids(self):
        with self.assertRaises(ValueError):
            validate_cases([self.valid, copy.deepcopy(self.valid)], REPO_ROOT)

    def test_symlinked_fixture_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="eval-schema-test-") as directory:
            root = Path(directory)
            fixture = root / "evals" / "fixtures" / "sample"
            fixture.mkdir(parents=True)
            (root / "outside.txt").write_text("outside")
            (fixture / "linked.txt").symlink_to(root / "outside.txt")
            case = copy.deepcopy(self.valid)
            case["fixture_dir"] = "evals/fixtures/sample"
            with self.assertRaises(ValueError):
                validate_case(case, root)


if __name__ == "__main__":
    unittest.main()
