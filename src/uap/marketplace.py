from __future__ import annotations

import json
from pathlib import Path

from .registry import AgentRegistry


class Marketplace:
    """V4 foundation — capability-indexed agent discovery."""

    def __init__(self, workspace: Path) -> None:
        self.root = workspace / ".uap" / "marketplace"
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry = AgentRegistry(workspace)

    def index(self) -> dict[str, list[dict]]:
        index: dict[str, list[dict]] = {}
        for entry in self.registry.list():
            spec_path = Path(entry["specPath"])
            if not spec_path.exists():
                alt = self.registry.root / f"{entry['agentId']}.yaml"
                spec_path = alt
            from .spec import load_agent_spec

            spec = load_agent_spec(spec_path)
            caps = spec.raw.get("spec", {}).get("capability", [])
            listing = {
                "agentId": entry["agentId"],
                "name": entry["name"],
                "version": entry["version"],
                "capabilities": caps,
            }
            for cap in caps:
                index.setdefault(cap, []).append(listing)
            manifest_path = self.root / f"{entry['agentId']}.json"
            manifest_path.write_text(json.dumps(listing, indent=2), encoding="utf-8")
        index_path = self.root / "index.json"
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        return index

    def search(self, capability: str) -> list[dict]:
        index_path = self.root / "index.json"
        if not index_path.exists():
            self.index()
        index = json.loads(index_path.read_text(encoding="utf-8"))
        return index.get(capability, [])
