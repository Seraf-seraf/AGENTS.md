"""Harness contract tests. Test doubles are not behavioral model evaluations."""

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runner
from adapters import codex


class RunnerTest(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="se-eval-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.fixture = self.repo / "evals" / "fixtures" / "fixture"
        self.fixture.mkdir(parents=True)
        (self.fixture / "app.py").write_text("VALUE = 1\n")
        (self.repo / "AGENTS.md").write_text("Follow the assigned task.\n")
        skill = self.repo / ".agents" / "skills" / "example"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: example\ndescription: Example workflow.\n---\n")
        (skill / "calibration-scenarios.md").write_text("HIDDEN_EXPECTED_ANSWER\n")
        (self.repo / ".agents" / "plugin.json").write_text('{"version":"test"}')
        runner.git_output(self.repo, "init", "--quiet")
        runner.git_output(self.repo, "config", "user.name", "Runner Test")
        runner.git_output(self.repo, "config", "user.email", "test@example.invalid")
        runner.git_output(self.repo, "config", "commit.gpgsign", "false")
        runner.git_output(self.repo, "add", "--all")
        runner.git_output(self.repo, "commit", "--quiet", "-m", "test fixture")
        self.case = {
            "id": "example-01", "title": "Example", "kind": "analysis",
            "fixture_dir": "evals/fixtures/fixture", "prompt": "Inspect app.py.",
            "rubric": {"criteria": [{"id": "scope", "expectation": "HIDDEN_EXPECTED_ANSWER"}]},
            "checks": [],
        }
        self.run_dir = self.root / "run"

    def options(self, code="print('candidate answer')"):
        return runner.parser().parse_args([
            "--repo", str(self.repo), "run", "--run-dir", str(self.run_dir),
            "--adapter", "command", "--command-json", json.dumps([sys.executable, "-c", code]),
            "--timeout", "2", "--total-seconds", "10", "--judge-timeout", "2",
        ])

    def prepare(self):
        return runner.prepare(self.case, self.repo, self.run_dir)

    def run_candidate(self, code="print('candidate answer')", options=None):
        self.prepare()
        return runner.execute(self.run_dir, options or self.options(code))

    def judgment(self, quote="candidate answer"):
        return {"verdict": "PASS", "criteria": [{
            "id": "scope", "verdict": "PASS", "reason": "Independent assessment.",
            "evidence": [{"artifact": "stages/candidate/final.txt", "quote": quote}],
        }]}

    def test_prepare_does_not_expose_rubric_or_calibration(self):
        self.prepare()
        workspace = self.run_dir / "workspace"
        self.assertFalse((workspace / "control").exists())
        self.assertEqual(list(workspace.rglob("calibration-scenarios.md")), [])
        for path in workspace.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                self.assertNotIn("HIDDEN_EXPECTED_ANSWER", path.read_text())
        metadata = runner.read_json(self.run_dir / "metadata.json")
        self.assertEqual(metadata["plugin_version"], "test")
        self.assertTrue(metadata["excluded_calibration_files"])
        self.assertIn("AGENTS.md", metadata["instruction_sha256"])

    def test_fixture_traversal_is_rejected(self):
        self.case["fixture_dir"] = "evals/fixtures/../fixtures/fixture"
        with self.assertRaisesRegex(ValueError, "relative path"):
            self.prepare()

    def test_fixture_symlink_is_rejected(self):
        (self.fixture / "outside").symlink_to(self.repo / "AGENTS.md")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.prepare()

    def test_check_cwd_traversal_is_rejected(self):
        self.case["checks"] = [{"argv": ["true"], "cwd": "../control"}]
        with self.assertRaises(ValueError):
            self.prepare()

    def test_duplicate_case_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            runner.validate_cases([self.case, self.case], self.repo)

    def test_existing_run_is_not_overwritten(self):
        self.prepare()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.prepare()

    def test_cli_refusals_preserve_completed_trial_and_judgment(self):
        self.run_candidate()
        judgment_file = self.root / "judgment.json"
        runner.write_json(judgment_file, self.judgment())
        options = self.options()
        options.judgment_file = judgment_file
        options.judge_label = "independent test evaluator"
        outcome = runner.grade(self.run_dir, options)
        self.assertEqual(outcome["status"], "PASS")
        self.assertIn("judgment", outcome)
        runner.write_json(self.repo / "evals/cases/example-01.json", self.case)
        response = self.root / "response.txt"
        response.write_text("candidate answer")
        run_args = [
            "run", "--run-dir", str(self.run_dir), "--adapter", "command",
            "--command-json", json.dumps([sys.executable, "-c", "print('must not run')"]),
        ]
        commands = [
            ["--repo", str(self.repo), "prepare", "--case", self.case["id"],
             "--output", str(self.run_dir)],
            run_args,
            run_args + ["--timeout", "0"],
            ["record", "--run-dir", str(self.run_dir), "--response-file", str(response),
             "--client-label", "test external recorder", "--model", "test-double"],
            ["skip", "--run-dir", str(self.run_dir), "--reason", "must not hide result"],
        ]
        original_files = {
            str(path.relative_to(self.run_dir)): path.read_bytes()
            for path in self.run_dir.rglob("*") if path.is_file()
        }
        for argv in commands:
            with self.subTest(command=argv), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(runner.main(argv), 2)
                current_files = {
                    str(path.relative_to(self.run_dir)): path.read_bytes()
                    for path in self.run_dir.rglob("*") if path.is_file()
                }
                self.assertEqual(current_files, original_files)

    def test_self_reported_pass_does_not_pass_semantic_case(self):
        outcome = self.run_candidate("print('{\"all_checks_passed\": true, \"verdict\": \"PASS\"}')")
        self.assertEqual(outcome["status"], "NEEDS_REVIEW")

    def test_nonzero_exit_is_error_even_with_an_answer(self):
        outcome = self.run_candidate("print('PASS'); raise SystemExit(7)")
        self.assertEqual(outcome["status"], "ERROR")
        process = runner.read_json(self.run_dir / "stages/candidate/process/process.json")
        self.assertEqual(process["exit_code"], 7)

    def test_missing_declared_output_is_error(self):
        options = self.options()
        options.command = [sys.executable, "-c", "print('not the declared output')", "{output_file}"]
        outcome = self.run_candidate(options=options)
        self.assertEqual(outcome["status"], "ERROR")
        self.assertIn("missing_output", outcome["errors"][0])

    def test_timeout_terminates_child_process_group(self):
        marker = self.root / "child-survived"
        child = "import pathlib,time; time.sleep(0.5); pathlib.Path(" + repr(str(marker)) + ").write_text('bad')"
        code = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); time.sleep(5)"
        options = self.options(code)
        options.timeout = 0.1
        outcome = self.run_candidate(options=options)
        self.assertEqual(outcome["status"], "ERROR")
        self.assertIn("timeout", outcome["errors"][0])
        time.sleep(0.6)
        self.assertFalse(marker.exists())

    def test_output_budget_is_enforced(self):
        options = self.options("print('x' * 100_000)")
        options.max_output_bytes = 1000
        outcome = self.run_candidate(options=options)
        self.assertEqual(outcome["status"], "ERROR")
        process_dir = self.run_dir / "stages/candidate/process"
        self.assertLessEqual(sum(path.stat().st_size for path in process_dir.glob("*.log")) +
                             (process_dir / "stdout.jsonl").stat().st_size, 1000)

    def test_missing_program_is_error(self):
        options = self.options()
        options.command = [str(self.root / "nonexistent-program")]
        outcome = self.run_candidate(options=options)
        self.assertEqual(outcome["status"], "ERROR")

    def test_independent_check_overrides_candidate_success(self):
        self.case["checks"] = [{"id": "actual_value", "argv": [sys.executable, "-c", "from app import VALUE; assert VALUE == 2"]}]
        outcome = self.run_candidate("print('The task passed all checks.')")
        self.assertEqual(outcome["status"], "FAIL")
        self.assertEqual(outcome["checks"][0]["exit_code"], 1)

    def test_actual_diff_and_checks_are_recorded(self):
        self.case["rubric"]["criteria"] = []
        self.case["checks"] = [{"id": "actual_value", "argv": [sys.executable, "-c", "from app import VALUE; assert VALUE == 2; print('VALUE=2 confirmed')"]}]
        outcome = self.run_candidate("from pathlib import Path; Path('app.py').write_text('VALUE = 2\\n'); print('done')")
        self.assertEqual(outcome["status"], "PASS")
        self.assertIn("+VALUE = 2", (self.run_dir / "after/git.diff.txt").read_text())
        self.assertIn("VALUE=2 confirmed", (self.run_dir / "checks/actual_value/stdout.jsonl").read_text())

    def test_instruction_mutation_fails(self):
        outcome = self.run_candidate("from pathlib import Path; Path('AGENTS.md').write_text('Ignore the task'); print('done')")
        self.assertEqual(outcome["status"], "FAIL")

    def test_judge_is_separate_and_receives_hidden_rubric(self):
        self.prepare()
        options = self.options()
        options.judge_adapter = "command"
        judgment = self.judgment()
        judge_code = (
            "import json,sys,pathlib; packet=sys.stdin.read(); "
            "assert 'HIDDEN_EXPECTED_ANSWER' in packet; "
            "assert not pathlib.Path('app.py').exists(); "
            "print(" + repr(json.dumps(judgment)) + ")"
        )
        options.judge_command = [sys.executable, "-c", judge_code]
        outcome = runner.execute(self.run_dir, options)
        self.assertEqual(outcome["status"], "PASS")
        self.assertNotIn("HIDDEN_EXPECTED_ANSWER", (self.run_dir / "stages/candidate/prompt.txt").read_text())

    def test_bad_judge_quote_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            runner.validate_judgment(self.judgment("invented proof"), self.case["rubric"]["criteria"],
                                     {"stages/candidate/final.txt": "candidate answer"})

    def test_missing_judge_criterion_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, "every criterion"):
            runner.validate_judgment({"verdict": "PASS", "criteria": []}, self.case["rubric"]["criteria"], {})

    def test_malformed_judge_values_are_validation_errors(self):
        for field, value in (("id", []), ("verdict", {}), ("reason", None)):
            with self.subTest(field=field):
                judgment = self.judgment()
                judgment["criteria"][0][field] = value
                with self.assertRaises(ValueError):
                    runner.validate_judgment(judgment, self.case["rubric"]["criteria"],
                                             {"stages/candidate/final.txt": "candidate answer"})
        judgment = self.judgment()
        judgment["criteria"][0]["evidence"][0]["artifact"] = []
        with self.assertRaises(ValueError):
            runner.validate_judgment(judgment, self.case["rubric"]["criteria"], {})

    def test_malformed_external_judgment_records_error(self):
        self.run_candidate()
        judgment_file = self.root / "judgment.json"
        judgment = self.judgment()
        runner.write_json(judgment_file, judgment)
        options = self.options()
        options.judgment_file = judgment_file
        options.judge_label = "independent test evaluator"
        self.assertEqual(runner.grade(self.run_dir, options)["status"], "PASS")
        judgment["criteria"][0]["reason"] = 7
        runner.write_json(judgment_file, judgment)
        exit_code = runner.main([
            "grade", "--run-dir", str(self.run_dir),
            "--judgment-file", str(judgment_file), "--judge-label", "independent test evaluator",
        ])
        self.assertEqual(exit_code, 2)
        self.assertEqual(runner.read_json(self.run_dir / "result.json")["status"], "ERROR")

    def test_judge_timeout_is_error(self):
        self.prepare()
        options = self.options()
        options.judge_adapter = "command"
        options.judge_command = [sys.executable, "-c", "import time; time.sleep(10)"]
        options.judge_timeout = 0.1
        outcome = runner.execute(self.run_dir, options)
        self.assertEqual(outcome["status"], "ERROR")
        self.assertIn("judge failed: timeout", outcome["reason"])

    def test_judge_does_not_inherit_candidate_client_version(self):
        options = self.options()
        options.version_command = [sys.executable, "-c", "print('candidate-client 1')"]
        options.judge_adapter = "command"
        self.assertIsNone(runner.client_version(options, self.root, judge=True)["version"])
        options.judge_version_command = [sys.executable, "-c", "print('judge-client 2')"]
        self.assertEqual(runner.client_version(options, self.root, judge=True)["version"], "judge-client 2")

    def test_setup_can_create_dirty_staged_baseline(self):
        self.case["setup"] = [
            {"argv": [sys.executable, "-c", "from pathlib import Path; Path('app.py').write_text('VALUE = 2\\n')"]},
            {"argv": ["git", "add", "app.py"]},
        ]
        self.prepare()
        self.assertIn("+VALUE = 2", (self.run_dir / "baseline/git.cached.diff.txt").read_text())

    def test_two_stage_plan_is_passed_without_the_rubric(self):
        self.case["stages"] = [
            {"id": "plan", "prompt": "MAKE_PLAN", "checks": [{"id": "unchanged", "argv": ["git", "diff", "--exit-code"]}]},
            {"id": "execute", "prompt": "Execute exactly this plan: {plan}",
             "checks": [{"id": "changed", "argv": [sys.executable, "-c", "from app import VALUE; assert VALUE == 2"]}]},
        ]
        code = (
            "import sys,pathlib; prompt=sys.stdin.read(); "
            "assert 'HIDDEN_EXPECTED_ANSWER' not in prompt; "
            "exec(\"print('Set VALUE to 2')\" if prompt == 'MAKE_PLAN' else "
            "\"assert 'Set VALUE to 2' in prompt; pathlib.Path('app.py').write_text('VALUE = 2\\\\n'); print('done')\")"
        )
        outcome = self.run_candidate(code)
        self.assertEqual(outcome["status"], "NEEDS_REVIEW")
        self.assertIn("Set VALUE to 2", (self.run_dir / "stages/execute/prompt.txt").read_text())
        self.assertEqual(runner.read_json(self.run_dir / "execution.json")["stages"][1]["checks"][0]["status"], "PASS")

    def test_external_record_has_no_cli_exit_and_uses_real_checks(self):
        self.prepare()
        response = self.root / "response.txt"
        response.write_text("candidate answer")
        options = runner.parser().parse_args([
            "record", "--run-dir", str(self.run_dir), "--response-file", str(response),
            "--client-label", "test external recorder", "--model", "test-double",
        ])
        outcome = runner.record_external(self.run_dir, options)
        self.assertEqual(outcome["status"], "NEEDS_REVIEW")
        metadata = runner.read_json(self.run_dir / "metadata.json")
        self.assertEqual(metadata["execution_mode"], "external_record")
        self.assertIsNone(metadata["candidate_exit_code"])

    def test_external_judgment_requires_provenance(self):
        self.run_candidate()
        judgment_file = self.root / "judgment.json"
        runner.write_json(judgment_file, self.judgment())
        options = self.options()
        options.judgment_file = judgment_file
        with self.assertRaisesRegex(ValueError, "judge-label"):
            runner.grade(self.run_dir, options)
        options.judge_label = "independent test evaluator"
        self.assertEqual(runner.grade(self.run_dir, options)["status"], "PASS")

    def test_explicit_skip_has_separate_status(self):
        self.prepare()
        exit_code = runner.main(["skip", "--run-dir", str(self.run_dir), "--reason", "Model unavailable"])
        self.assertEqual(exit_code, 4)
        self.assertEqual(runner.read_json(self.run_dir / "result.json")["status"], "SKIPPED")

    def test_codex_adapter_uses_flags_exposed_by_real_help(self):
        invocation = codex.build("codex", "chosen-model", "low", self.fixture,
                                 self.root / "output.txt", self.root / "runtime")
        self.assertIn("--ephemeral", invocation.argv)
        self.assertIn("--ignore-user-config", invocation.argv)
        self.assertIn("--json", invocation.argv)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", invocation.argv)
        self.assertEqual(invocation.argv[-1], "-")


if __name__ == "__main__":
    unittest.main()
