import unittest
from worker import Worker


class WorkerTest(unittest.TestCase):
    def test_starts(self):
        worker = Worker()
        worker.start()
        self.assertEqual(worker.status()["state"], "running")
