def get_document(rows, document_id, session):
    row = next(row for row in rows if row["id"] == document_id)
    if row["tenant_id"] != session["tenant_id"]:
        raise PermissionError("forbidden")
    return row


def list_documents(rows, session):
    return list(rows)


def download_attachment(rows, document_id, session):
    row = next(row for row in rows if row["id"] == document_id)
    return row["attachment"]
