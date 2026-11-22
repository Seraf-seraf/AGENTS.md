import unittest
from app import format_total


class AmountTest(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_total(0), "0 cents")
