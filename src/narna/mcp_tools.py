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
    {
        "name": "narna_evaluate_action",
        "description": "Evaluate any proposed action with ADQA → ACT/REVIEW/REJECT + DQS (universal API).",
        "inputSchema": {
            "type": "object",
            "required": ["action"],
            "properties": {
                "action": {"type": "string"},
                "evidence": {"type": "array", "items": {"type": "string"}},
                "question": {"type": "string"},
                "context": {"type": "object"},
            },
        },
    },
    {
        "name": "narna_trace_get",
        "description": "Load a Decision Trace by traceId or decisionId.",
        "inputSchema": {
            "type": "object",
            "required": ["traceId"],
            "properties": {"traceId": {"type": "string"}},
        },
    },
    {
        "name": "narna_trace_list",
        "description": "List recent Decision Traces.",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}},
        },
    },
    {
        "name": "narna_replay",
        "description": "Replay a Decision Trace with today's knowledge.",
        "inputSchema": {
            "type": "object",
            "required": ["traceId"],
            "properties": {
                "traceId": {"type": "string"},
                "extraContext": {"type": "string"},
            },
        },
    },
    {
        "name": "narna_runtime_status",
        "description": (
            "Probe NARNA runtime readiness for OpenClaw/Cursor: version, toolCount, "
            "browser, shell backend. Does NOT expose the full 44-tool Ask loop over MCP — "
            "use narna_agent_ask / narna_adqa_check for decisions."
        ),
        "inputSchema": {"type": "object", "properties": {}},
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
            "narna_evaluate_action": self._evaluate_action,
            "narna_trace_get": self._trace_get,
            "narna_trace_list": self._trace_list,
            "narna_replay": self._replay,
            "narna_runtime_status": self._runtime_status,
        }
        fn = handlers.get(name)
        if not fn:
            return {"ok": False, "error": f"unknown tool: {name}"}
        return fn(args)

    def _runtime_status(self, args: dict[str, Any]) -> dict[str, Any]:
        import os

        from uap.agent_tools import TOOL_SPECS

        try:
            from narna import __version__ as ver
        except Exception:
            ver = "0.2.1"
        browser: dict[str, Any]
        try:
            from uap.browser_session import browser_ready

            browser = browser_ready()
        except Exception as e:
            browser = {"ready": False, "error": str(e)[:200]}
        return {
            "ok": True,
            "version": ver,
            "toolCount": len(TOOL_SPECS),
            "mcpSurface": "adqa+ask+status",
            "note": "MCP exposes decision tools, not the full 44-tool Hermes runtime",
            "shellBackend": (os.environ.get("UAP_SHELL_BACKEND") or "local").strip().lower(),
            "browser": browser,
            "workspace": str(self.workspace),
            "standard": "NGS-0029-mcp",
        }

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

        message = str(args.get("message") or "").strip()
        if not message:
            return {"ok": False, "error": "message required"}
        try:
            out = NarnaAgent(self.workspace, router=ModelRouter()).ask(
                message,
                session_id=args.get("sessionId") or args.get("session_id"),
                challenge=bool(args.get("challenge")),
            )
        except Exception as e:
            return {
                "ok": False,
                "error": str(e)[:500],
                "hint": "BYOK: set UAP_OPENROUTER_API_KEY / UAP_OPENAI_API_KEY or pass org API key",
            }
        if not isinstance(out, dict):
            return {"ok": True, "answer": str(out)}
        # Mock path still returns ADQA — surface clearly when no live model
        mockish = str(out.get("provider") or out.get("model") or "").lower() in {
            "mock",
            "",
        } and not out.get("answer")
        if out.get("error"):
            return {"ok": False, **out}
        result = {"ok": True, **out}
        if mockish or out.get("mock"):
            result["hint"] = "Running mock/BYOK-missing path — paste an LLM key for live answers"
        return result

    def _evaluate_action(self, args: dict[str, Any]) -> dict[str, Any]:
        from narna.evaluate import evaluate

        return evaluate(
            action=str(args.get("action") or ""),
            evidence=list(args.get("evidence") or []) if isinstance(args.get("evidence"), list) else None,
            context=args.get("context") if isinstance(args.get("context"), dict) else None,
            question=args.get("question"),
            workspace=self.workspace,
        )

    def _trace_get(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.decision_trace import DecisionTraceStore

        tid = str(args.get("traceId") or args.get("trace_id") or "")
        row = DecisionTraceStore(self.workspace).get(tid)
        if not row:
            return {"ok": False, "error": "trace not found"}
        return {"ok": True, "trace": row}

    def _trace_list(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.decision_trace import DecisionTraceStore

        rows = DecisionTraceStore(self.workspace).list_traces(limit=int(args.get("limit") or 10))
        return {"ok": True, "traces": rows, "count": len(rows)}

    def _replay(self, args: dict[str, Any]) -> dict[str, Any]:
        from uap.model_router import ModelRouter
        from uap.narna_agent import NarnaAgent

        agent = NarnaAgent(self.workspace, router=ModelRouter())
        try:
            out = agent.replay(
                str(args.get("traceId") or ""),
                extra_context=str(args.get("extraContext") or args.get("extra_context") or "")
                or None,
            )
        except KeyError as e:
            return {"ok": False, "error": str(e)}
        return out
