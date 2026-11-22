def list_orders(rows):
    return [{"id": row["id"]} for row in rows]
