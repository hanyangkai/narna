"""Execution Unit — metered governance action."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id

GU_WEIGHTS: dict[str, int] = {
    "agent": 1,
    "sub_agent": 1,
    "tool": 1,
    "mcp": 1,
    "llm": 1,
    "workflow_step": 1,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class ExecutionUnit:
    unit_id: str
    session_id: str
    logical_agent_id: str
    unit_kind: str
    gu_cost: int
    parent_unit_id: str | None = None
    run_id: str | None = None
    tool_name: str | None = None
    label: str | None = None
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "unitId": self.unit_id,
            "sessionId": self.session_id,
            "logicalAgentId": self.logical_agent_id,
            "unitKind": self.unit_kind,
            "guCost": self.gu_cost,
        }
        if self.parent_unit_id:
            out["parentUnitId"] = self.parent_unit_id
        if self.run_id:
            out["runId"] = self.run_id
        if self.tool_name:
            out["toolName"] = self.tool_name
        if self.label:
            out["label"] = self.label
        if self.started_at:
            out["startedAt"] = self.started_at
        if self.completed_at:
            out["completedAt"] = self.completed_at
        return out


class ExecutionUnitLog:
    def __init__(self, session_dir: Path) -> None:
        self.path = session_dir / "units.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, unit: ExecutionUnit) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(unit.to_dict()) + "\n")

    def list_units(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows


def gu_cost_for(unit_kind: str) -> int:
    return GU_WEIGHTS.get(unit_kind, 1)


def mint_execution_unit(
    *,
    session_id: str,
    logical_agent_id: str,
    unit_kind: str,
    parent_unit_id: str | None = None,
    run_id: str | None = None,
    tool_name: str | None = None,
    label: str | None = None,
) -> ExecutionUnit:
    return ExecutionUnit(
        unit_id=new_id("eu"),
        session_id=session_id,
        logical_agent_id=logical_agent_id,
        unit_kind=unit_kind,
        gu_cost=gu_cost_for(unit_kind),
        parent_unit_id=parent_unit_id,
        run_id=run_id,
        tool_name=tool_name,
        label=label,
        started_at=_now(),
    )
