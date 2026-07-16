"""Framework adapters — Borrow the Wave (extend, never replace)."""

from __future__ import annotations

from typing import Any

from .anthropic import AnthropicAdapter
from .base import AdapterResult, BaseAdapter
from .crewai import CrewAIAdapter
from .google import GoogleAdapter
from .langgraph import LangGraphAdapter
from .mcp import McpAdapter
from .openai_agents import OpenAIAdapter
from .openshell import OpenShellAdapter
from .otel import OpenTelemetryAdapter, export_run_as_otel_attributes
from .otel_export import export_run_to_otlp

_ADAPTERS: list[BaseAdapter] = [
    LangGraphAdapter(),
    CrewAIAdapter(),
    OpenAIAdapter(),
    AnthropicAdapter(),
    GoogleAdapter(),
    McpAdapter(),
    OpenTelemetryAdapter(),
    OpenShellAdapter(),
]

_MARKERS: list[tuple[str, tuple[str, ...]]] = [
    ("langgraph", ("langgraph", "CompiledStateGraph", "StateGraph")),
    ("crewai", ("crewai",)),
    ("openai", ("openai", "agents.agent", "agents.run")),
    ("anthropic", ("anthropic", "claude")),
    ("google", ("google.genai", "generativeai", "vertexai", "gemini", "google.adk")),
    ("mcp", ("mcp", "ClientSession", "FastMCP")),
    ("opentelemetry", ("opentelemetry",)),
    ("openshell", ("openshell", "open_shell")),
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
        "anthropic": "anthropic",
        "google": "google",
        "vertexai": "google",
        "mcp": "mcp",
        "opentelemetry": "opentelemetry",
        "openshell": "openshell",
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


ADAPTER_CATALOG = [
    {"id": "openai", "package": "narna-openai", "status": "available", "works_with": "OpenAI Agents / client"},
    {"id": "anthropic", "package": "narna-anthropic", "status": "available", "works_with": "Anthropic / Claude"},
    {"id": "google", "package": "narna-google", "status": "available", "works_with": "Google ADK / Gemini"},
    {"id": "langgraph", "package": "narna-langgraph", "status": "available", "works_with": "LangGraph"},
    {"id": "mcp", "package": "narna-mcp", "status": "available", "works_with": "MCP servers/clients"},
    {"id": "opentelemetry", "package": "narna-opentelemetry", "status": "available", "works_with": "OpenTelemetry"},
    {"id": "crewai", "package": "narna-crewai", "status": "available", "works_with": "CrewAI"},
    {"id": "openshell", "package": "narna-openshell", "status": "available", "works_with": "OpenShell"},
]

__all__ = [
    "ADAPTER_CATALOG",
    "attach_adapter",
    "detect_framework",
    "resolve_adapter",
    "export_run_as_otel_attributes",
    "export_run_to_otlp",
    "OpenAIAdapter",
    "AnthropicAdapter",
    "GoogleAdapter",
    "LangGraphAdapter",
    "McpAdapter",
    "OpenTelemetryAdapter",
    "CrewAIAdapter",
    "OpenShellAdapter",
]
