"""Governance Session — container for execution graph and GU metering."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class GovernanceSession:
    session_id: str
    logical_agent_id: str
    root_run_id: str | None = None
    state: str = "open"
    created_at: str = field(default_factory=_now)
    closed_at: str | None = None
    total_gu: int = 0
    terminate_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sessionId": self.session_id,
            "logicalAgentId": self.logical_agent_id,
            "rootRunId": self.root_run_id,
            "state": self.state,
            "createdAt": self.created_at,
            "closedAt": self.closed_at,
            "totalGu": self.total_gu,
            "terminateReason": self.terminate_reason,
        }


class SessionStore:
    def __init__(self, workspace: Path) -> None:
        self.root = workspace / ".uap" / "sessions"
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, logical_agent_id: str, *, root_run_id: str | None = None) -> GovernanceSession:
        session = GovernanceSession(
            session_id=new_id("session"),
            logical_agent_id=logical_agent_id,
            root_run_id=root_run_id,
        )
        self.save(session)
        return session

    def path(self, session_id: str) -> Path:
        return self.root / session_id

    def save(self, session: GovernanceSession) -> None:
        d = self.path(session.session_id)
        d.mkdir(parents=True, exist_ok=True)
        (d / "session.json").write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")

    def load(self, session_id: str) -> GovernanceSession:
        data = json.loads((self.path(session_id) / "session.json").read_text(encoding="utf-8"))
        return GovernanceSession(
            session_id=data["sessionId"],
            logical_agent_id=data["logicalAgentId"],
            root_run_id=data.get("rootRunId"),
            state=data.get("state", "open"),
            created_at=data.get("createdAt", _now()),
            closed_at=data.get("closedAt"),
            total_gu=int(data.get("totalGu") or 0),
            terminate_reason=data.get("terminateReason"),
        )

    def close(self, session_id: str, *, terminated: bool = False, reason: str | None = None) -> GovernanceSession:
        session = self.load(session_id)
        session.state = "terminated" if terminated else "closed"
        session.closed_at = _now()
        session.terminate_reason = reason
        self.save(session)
        return session
