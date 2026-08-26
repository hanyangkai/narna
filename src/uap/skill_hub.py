"""Skill Hub — OpenClaw/ClawHub-like shared skill index (v0)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SkillHub:
    """Tenant-local hub that can export/import portable skill packs."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "skill-hub"
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "index.json"

    def _read(self) -> dict[str, Any]:
        if not self.index.exists():
            return {"skills": [], "standard": "NGS-0029-skill-hub"}
        return json.loads(self.index.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.index.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def list_public(self) -> list[dict[str, Any]]:
        return list(self._read().get("skills") or [])

    def publish(
        self,
        *,
        name: str,
        body: str,
        tags: list[str] | None = None,
        author: str | None = None,
        skill_id: str | None = None,
    ) -> dict[str, Any]:
        name = (name or "").strip()
        body = (body or "").strip()
        if not name or not body:
            raise ValueError("name and body required")
        sid = skill_id or new_id("hub")
        row = {
            "skillId": sid,
            "name": name,
            "body": body[:12000],
            "tags": tags or [],
            "author": author or "anonymous",
            "publishedAt": _now(),
            "downloads": 0,
            "standard": "agentskills.io-compatible-v0",
        }
        (self.root / f"{sid}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        idx = self._read()
        skills = [s for s in (idx.get("skills") or []) if s.get("skillId") != sid]
        skills.append(
            {
                "skillId": sid,
                "name": name,
                "tags": row["tags"],
                "author": row["author"],
                "publishedAt": row["publishedAt"],
            }
        )
        idx["skills"] = skills[-500:]
        self._write(idx)
        return row

    def get(self, skill_id: str) -> dict[str, Any] | None:
        path = self.root / f"{skill_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def install_to_store(self, skill_id: str, *, skills: Any) -> dict[str, Any]:
        row = self.get(skill_id)
        if not row:
            raise KeyError(skill_id)
        installed = skills.save(
            name=str(row["name"]),
            body=str(row["body"]),
            tags=list(row.get("tags") or []) + ["hub"],
        )
        # bump downloads
        row["downloads"] = int(row.get("downloads") or 0) + 1
        (self.root / f"{skill_id}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        return installed
