import unittest
import receipt
import totals


class ImportTest(unittest.TestCase):
    def test_imports(self):
        self.assertTrue(callable(receipt.render))
        self.assertTrue(callable(totals.total_cents))
