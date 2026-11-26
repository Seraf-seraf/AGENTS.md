"""Availability of a scheduled event."""


def is_open(starts_at, ends_at, now, cancelled=False):
    return not cancelled and starts_at <= now <= ends_at
