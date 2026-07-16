from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .agent import Agent
from .spec import load_agent_spec


@dataclass
class OrchestratorResult:
    coordinator_run_id: str
    child_results: list[dict[str, Any]] = field(default_factory=list)


class MultiAgentOrchestrator:
    """V6 foundation — delegate runs across agents."""

    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace or Path.cwd()

    def run_pipeline(
        self,
        *,
        coordinator_spec: str | Path,
        child_specs: list[str | Path],
        input_text: str,
    ) -> OrchestratorResult:
        coordinator = Agent.from_spec(coordinator_spec, workspace=self.workspace)
        coord_result = coordinator.run(input=input_text)
        children: list[dict[str, Any]] = []

        for spec_path in child_specs:
            child = Agent.from_spec(spec_path, workspace=self.workspace)
            child_result = child.run(input=input_text)
            children.append(
                {
                    "agentId": child.spec.agent_id,
                    "runId": child_result.run_id,
                    "state": child_result.state,
                }
            )

        return OrchestratorResult(coordinator_run_id=coord_result.run_id, child_results=children)
