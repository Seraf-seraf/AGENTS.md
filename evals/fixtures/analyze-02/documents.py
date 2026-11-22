def can_read(document, user):
    return user["active"] and document["owner_id"] == user["id"]


def download(document, user):
    if not can_read(document, user):
        raise PermissionError("forbidden")
    return document["body"]


def preview(document, user):
    return download(document, user)[:20]
