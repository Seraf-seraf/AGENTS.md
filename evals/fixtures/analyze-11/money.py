def format_cents(value):
    if type(value) is not int:
        raise TypeError("integer cents required")
    sign = "-" if value < 0 else ""
    major, minor = divmod(abs(value), 100)
    return f"{sign}{major}.{minor:02d}"
