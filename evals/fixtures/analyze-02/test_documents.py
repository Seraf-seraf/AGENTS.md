import unittest
from documents import download


class DocumentTest(unittest.TestCase):
    def test_owner(self):
        document = {"owner_id": "u1", "body": "private"}
        self.assertEqual(download(document, {"id": "u1", "active": True}), "private")
