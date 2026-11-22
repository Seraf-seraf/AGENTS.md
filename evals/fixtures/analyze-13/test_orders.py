import unittest
from orders import list_orders


class OrdersTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(list_orders([]), [])
