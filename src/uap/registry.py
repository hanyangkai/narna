from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .identity import IdentityStore
from .spec import AgentSpec, load_agent_spec


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AgentRegistry:
    """Phase 3 — local Agent Registry (GitHub for Agents foundation)."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.root = workspace / ".uap" / "registry"
        self.root.mkdir(parents=True, exist_ok=True)

    def register(
        self,
        spec_path: Path,
        *,
        workspace: Path,
        passport: dict[str, Any] | None = None,
        category: str | None = None,
        stars: int = 0,
        downloads: int = 0,
    ) -> dict[str, Any]:
        spec = load_agent_spec(spec_path)
        identity = IdentityStore(workspace).issue(spec)
        caps = list(spec.raw.get("spec", {}).get("capability", []))
        trust = None
        if passport and passport.get("trust"):
            trust = passport["trust"].get("score")

        primary_cap = category or (caps[0] if caps else "general")
        entry: dict[str, Any] = {
            "agentId": spec.agent_id,
            "name": spec.name,
            "version": spec.version,
            "creator": str(spec.raw["metadata"].get("creator", "local")),
            "capabilities": caps,
            "category": primary_cap,
            "trustScore": trust,
            "stars": stars,
            "downloads": downloads,
            "executions": (passport or {}).get("history", {}).get("runCount", 0),
            "specPath": str(spec_path.resolve()),
            "identity": identity,
            "passport": passport,
            "publishedAt": _now(),
            "status": "published",
        }
        # Preserve stars/downloads if re-publishing
        existing = self.get(spec.agent_id)
        if existing:
            entry["stars"] = int(existing.get("stars", stars) or 0)
            entry["downloads"] = int(existing.get("downloads", downloads) or 0)
            if entry["trustScore"] is None:
                entry["trustScore"] = existing.get("trustScore")

        out = self.root / f"{spec.agent_id}.json"
        out.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        shutil.copy(spec_path, self.root / f"{spec.agent_id}.yaml")
        if passport:
            (self.root / f"{spec.agent_id}.passport.json").write_text(
                json.dumps(passport, indent=2), encoding="utf-8"
            )
        return entry

    def get(self, agent_id: str) -> dict[str, Any] | None:
        path = self.root / f"{agent_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def get_passport(self, agent_id: str) -> dict[str, Any] | None:
        path = self.root / f"{agent_id}.passport.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        entry = self.get(agent_id)
        if entry and entry.get("passport"):
            return entry["passport"]
        return None

    def list(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for p in sorted(self.root.glob("*.json")):
            if p.name.endswith(".passport.json"):
                continue
            out.append(json.loads(p.read_text(encoding="utf-8")))
        return out

    def search(self, *, capability: str | None = None, q: str | None = None) -> list[dict[str, Any]]:
        rows = self.list()
        if capability:
            cap = capability.lower()
            rows = [
                r
                for r in rows
                if cap in [c.lower() for c in r.get("capabilities", [])]
                or cap == str(r.get("category", "")).lower()
            ]
        if q:
            needle = q.lower()
            rows = [
                r
                for r in rows
                if needle in str(r.get("name", "")).lower()
                or needle in str(r.get("agentId", "")).lower()
                or needle in str(r.get("creator", "")).lower()
            ]
        return rows

    def trending(self, *, category: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.list()
        if category:
            cat = category.lower()
            rows = [
                r
                for r in rows
                if cat == str(r.get("category", "")).lower()
                or cat in [c.lower() for c in r.get("capabilities", [])]
            ]

        def _rank(r: dict[str, Any]) -> tuple:
            trust = float(r.get("trustScore") or 0)
            stars = int(r.get("stars") or 0)
            downloads = int(r.get("downloads") or 0)
            executions = int(r.get("executions") or 0)
            return (trust, stars, downloads, executions)

        rows.sort(key=_rank, reverse=True)
        return rows[:limit]

    def star(self, agent_id: str) -> dict[str, Any]:
        entry = self.get(agent_id)
        if entry is None:
            raise KeyError(f"agent not found: {agent_id}")
        entry["stars"] = int(entry.get("stars") or 0) + 1
        (self.root / f"{agent_id}.json").write_text(
            json.dumps(entry, indent=2), encoding="utf-8"
        )
        return entry

    def record_download(self, agent_id: str) -> dict[str, Any]:
        entry = self.get(agent_id)
        if entry is None:
            raise KeyError(f"agent not found: {agent_id}")
        entry["downloads"] = int(entry.get("downloads") or 0) + 1
        (self.root / f"{agent_id}.json").write_text(
            json.dumps(entry, indent=2), encoding="utf-8"
        )
        return entry
