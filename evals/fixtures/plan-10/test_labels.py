import unittest
from labels import normalize


class LabelsTest(unittest.TestCase):
    def test_examples(self):
        self.assertEqual(normalize(""), "")
        self.assertEqual(normalize("   "), "")
        self.assertEqual(normalize(" a\t b "), "a b")
