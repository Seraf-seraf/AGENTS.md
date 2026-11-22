import unittest
from api import get_document


class ApiTest(unittest.TestCase):
    def test_owner(self):
        rows = [{"id": "d1", "tenant_id": "t1", "attachment": "private"}]
        self.assertEqual(get_document(rows, "d1", {"tenant_id": "t1"})["id"], "d1")
