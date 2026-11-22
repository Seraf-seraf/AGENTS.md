import unittest
from shipping import fee


class ShippingTest(unittest.TestCase):
    def test_boundary(self):
        self.assertEqual(fee(1000), 200)
        self.assertEqual(fee(1001), 400)
