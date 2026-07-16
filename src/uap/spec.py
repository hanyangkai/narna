from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from .schemas import validator_for


@dataclass(frozen=True)
class AgentSpec:
    raw: dict[str, Any]

    @property
    def agent_id(self) -> str:
        return str(self.raw["metadata"]["id"])

    @property
    def name(self) -> str:
        return str(self.raw["metadata"]["name"])

    @property
    def version(self) -> str:
        return str(self.raw["metadata"]["version"])


def load_agent_spec(path: str | Path) -> AgentSpec:
    p = Path(path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("AgentSpec must be a mapping/document object")
    validator = validator_for("agent-spec.schema.json")
    errors = sorted(validator.iter_errors(raw), key=lambda e: e.path)
    if errors:
        lines = []
        for e in errors[:20]:
            loc = "/".join(str(x) for x in e.path) or "<root>"
            lines.append(f"{loc}: {e.message}")
        more = "" if len(errors) <= 20 else f"\n... and {len(errors) - 20} more"
        raise ValueError("AgentSpec validation failed:\n" + "\n".join(lines) + more)
    return AgentSpec(raw=raw)

