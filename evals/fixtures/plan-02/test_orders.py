import unittest
from orders import list_orders


class OrdersTest(unittest.TestCase):
    def test_records(self):
        rows = [{"id": "a", "status": "open"}]
        self.assertEqual(list_orders(rows), rows)
