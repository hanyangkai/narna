from __future__ import annotations

import json
import shutil
from pathlib import Path

from .identity import IdentityStore
from .spec import AgentSpec, load_agent_spec


class AgentRegistry:
    """V5 foundation — local agent + identity registry."""

    def __init__(self, workspace: Path) -> None:
        self.root = workspace / ".uap" / "registry"
        self.root.mkdir(parents=True, exist_ok=True)

    def register(self, spec_path: Path, *, workspace: Path) -> dict:
        spec = load_agent_spec(spec_path)
        identity = IdentityStore(workspace).issue(spec)
        entry = {
            "agentId": spec.agent_id,
            "name": spec.name,
            "version": spec.version,
            "specPath": str(spec_path.resolve()),
            "identity": identity,
        }
        out = self.root / f"{spec.agent_id}.json"
        out.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        shutil.copy(spec_path, self.root / f"{spec.agent_id}.yaml")
        return entry

    def get(self, agent_id: str) -> dict | None:
        path = self.root / f"{agent_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self) -> list[dict]:
        out = []
        for p in self.root.glob("*.json"):
            out.append(json.loads(p.read_text(encoding="utf-8")))
        return out
