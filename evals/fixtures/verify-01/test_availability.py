import unittest

from availability import is_open


class AvailabilityTest(unittest.TestCase):
    def test_before_start(self):
        self.assertFalse(is_open(10, 20, 9))

    def test_at_start(self):
        self.assertTrue(is_open(10, 20, 10))

    def test_inside_window(self):
        self.assertTrue(is_open(10, 20, 15))

    def test_at_end(self):
        self.assertTrue(is_open(10, 20, 20))

    def test_after_end(self):
        self.assertFalse(is_open(10, 20, 21))

    def test_cancelled_event(self):
        self.assertFalse(is_open(10, 20, 15, cancelled=True))


if __name__ == "__main__":
    unittest.main()
