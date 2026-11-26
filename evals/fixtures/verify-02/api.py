"""Serialize the artifact catalog response."""

import json

from artifacts import build_artifacts


def list_artifacts_response(records):
    artifacts = build_artifacts(records)
    items = [
        {
            "id": artifact["id"],
            "title": artifact["title"],
            "metadata": {
                "media_type": artifact["metadata"]["media_type"],
            },
        }
        for artifact in artifacts
    ]
    return 200, json.dumps({"data": {"artifacts": items}}, ensure_ascii=False)
