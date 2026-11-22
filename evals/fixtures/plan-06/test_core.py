import unittest
from core import greeting


class CoreTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(greeting("Ada"), "Hi, Ada!")
