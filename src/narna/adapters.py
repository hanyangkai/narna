"""Adapter detection — Borrow the Wave: extend frameworks, never replace."""

from __future__ import annotations

from typing import Any

# Ordered heuristics: (framework_id, predicate markers)
_MARKERS: list[tuple[str, tuple[str, ...]]] = [
    ("langgraph", ("langgraph", "CompiledStateGraph", "StateGraph")),
    ("crewai", ("crewai", "Crew", "Agent")),
    ("openai_agents", ("agents", "Agent", "Runner")),
    ("autogen", ("autogen", "ConversableAgent")),
    ("mcp", ("mcp", "Server", "ClientSession")),
    ("llamaindex", ("llama_index", "Workflow")),
    ("haystack", ("haystack", "Pipeline")),
    ("semantic_kernel", ("semantic_kernel", "Kernel")),
]


def detect_framework(obj: Any) -> str | None:
    if obj is None:
        return None
    mod = getattr(type(obj), "__module__", "") or ""
    qual = f"{mod}.{type(obj).__name__}"
    blob = qual.lower()
    for fid, markers in _MARKERS:
        for m in markers:
            if m.lower() in blob:
                return fid
    # module roots
    root = mod.split(".")[0].lower() if mod else ""
    aliases = {
        "langgraph": "langgraph",
        "crewai": "crewai",
        "agents": "openai_agents",
        "autogen": "autogen",
        "mcp": "mcp",
        "llama_index": "llamaindex",
        "haystack": "haystack",
        "semantic_kernel": "semantic_kernel",
    }
    return aliases.get(root)


def attach_adapter(agent: Any, foreign: Any, framework: str | None) -> None:
    """Attach lightweight adapter metadata (deep hooks land in dedicated packages)."""
    agent._adapter = {
        "framework": framework or "generic",
        "package": f"narna-{_pkg_slug(framework)}" if framework else "narna-generic",
        "status": "scaffold",
        "message": (
            f"Works with {framework}." if framework else "Generic wrap — business logic unchanged."
        ),
    }
    if foreign is not None and hasattr(foreign, "__dict__"):
        # Non-invasive: stash reverse pointer if possible without breaking foreign
        try:
            setattr(foreign, "__narna_agent__", agent)
        except Exception:
            pass


def _pkg_slug(framework: str | None) -> str:
    if not framework:
        return "generic"
    return framework.replace("_", "-")


ADAPTER_CATALOG = [
    {"id": "openai", "package": "narna-openai", "status": "scaffold"},
    {"id": "anthropic", "package": "narna-anthropic", "status": "planned"},
    {"id": "google", "package": "narna-google", "status": "planned"},
    {"id": "mcp", "package": "narna-mcp", "status": "scaffold"},
    {"id": "opentelemetry", "package": "narna-opentelemetry", "status": "planned"},
    {"id": "langgraph", "package": "narna-langgraph", "status": "scaffold"},
    {"id": "crewai", "package": "narna-crewai", "status": "scaffold"},
    {"id": "openshell", "package": "narna-openshell", "status": "planned"},
]
