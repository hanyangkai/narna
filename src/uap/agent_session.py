"""Multi-turn agent sessions (chat continuity for Ask / mobile / Telegram)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AgentSessionStore:
    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "agent-sessions"
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.root / f"{session_id}.json"

    def get_or_create(
        self,
        session_id: str | None = None,
        *,
        channel: str = "web",
        external_id: str | None = None,
    ) -> dict[str, Any]:
        if session_id:
            existing = self.get(session_id)
            if existing:
                return existing
        # Find by external channel id (Telegram chat id)
        if external_id:
            for path in self.root.glob("*.json"):
                try:
                    row = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if row.get("externalId") == external_id and row.get("channel") == channel:
                    return row
        sid = session_id or new_id("sess")
        row = {
            "sessionId": sid,
            "channel": channel,
            "externalId": external_id,
            "messages": [],
            "createdAt": _now(),
            "updatedAt": _now(),
        }
        self._write(row)
        return row

    def get(self, session_id: str) -> dict[str, Any] | None:
        path = self._path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, row: dict[str, Any]) -> None:
        row["updatedAt"] = _now()
        self._path(str(row["sessionId"])).write_text(
            json.dumps(row, indent=2) + "\n", encoding="utf-8"
        )

    def append(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self.get(session_id) or self.get_or_create(session_id)
        messages = list(row.get("messages") or [])
        messages.append(
            {
                "role": role,
                "content": content[:20000],
                "meta": meta or {},
                "ts": _now(),
            }
        )
        row["messages"] = messages[-80:]
        self._write(row)
        return row

    def history_for_prompt(self, session_id: str, *, limit: int = 12) -> list[dict[str, str]]:
        row = self.get(session_id)
        if not row:
            return []
        out: list[dict[str, str]] = []
        for m in (row.get("messages") or [])[-limit:]:
            role = str(m.get("role") or "user")
            if role not in {"user", "assistant", "system"}:
                role = "user"
            out.append({"role": role, "content": str(m.get("content") or "")[:4000]})
        return out
