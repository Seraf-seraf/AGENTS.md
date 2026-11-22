def checkout(store, analytics, order):
    analytics.track("order_created", order["id"])
    store.append(dict(order))
    return {"order_id": order["id"], "saved": True}
