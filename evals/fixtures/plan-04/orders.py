def submit(order, store, services):
    store.append(dict(order))
    return order["id"]
