def list_orders(rows):
    return [row for row in rows if row["status"] != "deleted" and row["active"]]


def export_ids(rows):
    return [row["id"] for row in list_orders(rows)]
