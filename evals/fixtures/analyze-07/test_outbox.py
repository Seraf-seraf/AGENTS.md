import unittest
from outbox import connect, save_order


class OutboxTest(unittest.TestCase):
    def test_order_and_task(self):
        connection = connect()
        save_order(connection, "o1")
        self.assertEqual(connection.execute("SELECT id FROM tasks").fetchall(), [("o1",)])
        connection.close()
