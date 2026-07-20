"""Metering — Governance Units (GU) counters and budgets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class BudgetConfig:
    monthly_limit_gu: int | None = None
    session_limit_gu: int | None = None
    logical_agent_budget_gu: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BudgetConfig:
        if not data:
            return cls()
        return cls(
            monthly_limit_gu=data.get("monthlyLimitGu"),
            session_limit_gu=data.get("sessionLimitGu"),
            logical_agent_budget_gu=data.get("logicalAgentBudgetGu"),
        )


class MeteringStore:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.path = workspace / ".uap" / "metering.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"periodStart": _now(), "usedGu": 0, "sessions": {}})

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def org_used_gu(self) -> int:
        return int(self._read().get("usedGu") or 0)

    def add_gu(self, amount: int, *, session_id: str) -> int:
        data = self._read()
        data["usedGu"] = int(data.get("usedGu") or 0) + amount
        sessions = data.setdefault("sessions", {})
        sessions[session_id] = int(sessions.get(session_id) or 0) + amount
        self._write(data)
        return int(data["usedGu"])

    def session_used_gu(self, session_id: str) -> int:
        return int(self._read().get("sessions", {}).get(session_id) or 0)

    def load_budget_config(self) -> BudgetConfig:
        budget_path = self.workspace / ".uap" / "budget.json"
        if not budget_path.exists():
            return BudgetConfig()
        return BudgetConfig.from_dict(json.loads(budget_path.read_text(encoding="utf-8")))
