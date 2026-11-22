import unittest
import api


class ApiImportTest(unittest.TestCase):
    def test_import(self):
        self.assertTrue(callable(api.resolve))
