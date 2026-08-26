"""SQLite FTS5 memory + lightweight user profile (Hermes/Honcho-lite v0)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AgentMemoryFTS:
    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        root = self.workspace / ".uap"
        root.mkdir(parents=True, exist_ok=True)
        self.db_path = root / "agent_memory.sqlite3"
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA busy_timeout=30000")
        except Exception:
            pass
        return conn

    def _init(self) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    meta_json TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts
                USING fts5(content, session_id UNINDEXED, role UNINDEXED, tokenize='porter')
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def index_turn(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> None:
        content = (content or "")[:20000]
        conn = self._conn()
        try:
            conn.execute(
                "INSERT INTO turns(session_id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
                (session_id, role, content, json.dumps(meta or {}), _now()),
            )
            conn.execute(
                "INSERT INTO turns_fts(content, session_id, role) VALUES (?,?,?)",
                (content, session_id, role),
            )
            conn.commit()
        finally:
            conn.close()

    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []
        safe = " ".join(tok for tok in q.replace('"', " ").split() if tok)[:200]
        if not safe:
            return []
        conn = self._conn()
        try:
            try:
                rows = conn.execute(
                    """
                    SELECT session_id, role, content
                    FROM turns_fts
                    WHERE turns_fts MATCH ?
                    LIMIT ?
                    """,
                    (safe, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                rows = conn.execute(
                    """
                    SELECT session_id, role, content FROM turns
                    WHERE lower(content) LIKE ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (f"%{safe.lower()}%", limit),
                ).fetchall()
            return [
                {
                    "source": "fts",
                    "sessionId": r["session_id"],
                    "role": r["role"],
                    "snippet": str(r["content"])[:240],
                }
                for r in rows
            ]
        finally:
            conn.close()

    def set_profile(self, key: str, value: str) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                INSERT INTO user_profile(key, value, updated_at) VALUES(?,?,?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value[:2000], _now()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_profile(self) -> dict[str, str]:
        conn = self._conn()
        try:
            rows = conn.execute("SELECT key, value FROM user_profile").fetchall()
            return {str(r["key"]): str(r["value"]) for r in rows}
        finally:
            conn.close()

    def observe_user_message(self, message: str) -> None:
        """Honcho-lite: extract crude preferences from user text."""
        msg = (message or "").lower()
        if "prefer" in msg or "i like" in msg or "tôi thích" in msg:
            self.set_profile("preference_note", message[:500])
        if "don't" in msg or "do not" in msg or "đừng" in msg or "không muốn" in msg:
            self.set_profile("avoid_note", message[:500])
        if "my name is" in msg or "tôi là" in msg or "i am " in msg:
            self.set_profile("identity_note", message[:300])
