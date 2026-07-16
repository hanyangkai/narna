"""Framework adapters — Borrow the Wave (extend, never replace)."""

from __future__ import annotations

from typing import Any

from .base import AdapterResult, BaseAdapter
from .crewai import CrewAIAdapter
from .langgraph import LangGraphAdapter
from .mcp import McpAdapter
from .openai_agents import OpenAIAdapter
from .otel import OpenTelemetryAdapter, export_run_as_otel_attributes

_ADAPTERS: list[BaseAdapter] = [
    LangGraphAdapter(),
    CrewAIAdapter(),
    OpenAIAdapter(),
    McpAdapter(),
    OpenTelemetryAdapter(),
]

# Ordered heuristics for detect_framework (module markers)
_MARKERS: list[tuple[str, tuple[str, ...]]] = [
    ("langgraph", ("langgraph", "CompiledStateGraph", "StateGraph")),
    ("crewai", ("crewai",)),
    ("openai", ("openai", "agents.agent", "agents.run")),
    ("mcp", ("mcp", "ClientSession", "FastMCP")),
    ("opentelemetry", ("opentelemetry",)),
    ("autogen", ("autogen", "ConversableAgent")),
    ("llamaindex", ("llama_index",)),
    ("haystack", ("haystack",)),
    ("semantic_kernel", ("semantic_kernel",)),
]


def detect_framework(obj: Any) -> str | None:
    if obj is None:
        return None
    for adapter in _ADAPTERS:
        if adapter.matches(obj):
            return adapter.id
    mod = getattr(type(obj), "__module__", "") or ""
    qual = f"{mod}.{type(obj).__name__}".lower()
    for fid, markers in _MARKERS:
        for m in markers:
            if m.lower() in qual:
                return fid
    root = mod.split(".")[0].lower() if mod else ""
    aliases = {
        "langgraph": "langgraph",
        "crewai": "crewai",
        "openai": "openai",
        "agents": "openai",
        "mcp": "mcp",
        "opentelemetry": "opentelemetry",
        "autogen": "autogen",
        "llama_index": "llamaindex",
        "haystack": "haystack",
        "semantic_kernel": "semantic_kernel",
    }
    return aliases.get(root)


def resolve_adapter(framework: str | None, foreign: Any = None) -> BaseAdapter | None:
    if foreign is not None:
        for adapter in _ADAPTERS:
            if adapter.matches(foreign):
                return adapter
    if framework:
        for adapter in _ADAPTERS:
            if adapter.id == framework or adapter.id.replace("_", "-") == framework:
                return adapter
    return None


def attach_adapter(agent: Any, foreign: Any, framework: str | None) -> AdapterResult:
    adapter = resolve_adapter(framework, foreign)
    if adapter is None:
        result = AdapterResult(
            framework=framework or "generic",
            package=f"narna-{(framework or 'generic').replace('_', '-')}",
            status="generic",
            hooks=[],
            message="Generic wrap — business logic unchanged.",
        )
    else:
        result = adapter.attach(agent, foreign)
    agent._adapter = {
        "framework": result.framework,
        "package": result.package,
        "status": result.status,
        "hooks": result.hooks,
        "message": result.message,
    }
    if foreign is not None:
        try:
            setattr(foreign, "__narna_agent__", agent)
        except Exception:
            pass
    return result


def _pkg_slug(framework: str | None) -> str:
    if not framework:
        return "generic"
    return framework.replace("_", "-")


ADAPTER_CATALOG = [
    {"id": "openai", "package": "narna-openai", "status": "available", "works_with": "OpenAI Agents / client"},
    {"id": "langgraph", "package": "narna-langgraph", "status": "available", "works_with": "LangGraph"},
    {"id": "mcp", "package": "narna-mcp", "status": "available", "works_with": "MCP servers/clients"},
    {"id": "opentelemetry", "package": "narna-opentelemetry", "status": "available", "works_with": "OpenTelemetry"},
    {"id": "crewai", "package": "narna-crewai", "status": "available", "works_with": "CrewAI"},
    {"id": "anthropic", "package": "narna-anthropic", "status": "planned", "works_with": "Anthropic"},
    {"id": "google", "package": "narna-google", "status": "planned", "works_with": "Google ADK"},
    {"id": "openshell", "package": "narna-openshell", "status": "planned", "works_with": "OpenShell"},
]

__all__ = [
    "ADAPTER_CATALOG",
    "attach_adapter",
    "detect_framework",
    "resolve_adapter",
    "export_run_as_otel_attributes",
    "OpenAIAdapter",
    "LangGraphAdapter",
    "McpAdapter",
    "OpenTelemetryAdapter",
    "CrewAIAdapter",
]
