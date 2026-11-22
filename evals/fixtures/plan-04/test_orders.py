import unittest
from orders import submit
from services import Services


class OrderTest(unittest.TestCase):
    def test_saved(self):
        store = []
        self.assertEqual(submit({"id": "o1"}, store, Services()), "o1")
        self.assertEqual(store, [{"id": "o1"}])
