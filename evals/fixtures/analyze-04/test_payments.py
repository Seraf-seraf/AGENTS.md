import unittest
from payments import Gateway


class GatewayTest(unittest.TestCase):
    def test_duplicate_id(self):
        gateway = Gateway()
        gateway.charge("p1", 100)
        gateway.charge("p1", 100)
        self.assertEqual(len(gateway.records), 1)
