import unittest
from money import format_cents


class MoneyTest(unittest.TestCase):
    def test_values(self):
        for value, expected in [(0, "0.00"), (1, "0.01"), (-101, "-1.01"), (10 ** 20, "1000000000000000000.00")]:
            self.assertEqual(format_cents(value), expected)

    def test_types(self):
        for value in [True, 1.5, "100", None]:
            with self.assertRaises(TypeError):
                format_cents(value)
