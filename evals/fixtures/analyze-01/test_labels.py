import unittest
from labels import display_name


class LabelsTest(unittest.TestCase):
    def test_whitespace(self):
        self.assertEqual(display_name(" Ada ", "  Lovelace "), "Ada Lovelace")

    def test_empty(self):
        self.assertEqual(display_name("", ""), "")
