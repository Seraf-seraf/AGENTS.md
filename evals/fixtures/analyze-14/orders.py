def list_orders(rows, status=None):
    return [row for row in rows if row["status"] != "deleted" and (status is None or row["status"] == status)]
