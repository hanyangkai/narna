from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .agent import Agent
from .governor import Governor
from .spec import load_agent_spec


@dataclass
class OrchestratorResult:
    coordinator_run_id: str
    session_id: str | None = None
    root_execution_unit_id: str | None = None
    total_gu: int = 0
    child_results: list[dict[str, Any]] = field(default_factory=list)


class MultiAgentOrchestrator:
    """Delegate runs across agents within a single Governance Session + Execution Graph."""

    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace or Path.cwd()
        self.governor = Governor(self.workspace)

    def run_pipeline(
        self,
        *,
        coordinator_spec: str | Path,
        child_specs: list[str | Path],
        input_text: str,
    ) -> OrchestratorResult:
        coordinator = Agent.from_spec(coordinator_spec, workspace=self.workspace)
        # Coordinator opens session but does not close — children share the graph
        coord_result = coordinator.run(
            input=input_text,
            close_session=False,
        )
        session_id = coord_result.session_id
        parent_unit = coord_result.root_execution_unit_id
        children: list[dict[str, Any]] = []

        for spec_path in child_specs:
            child = Agent.from_spec(spec_path, workspace=self.workspace)
            child_result = child.run(
                input=input_text,
                session_id=session_id,
                parent_unit_id=parent_unit,
                unit_kind="sub_agent",
                close_session=False,
            )
            children.append(
                {
                    "agentId": child.spec.agent_id,
                    "runId": child_result.run_id,
                    "state": child_result.state,
                    "sessionId": child_result.session_id,
                    "executionUnitId": child_result.root_execution_unit_id,
                }
            )

        total_gu = 0
        if session_id:
            session = self.governor.sessions.load(session_id)
            total_gu = session.total_gu
            self.governor.close_session(session_id)

        return OrchestratorResult(
            coordinator_run_id=coord_result.run_id,
            session_id=session_id,
            root_execution_unit_id=parent_unit,
            total_gu=total_gu,
            child_results=children,
        )
