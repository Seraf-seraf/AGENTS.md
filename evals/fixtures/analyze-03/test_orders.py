import unittest
from orders import export_ids


class ExportTest(unittest.TestCase):
    def test_active_order(self):
        self.assertEqual(export_ids([{"id": "a", "status": "active", "active": True}]), ["a"])
