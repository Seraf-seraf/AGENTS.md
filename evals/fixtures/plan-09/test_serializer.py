import unittest
from serializer import encode


class SerializerTest(unittest.TestCase):
    def test_id(self):
        self.assertEqual(encode({"id": "o1"})["id"], "o1")
