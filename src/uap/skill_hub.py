"""Skill Hub — OpenClaw/ClawHub-like shared skill index (v0)."""

from __future__ import annotations

import io
import json
import os
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id
from .skill_md import markdown_to_skill, skill_to_markdown


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

    def export_zip(self, dest: str | Path | None = None) -> dict[str, Any]:
        """Bundle hub skills as SKILL.md zip (Hermes / agentskills.io interop)."""
        skills = []
        for meta in self.list_public():
            row = self.get(str(meta.get("skillId") or ""))
            if row:
                skills.append(row)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "index.json",
                json.dumps(
                    {"skills": [{"skillId": s["skillId"], "name": s["name"]} for s in skills],
                     "standard": "NGS-0029-skill-hub-zip"},
                    indent=2,
                )
                + "\n",
            )
            for s in skills:
                slug = str(s.get("skillId") or "skill")
                zf.writestr(f"skills/{slug}/SKILL.md", skill_to_markdown(s))
        data = buf.getvalue()
        path = Path(dest) if dest else self.root / "skills-hub.zip"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {"ok": True, "path": str(path), "bytes": len(data), "n": len(skills)}

    def import_zip(self, src: str | Path | bytes) -> dict[str, Any]:
        if isinstance(src, (bytes, bytearray)):
            zf = zipfile.ZipFile(io.BytesIO(bytes(src)))
        else:
            zf = zipfile.ZipFile(Path(src))
        imported: list[str] = []
        with zf:
            for name in zf.namelist():
                if not name.lower().endswith("skill.md") and not name.lower().endswith(".md"):
                    continue
                if name.lower().endswith("readme.md"):
                    continue
                raw = zf.read(name).decode("utf-8", errors="replace")
                parsed = markdown_to_skill(raw)
                body = str(parsed.get("body") or "").strip()
                skill_name = str(parsed.get("name") or Path(name).stem)
                if not body:
                    continue
                tags = parsed.get("tags") if isinstance(parsed.get("tags"), list) else []
                row = self.publish(
                    name=skill_name,
                    body=body,
                    tags=[str(t) for t in tags] + ["imported"],
                    author="zip",
                )
                imported.append(str(row["skillId"]))
        return {"ok": True, "imported": imported, "n": len(imported)}

    def sync_from_url(self, url: str | None = None) -> dict[str, Any]:
        """Pull a public skill index JSON (not Nous). URL from arg or UAP_SKILL_HUB_INDEX_URL."""
        target = (url or os.environ.get("UAP_SKILL_HUB_INDEX_URL") or "").strip()
        if not target:
            return {"ok": False, "error": "UAP_SKILL_HUB_INDEX_URL not set"}
        if target.startswith("file:"):
            path = Path(target.replace("file://", "").replace("file:", ""))
            payload = json.loads(path.read_text(encoding="utf-8"))
        elif target.startswith("http://") or target.startswith("https://"):
            req = urllib.request.Request(
                target,
                headers={"User-Agent": "narna-agent/0.2 (+https://narna.org)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        else:
            path = Path(target)
            if not path.is_file():
                return {"ok": False, "error": f"index not found: {target}"}
            payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("skills") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            return {"ok": False, "error": "index must be {skills: [...]} or a list"}
        added = 0
        for item in rows[:200]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            body = str(item.get("body") or item.get("markdown") or "").strip()
            if body.startswith("---"):
                parsed = markdown_to_skill(body)
                name = name or str(parsed.get("name") or "")
                body = str(parsed.get("body") or "")
            if not name or not body:
                continue
            existing_id = str(item.get("skillId") or "")
            if existing_id and self.get(existing_id):
                continue
            self.publish(
                name=name,
                body=body[:12000],
                tags=list(item.get("tags") or []) + ["synced"],
                author=str(item.get("author") or "index"),
                skill_id=existing_id or None,
            )
            added += 1
        return {
            "ok": True,
            "url": target,
            "added": added,
            "indexSize": len(rows),
            "local": len(self.list_public()),
        }

    def maybe_autopublish(
        self,
        *,
        name: str,
        body: str,
        dqs: int | None,
        tags: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """When DQS≥80 and UAP_SKILL_HUB_AUTOPUBLISH=1, publish to local hub."""
        if dqs is None or int(dqs) < 80:
            return None
        flag = str(os.environ.get("UAP_SKILL_HUB_AUTOPUBLISH") or "").strip().lower()
        if flag not in {"1", "true", "yes", "on"}:
            return None
        return self.publish(
            name=name[:80],
            body=body[:12000],
            tags=list(tags or []) + ["auto"],
            author="narna-agent",
        )
