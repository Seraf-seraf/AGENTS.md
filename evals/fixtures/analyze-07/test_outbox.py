import os
import sqlite3
import tempfile
import unittest
from outbox import connect, deliver, save_order


class Receiver:
    def __init__(self):
        self.unavailable = False
        self.attempts = []
        self.notifications = []

    def send_once(self, task_id):
        self.attempts.append(task_id)
        if self.unavailable:
            raise ConnectionError("receiver unavailable")
        if task_id not in self.notifications:
            self.notifications.append(task_id)


class OutboxTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        original_directory = os.getcwd()
        os.chdir(directory.name)
        self.addCleanup(os.chdir, original_directory)

    def open_connection(self):
        connection = connect()
        self.addCleanup(connection.close)
        return connection

    def test_order_and_task(self):
        connection = self.open_connection()
        save_order(connection, "o1")
        self.assertEqual(
            connection.execute("SELECT id FROM orders").fetchall(), [("o1",)],
        )
        self.assertEqual(
            connection.execute("SELECT id, done FROM tasks").fetchall(), [("o1", 0)],
        )

    def test_reopen_delivers_saved_task_and_keeps_it_done(self):
        connection = self.open_connection()
        save_order(connection, "o1")
        connection.close()
        reopened = self.open_connection()
        self.assertEqual(
            reopened.execute("SELECT id FROM orders").fetchall(), [("o1",)],
        )
        self.assertEqual(
            reopened.execute("SELECT id, done FROM tasks").fetchall(), [("o1", 0)],
        )
        receiver = Receiver()
        deliver(reopened, receiver)
        self.assertEqual(receiver.notifications, ["o1"])
        reopened.close()
        completed = self.open_connection()
        self.assertEqual(
            completed.execute("SELECT id, done FROM tasks").fetchall(), [("o1", 1)],
        )
        deliver(completed, receiver)
        self.assertEqual(receiver.attempts, ["o1"])

    def test_task_insert_error_rolls_back_order(self):
        connection = self.open_connection()
        with connection:
            connection.execute("INSERT INTO tasks(id) VALUES (?)", ("o1",))
        with self.assertRaises(sqlite3.IntegrityError):
            save_order(connection, "o1")
        connection.close()
        reopened = self.open_connection()
        self.assertEqual(reopened.execute("SELECT id FROM orders").fetchall(), [])
        self.assertEqual(
            reopened.execute("SELECT id, done FROM tasks").fetchall(), [("o1", 0)],
        )

    def test_receiver_error_leaves_task_for_retry(self):
        connection = self.open_connection()
        save_order(connection, "o1")
        receiver = Receiver()
        receiver.unavailable = True
        with self.assertRaises(ConnectionError):
            deliver(connection, receiver)
        self.assertEqual(receiver.notifications, [])
        connection.close()
        reopened = self.open_connection()
        self.assertEqual(
            reopened.execute("SELECT id, done FROM tasks").fetchall(), [("o1", 0)],
        )
        receiver.unavailable = False
        deliver(reopened, receiver)
        self.assertEqual(receiver.notifications, ["o1"])
        self.assertEqual(receiver.attempts, ["o1", "o1"])
        self.assertEqual(
            reopened.execute("SELECT done FROM tasks").fetchall(), [(1,)],
        )

    def test_ack_error_retries_without_duplicate_notification(self):
        connection = self.open_connection()
        save_order(connection, "o1")
        connection.executescript(
            "CREATE TEMP TRIGGER reject_ack BEFORE UPDATE ON tasks "
            "BEGIN SELECT RAISE(ABORT, 'ack unavailable'); END;"
        )
        receiver = Receiver()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "ack unavailable"):
            deliver(connection, receiver)
        self.assertEqual(receiver.notifications, ["o1"])
        connection.close()
        reopened = self.open_connection()
        self.assertEqual(
            reopened.execute("SELECT id, done FROM tasks").fetchall(), [("o1", 0)],
        )
        deliver(reopened, receiver)
        self.assertEqual(receiver.notifications, ["o1"])
        self.assertEqual(receiver.attempts, ["o1", "o1"])
        self.assertEqual(
            reopened.execute("SELECT done FROM tasks").fetchall(), [(1,)],
        )
