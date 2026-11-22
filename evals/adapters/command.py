"""Adapter for a trusted command supplied as a JSON argv array."""

from . import Invocation, substitute


def build(argv, workspace, prompt_file, output_file, schema_file=None):
    """Send the prompt on stdin; optionally collect a declared output file."""
    values = {
        "workspace": workspace,
        "prompt_file": prompt_file,
        "output_file": output_file,
        "schema_file": schema_file or "",
    }
    uses_output_file = any("{output_file}" in argument for argument in argv)
    return Invocation(
        substitute(argv, values), output_file if uses_output_file else None
    )
