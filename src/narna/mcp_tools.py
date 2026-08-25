"""NARNA MCP tool surface — expose ADQA + Decision Memory to any MCP client.

Hot stacks (Cursor, Claude Code, Codex, OpenClaw, Gemini CLI) speak MCP.
They already use CMEM for continuity; call these tools for decision quality.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


TOOL_DEFS: list[dict[str, Any]] = [
    {
        "name": "narna_adqa_check",
        "description": "Score a proposed action with ADQA (DQS + Decision Guardian). Complements CMEM memory recall.",
        "inputSchema": {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {"type": "string"},
                "provider": {"type": "string"},
                "evidencePresent": {"type": "array", "items": {"type": "string"}},
                "agentId": {"type": "string"},
                "question": {"type": "string"},
            },
        },
    },
    {
        "name": "narna_dmemory_query",
        "description": "Query NARNA Decision Memory (quality records / lessons), not CMEM observations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    {
        "name": "narna_learning_prior",
        "description": "Get Outcome Learning prior for an action (NGS-0026).",
        "inputSchema": {
            "type": "object",
            "required": ["action"],
            "properties": {"action": {"type": "string"}},
        },
    },
    {
        "name": "narna_cmem_enrich",
        "description": "Pull CMEM feedstock into ADQA context (bridge; does not replace CMEM).",
        "inputSchema": {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {"type": "string"},
                "limit": {"type": "integer", "default": 8},
            },
        },
    },
    {
        "name": "narna_agent_ask",
        "description": "Ask NARNA Agent (NGS-0029): reason + ADQA + Decision Memory. Model-agnostic.",
        "inputSchema": {
            "type": "object",
            "required": ["message"],
            "properties": {
                "message": {"type": "string"},
                "challenge": {"type": "boolean", "default": False},
                "sessionId": {"type": "string"},
            },
        },
    },
]


class NarnaMcpTools:
    """Dispatch NARNA tools for MCP hosts without requiring the `mcp` package."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def list_tools(self) -> list[dict[str, Any]]:
        return list(TOOL_DEFS)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        args = dict(arguments or {})
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "narna_adqa_check": self._adqa_check,
            "narna_dmemory_query": self._dmemory_query,
            "narna_learning_prior": self._learning_prior,
            "narna_cmem_enrich": self._cmem_enrich,
            "narna_agent_ask": self._agent_ask,
        }
        fn = handlers.get(name)
        if not fn:
            return {"ok": False, "error": f"unknown tool: {name}"}
        return fn(args)

    def _adqa_check(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.adqa import ADQAEngine

        evidence = args.get("evidencePresent") or args.get("evidence_present") or []
        out = ADQAEngine(self.workspace).check_proposed(
            action=str(args.get("action") or ""),
            provider=args.get("provider"),
            evidence_present=list(evidence) if isinstance(evidence, list) else [],
            agent_id=args.get("agentId") or args.get("agent_id"),
            question=args.get("question"),
        )
        return {"ok": True, **out}

    def _dmemory_query(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.decision_memory import DecisionMemory

        limit = int(args.get("limit") or 10)
        rows = DecisionMemory(self.workspace).query(action=args.get("action"), limit=limit)
        return {"ok": True, "records": rows, "count": len(rows)}

    def _learning_prior(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.outcome_learning import OutcomeLearningEngine

        prior = OutcomeLearningEngine(self.workspace).prior_for(str(args.get("action") or ""))
        return {"ok": True, "prior": prior}

    def _cmem_enrich(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.cmem_bridge import CmemBridge

        ctx = CmemBridge(self.workspace).enrich_context(
            str(args.get("action") or ""),
            limit=int(args.get("limit") or 8),
        )
        return {
            "ok": True,
            "cmem": ctx.get("_cmem"),
            "decisionMemory": ctx.get("decisionMemory"),
            "memory": ctx.get("_memory"),
        }

    def _agent_ask(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.model_router import ModelRouter
        from uap.narna_agent import NarnaAgent

        out = NarnaAgent(self.workspace, router=ModelRouter()).ask(
            str(args.get("message") or ""),
            session_id=args.get("sessionId") or args.get("session_id"),
            challenge=bool(args.get("challenge")),
        )
        return {"ok": True, **out}
