import unittest
import adapter


class ImportTest(unittest.TestCase):
    def test_import(self):
        self.assertTrue(callable(adapter.save_record))
