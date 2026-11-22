import sqlite3
import unittest
from pathlib import Path


class SchemaTest(unittest.TestCase):
    def test_schema(self):
        connection = sqlite3.connect(":memory:")
        connection.executescript(Path("schema.sql").read_text())
        connection.close()
