"""Local Codex exec adapter, verified against CLI 0.172.0-alpha.2 help."""

import json
import os
from pathlib import Path

from . import Invocation


def external_instruction_files():
    """Find global AGENTS files that would contaminate a standalone trial."""
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    for name in ("AGENTS.override.md", "AGENTS.md"):
        path = codex_home / name
        if path.is_file() and path.stat().st_size:
            return [str(path)]
    return []


def _disabled_user_skills():
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    roots = (codex_home / "skills", Path.home() / ".agents" / "skills")
    paths = set()
    for root in roots:
        if root.is_dir():
            paths.update(str(path.resolve()) for path in root.rglob("SKILL.md"))
    return [
        '{path = ' + json.dumps(path) + ', enabled = false}'
        for path in sorted(paths)
    ]


def build(binary, model, effort, workspace, output_file, state_dir,
          sandbox="workspace-write", schema_file=None):
    """Use invocation-only options; never change HOME or account settings."""
    if not model:
        raise ValueError("Codex trials require an explicit --model")
    contamination = external_instruction_files()
    if contamination:
        raise ValueError(
            "Global AGENTS instructions would contaminate this trial: "
            + ", ".join(contamination)
            + ". Use an isolated execution host; do not change account files."
        )
    argv = [
        binary, "exec", "--ephemeral", "--ignore-user-config", "--strict-config",
        "--disable", "hooks", "--disable", "apps", "--disable", "plugins",
        "--disable", "memories", "--color", "never", "--json",
        "--sandbox", sandbox, "--model", model, "-C", str(workspace),
        "-o", str(output_file),
    ]
    overrides = [
        "skills.bundled.enabled=false",
        "agents.enabled=false",
        'web_search="disabled"',
        'approval_policy="never"',
        'history.persistence="none"',
        "sqlite_home=" + json.dumps(str(state_dir / "state")),
        "log_dir=" + json.dumps(str(state_dir / "logs")),
    ]
    disabled_skills = _disabled_user_skills()
    if disabled_skills:
        overrides.append("skills.config=[" + ",".join(disabled_skills) + "]")
    if effort:
        overrides.append("model_reasoning_effort=" + json.dumps(effort))
    for override in overrides:
        argv.extend(["-c", override])
    if schema_file:
        argv.extend(["--output-schema", str(schema_file)])
    argv.append("-")
    return Invocation(argv, output_file)
