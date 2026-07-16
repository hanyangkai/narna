from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import AgentRegistry


class Marketplace:
    """Capability index + trending views over the Agent Registry."""

    def __init__(self, workspace: Path) -> None:
        self.root = workspace / ".uap" / "marketplace"
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry = AgentRegistry(workspace)

    def index(self) -> dict[str, list[dict]]:
        index: dict[str, list[dict]] = {}
        for entry in self.registry.list():
            caps = entry.get("capabilities") or []
            listing = {
                "agentId": entry["agentId"],
                "name": entry["name"],
                "version": entry["version"],
                "capabilities": caps,
                "category": entry.get("category"),
                "trustScore": entry.get("trustScore"),
                "stars": entry.get("stars", 0),
                "downloads": entry.get("downloads", 0),
            }
            for cap in caps:
                index.setdefault(cap, []).append(listing)
            if not caps:
                index.setdefault("general", []).append(listing)
            manifest_path = self.root / f"{entry['agentId']}.json"
            manifest_path.write_text(json.dumps(listing, indent=2), encoding="utf-8")
        index_path = self.root / "index.json"
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
        return index

    def search(self, capability: str) -> list[dict]:
        return self.registry.search(capability=capability)

    def trending(self, *, category: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.registry.trending(category=category, limit=limit)
        (self.root / "trending.json").write_text(
            json.dumps({"category": category, "agents": rows}, indent=2),
            encoding="utf-8",
        )
        return rows
