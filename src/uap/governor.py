"""Governor — session supervisor: budgets, loops, recursion."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .errors import UapRuntimeError
from .execution_graph import ExecutionGraph, GraphNode
from .execution_unit import ExecutionUnit, ExecutionUnitLog, mint_execution_unit
from .metering import MeteringStore
from .session import GovernanceSession, SessionStore


class GovernorError(UapRuntimeError):
    """Governor blocked or terminated execution."""


@dataclass
class GovernorConfig:
    recursion_depth_limit: int = 4
    recursion_risk_threshold: float = 0.85
    default_agent_budget_gu: int = 100


@dataclass
class GovernorResult:
    unit: ExecutionUnit
    session: GovernanceSession
    events: list[dict[str, Any]] = field(default_factory=list)
    recursive_risk: float = 0.0


class Governor:
    def __init__(self, workspace: Path, *, config: GovernorConfig | None = None) -> None:
        self.workspace = workspace
        self.config = config or GovernorConfig()
        self.sessions = SessionStore(workspace)
        self.metering = MeteringStore(workspace)
        self._current_unit: dict[str, str] = {}  # session_id -> last unit_id

    def open_session(self, logical_agent_id: str, *, root_run_id: str | None = None) -> GovernanceSession:
        budget = self.metering.load_budget_config()
        if budget.monthly_limit_gu is not None:
            if self.metering.org_used_gu() >= budget.monthly_limit_gu:
                raise GovernorError("monthly GU budget exceeded (Cost Guard)")
        return self.sessions.create(logical_agent_id, root_run_id=root_run_id)

    def begin_unit(
        self,
        session: GovernanceSession,
        *,
        logical_agent_id: str,
        unit_kind: str,
        run_id: str | None = None,
        tool_name: str | None = None,
        label: str | None = None,
        parent_unit_id: str | None = None,
    ) -> GovernorResult:
        if session.state != "open":
            raise GovernorError(f"session {session.session_id} is {session.state}")

        session_dir = self.sessions.path(session.session_id)
        graph = ExecutionGraph(session_dir)
        parent = parent_unit_id or self._current_unit.get(session.session_id)

        if graph.would_create_cycle(parent, logical_agent_id):
            self._terminate(session, reason="loop_detected")
            raise GovernorError("loop detected in execution graph")

        unit = mint_execution_unit(
            session_id=session.session_id,
            logical_agent_id=logical_agent_id,
            unit_kind=unit_kind,
            parent_unit_id=parent,
            run_id=run_id,
            tool_name=tool_name,
            label=label,
        )

        graph.add_node(
            GraphNode(
                unit_id=unit.unit_id,
                unit_kind=unit_kind,
                logical_agent_id=logical_agent_id,
                parent_unit_id=parent,
            )
        )

        ancestry = graph.ancestry_kinds(unit.unit_id)
        same_kind_streak = 0
        for k in ancestry:
            if k == unit_kind:
                same_kind_streak += 1
            else:
                break
        recursive_risk = min(1.0, same_kind_streak / max(1, self.config.recursion_depth_limit))

        if same_kind_streak >= self.config.recursion_depth_limit:
            self._terminate(session, reason="recursive_risk")
            raise GovernorError(
                f"recursive risk {recursive_risk:.0%}: {unit_kind} depth {same_kind_streak}"
            )

        budget = self.metering.load_budget_config()
        projected_session = self.metering.session_used_gu(session.session_id) + unit.gu_cost
        if budget.session_limit_gu is not None and projected_session > budget.session_limit_gu:
            self._terminate(session, reason="session_budget_exceeded")
            raise GovernorError("session GU budget exceeded")

        agent_budget = budget.logical_agent_budget_gu or self.config.default_agent_budget_gu
        if projected_session > agent_budget:
            self._terminate(session, reason="agent_budget_exceeded")
            raise GovernorError("logical agent GU budget exceeded")

        if budget.monthly_limit_gu is not None:
            if self.metering.org_used_gu() + unit.gu_cost > budget.monthly_limit_gu:
                self._terminate(session, reason="monthly_budget_exceeded")
                raise GovernorError("monthly GU budget exceeded (Cost Guard)")

        ExecutionUnitLog(session_dir).append(unit)
        self.metering.add_gu(unit.gu_cost, session_id=session.session_id)
        session.total_gu += unit.gu_cost
        self.sessions.save(session)
        self._current_unit[session.session_id] = unit.unit_id

        return GovernorResult(unit=unit, session=session, recursive_risk=recursive_risk)

    def close_session(self, session_id: str) -> GovernanceSession:
        self._current_unit.pop(session_id, None)
        return self.sessions.close(session_id, terminated=False)

    def _terminate(self, session: GovernanceSession, *, reason: str) -> None:
        self._current_unit.pop(session.session_id, None)
        self.sessions.close(session.session_id, terminated=True, reason=reason)

    def emit_session_events(
        self,
        log_append: Callable[..., dict[str, Any]],
        *,
        agent_id: str,
        run_id: str,
        session: GovernanceSession,
        result: GovernorResult,
        event_id_fn: Callable[[], str],
        ts_fn: Callable[[], str],
    ) -> None:
        log_append(
            event_id=event_id_fn(),
            event_type="ExecutionUnitStarted",
            agent_id=agent_id,
            run_id=run_id,
            ts=ts_fn(),
            payload={
                "executionUnit": result.unit.to_dict(),
                "recursiveRisk": result.recursive_risk,
            },
            session_id=session.session_id,
            execution_unit_id=result.unit.unit_id,
            parent_execution_unit_id=result.unit.parent_unit_id,
        )
