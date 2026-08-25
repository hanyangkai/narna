"""Agent skills store — Hermes-like reusable procedures (v0)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s[:48] or "skill"


class SkillStore:
    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "skills"
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "index.json"

    def _read_index(self) -> dict[str, Any]:
        if not self.index.exists():
            return {"skills": []}
        return json.loads(self.index.read_text(encoding="utf-8"))

    def _write_index(self, data: dict[str, Any]) -> None:
        self.index.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def list_skills(self) -> list[dict[str, Any]]:
        return list(self._read_index().get("skills") or [])

    def get(self, skill_id: str) -> dict[str, Any] | None:
        path = self.root / f"{skill_id}.json"
        if not path.exists():
            # try slug match in index
            for meta in self.list_skills():
                if meta.get("skillId") == skill_id or meta.get("slug") == skill_id:
                    path = self.root / f"{meta['skillId']}.json"
                    break
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(
        self,
        *,
        name: str,
        body: str,
        tags: list[str] | None = None,
        skill_id: str | None = None,
        improve_note: str | None = None,
    ) -> dict[str, Any]:
        sid = skill_id or new_id("skill")
        existing = self.get(sid)
        uses = int((existing or {}).get("uses") or 0)
        row = {
            "skillId": sid,
            "slug": _slug(name),
            "name": name,
            "body": body,
            "tags": tags or [],
            "uses": uses,
            "createdAt": (existing or {}).get("createdAt") or _now(),
            "updatedAt": _now(),
            "improveNote": improve_note,
            "standard": "NGS-0029-skills",
        }
        (self.root / f"{sid}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        idx = self._read_index()
        skills = [s for s in (idx.get("skills") or []) if s.get("skillId") != sid]
        skills.append(
            {
                "skillId": sid,
                "slug": row["slug"],
                "name": name,
                "tags": row["tags"],
                "updatedAt": row["updatedAt"],
            }
        )
        idx["skills"] = skills[-500:]
        self._write_index(idx)
        return row

    def bump_use(self, skill_id: str) -> None:
        row = self.get(skill_id)
        if not row:
            return
        row["uses"] = int(row.get("uses") or 0) + 1
        row["updatedAt"] = _now()
        (self.root / f"{skill_id}.json").write_text(
            json.dumps(row, indent=2) + "\n", encoding="utf-8"
        )

    def maybe_capture_from_answer(
        self,
        *,
        question: str,
        answer: str,
        dqs: int | None,
    ) -> dict[str, Any] | None:
        """Auto-save a skill stub when DQS is strong (Hermes-like learning nudge)."""
        if dqs is None or dqs < 75:
            return None
        name = (question.strip().split("\n")[0] or "Decision skill")[:80]
        body = (
            f"# Skill derived from Ask\n\n## Trigger\n{question[:500]}\n\n"
            f"## Procedure\n{answer[:2500]}\n"
        )
        return self.save(name=f"auto: {name}", body=body, tags=["auto", "ask"])

    def improve_from_outcome(
        self,
        *,
        skill_id: str | None = None,
        lesson: str,
        question: str = "",
    ) -> dict[str, Any] | None:
        """Append outcome lesson into a skill (self-improve v0)."""
        lesson = (lesson or "").strip()
        if not lesson:
            return None
        row = self.get(skill_id) if skill_id else None
        if row is None:
            # create lesson skill
            return self.save(
                name=f"lesson: {(question or lesson)[:60]}",
                body=f"# Lesson\n\n{lesson}\n\n## Context\n{question[:500]}\n",
                tags=["lesson", "outcome"],
                improve_note=lesson[:200],
            )
        body = str(row.get("body") or "") + f"\n\n## Outcome lesson\n{lesson}\n"
        return self.save(
            name=str(row.get("name") or "improved skill"),
            body=body[:12000],
            tags=list(row.get("tags") or []) + ["improved"],
            skill_id=str(row["skillId"]),
            improve_note=lesson[:200],
        )
