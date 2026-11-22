"""Small argv builders; subprocess management belongs to the runner."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Invocation:
    argv: list[str]
    output_file: Path | None = None


def substitute(argv, values):
    """Replace only known placeholders, without interpreting shell syntax."""
    result = []
    for argument in argv:
        for key, value in values.items():
            argument = argument.replace("{" + key + "}", str(value))
        result.append(argument)
    return result
