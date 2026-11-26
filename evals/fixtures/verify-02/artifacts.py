"""Build the application representation from canonical storage records."""


def build_artifacts(records):
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "metadata": {
                "media_type": row["media_type"],
                "byte_length": row["byte_length"],
                "revision": row["revision"],
            },
        }
        for row in records
    ]
