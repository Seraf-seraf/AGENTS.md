import unittest
from checkout import checkout


class Analytics:
    def track(self, event, order_id):
        pass


class CheckoutTest(unittest.TestCase):
    def test_saved(self):
        rows = []
        result = checkout(rows, Analytics(), {"id": "o1"})
        self.assertTrue(result["saved"])
        self.assertEqual(len(rows), 1)
