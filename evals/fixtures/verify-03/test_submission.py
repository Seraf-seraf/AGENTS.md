"""Checks for ordinary submission outcomes."""

from pathlib import Path
import tempfile
import unittest

from submission import PermanentFailure, SubmissionService, TemporaryFailure


class SubmissionTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "submissions.sqlite3"

    def test_success_is_persisted_for_another_service(self):
        calls = []

        def dependency(key):
            calls.append(key)
            return "receipt-a"

        expected = {"status": "succeeded", "receipt": "receipt-a"}
        first = SubmissionService(self.database, dependency)
        self.assertEqual(first.submit("a"), expected)
        second = SubmissionService(self.database, dependency)
        self.assertEqual(second.submit("a"), expected)
        self.assertEqual(calls, ["a"])

    def test_one_temporary_failure_can_recover_in_the_same_call(self):
        calls = []

        def dependency(key):
            calls.append(key)
            if len(calls) == 1:
                raise TemporaryFailure()
            return "receipt-b"

        result = SubmissionService(self.database, dependency).submit("b")
        self.assertEqual(result, {"status": "succeeded", "receipt": "receipt-b"})
        self.assertEqual(calls, ["b", "b"])

    def test_exhausted_call_returns_retryable(self):
        calls = []

        def dependency(key):
            calls.append(key)
            if len(calls) > 2:
                self.fail("Attempt budget exceeded")
            raise TemporaryFailure()

        result = SubmissionService(self.database, dependency).submit("c")
        self.assertEqual(result, {"status": "retryable", "receipt": None})
        self.assertEqual(calls, ["c", "c"])

    def test_permanent_failure_stops_immediately(self):
        calls = []

        def dependency(key):
            calls.append(key)
            raise PermanentFailure()

        result = SubmissionService(self.database, dependency).submit("d")
        self.assertEqual(result, {"status": "permanent", "receipt": None})
        self.assertEqual(calls, ["d"])


if __name__ == "__main__":
    unittest.main()
