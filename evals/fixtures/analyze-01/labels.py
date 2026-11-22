def _normalize(value):
    return " ".join(value.split())


def display_name(first, last):
    return _normalize(f"{first} {last}")
