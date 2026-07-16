"""Framework integrations — grow the virus without forcing rewrites."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from uap.agent import Agent


def wrap(
    foreign: Any = None,
    *,
    name: str | None = None,
    workspace: str | Path | None = None,
) -> Agent:
    """Wrap any existing agent / graph with a NARNA Agent.

    Phase 1: creates an offline NARNA Agent (identity + event log).
    Deep LangGraph / CrewAI / OpenAI Agents / MCP adapters follow.

    Example::

        from narna import wrap
        agent = wrap(my_langgraph_app, name="Researcher")
        agent.enable_vap()
        agent.run("summarize docs")
    """
    if isinstance(foreign, Agent):
        return foreign

    label = name
    if label is None and foreign is not None:
        label = getattr(foreign, "name", None) or getattr(foreign, "__name__", None)
    agent = Agent(
        str(label) if label else "Wrapped Agent",
        workspace=workspace,
    )
    agent._wrapped = foreign
    return agent
