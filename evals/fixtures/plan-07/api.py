def status():
    return {"status": "ok"}


ROUTES = [("/status", status)]


def resolve(path):
    for route, handler in ROUTES:
        if path == route:
            return handler()
    raise KeyError(path)
