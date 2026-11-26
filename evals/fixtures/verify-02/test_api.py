"""Existing response smoke tests."""

import json
import unittest

from api import list_artifacts_response


class ArtifactApiTest(unittest.TestCase):

    def test_lists_stored_artifact(self):
        records = [{
            "id": "document-1",
            "title": "Guide",
            "media_type": "application/pdf",
            "revision": 1,
            "byte_length": 4096,
        }]

        status, body = list_artifacts_response(records)
        items = json.loads(body)["data"]["artifacts"]

        self.assertEqual(status, 200)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], "document-1")
        self.assertEqual(items[0]["title"], "Guide")
        self.assertEqual(items[0]["metadata"]["media_type"], "application/pdf")

    def test_empty_catalog(self):
        status, body = list_artifacts_response([])

        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"data": {"artifacts": []}})


if __name__ == "__main__":
    unittest.main()
