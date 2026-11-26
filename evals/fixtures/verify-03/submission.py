"""Persist the outcome of a sequential submission."""

from collections.abc import Callable
import contextlib
from pathlib import Path
import sqlite3


MAX_ATTEMPTS_PER_CALL = 2


class TemporaryFailure(Exception):
    """The dependency rejected this attempt before its effect."""


class PermanentFailure(Exception):
    """The operation cannot be accepted with this key."""


class SubmissionService:
    def __init__(
        self, database: str | Path, dependency: Callable[[str], str]
    ) -> None:
        self.database = database
        self.dependency = dependency

    def submit(self, key: str) -> dict[str, str | None]:
        with contextlib.closing(sqlite3.connect(self.database)) as connection:
            with connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS submissions ("
                    "request_key TEXT PRIMARY KEY, state TEXT NOT NULL, "
                    "attempts INTEGER NOT NULL, receipt TEXT)"
                )
                connection.execute(
                    "INSERT OR IGNORE INTO submissions VALUES (?, ?, 0, NULL)",
                    (key, "pending"),
                )
                state, attempts, receipt = connection.execute(
                    "SELECT state, attempts, receipt FROM submissions "
                    "WHERE request_key = ?",
                    (key,),
                ).fetchone()
                if state in ("succeeded", "permanent"):
                    return {"status": state, "receipt": receipt}

                state = "retryable"
                while attempts < MAX_ATTEMPTS_PER_CALL:
                    attempts += 1
                    try:
                        receipt = self.dependency(key)
                    except TemporaryFailure:
                        continue
                    except PermanentFailure:
                        state = "permanent"
                        break
                    else:
                        state = "succeeded"
                        break
                connection.execute(
                    "UPDATE submissions SET state = ?, attempts = ?, "
                    "receipt = ? WHERE request_key = ?",
                    (state, attempts, receipt, key),
                )
                return {"status": state, "receipt": receipt}
