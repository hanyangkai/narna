"""Integration catalog — hot AI stacks NARNA extends (Borrow the Wave)."""

from __future__ import annotations

from typing import Any

from narna.adapters import ADAPTER_CATALOG

# Continuity memory (external) — NARNA consumes as feedstock
MEMORY_PARTNERS = [
    {
        "id": "cmem",
        "name": "CMEM / claude-mem",
        "role": "Memory continuity",
        "narna": "Decision quality (ADQA)",
        "package": "narna-cmem",
        "bridge": "CmemBridge + MCP tools",
        "url": "https://cmem.ai/",
    },
]

HOT_STACKS = [
    {"id": "openai", "name": "OpenAI / Agents SDK", "layer": "LLM / agents"},
    {"id": "anthropic", "name": "Anthropic / Claude", "layer": "LLM / agents"},
    {"id": "google", "name": "Google Gemini / ADK", "layer": "LLM / agents"},
    {"id": "langgraph", "name": "LangGraph", "layer": "orchestration"},
    {"id": "crewai", "name": "CrewAI", "layer": "multi-agent"},
    {"id": "autogen", "name": "AutoGen / AG2", "layer": "multi-agent"},
    {"id": "semantic_kernel", "name": "Semantic Kernel", "layer": "orchestration"},
    {"id": "llamaindex", "name": "LlamaIndex", "layer": "RAG / workflows"},
    {"id": "mcp", "name": "MCP clients", "layer": "tools"},
    {"id": "cmem", "name": "CMEM Cloud MCP", "layer": "memory"},
    {"id": "opentelemetry", "name": "OpenTelemetry", "layer": "observability"},
    {"id": "moltbook", "name": "Moltbook / OpenClaw", "layer": "social agents"},
]


def integration_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "philosophy": "Never Replace. Always Extend.",
        "split": {
            "cmem": "What does the agent remember?",
            "narna": "Was this decision good enough to act?",
        },
        "adapters": ADAPTER_CATALOG,
        "memoryPartners": MEMORY_PARTNERS,
        "hotStacks": HOT_STACKS,
        "mcpTools": [
            "narna_adqa_check",
            "narna_dmemory_query",
            "narna_learning_prior",
            "narna_cmem_enrich",
        ],
        "env": {
            "NARNA_CMEM_URL": "Private CMEM MCP/HTTP link",
            "NARNA_ADQA": "1 = ADQA gate on adapter calls",
            "NARNA_ADQA_STRICT": "1 = reject blocks host call",
            "NARNA_ADAPTER_MODE": "enforce | observe",
        },
    }
