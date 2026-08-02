"""Every environment variable the agent reads must be documented in .env.example."""

from __future__ import annotations

import re

from tests.conftest import REPO_ROOT

ENV_CALL = re.compile(r'(?:os\.getenv|require_env|env_or|env_int)\(\s*"([A-Z][A-Z0-9_]*)"')


def test_all_agent_env_vars_documented() -> None:
    documented = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    used: set[str] = set()
    for path in (REPO_ROOT / "agent").rglob("*.py"):
        used.update(ENV_CALL.findall(path.read_text(encoding="utf-8")))
    assert used, "expected the agent to read at least one env variable"
    missing = sorted(var for var in used if var not in documented)
    assert not missing, f".env.example is missing documentation for: {missing}"
