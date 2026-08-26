"""NARNA Agent Runtime — NGS-0029 Ask + tools + skills + multi-turn."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .adqa import ADQAEngine
from .agent_jobs import AgentJobStore
from .agent_memory_fts import AgentMemoryFTS
from .agent_session import AgentSessionStore
from .agent_skills import SkillStore
from .agent_tools import AgentToolbelt
from .decision_memory import DecisionMemory
from .model_router import ModelRouter, default_router_from_env
from .skill_hub import SkillHub

_TOOL_RE = re.compile(
    r"```(?:json)?\s*(\{[\s\S]*?\"tool\"[\s\S]*?\})\s*```|"
    r"(\{\s*\"tool\"\s*:\s*\"[^\"]+\"[\s\S]*?\})",
    re.MULTILINE,
)


def _parse_tool_calls(text: str) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for m in _TOOL_RE.finditer(text or ""):
        raw = m.group(1) or m.group(2) or ""
        try:
            obj = json.loads(raw)
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("tool"):
            calls.append(obj)
    # Also support NARNA_TOOL: name {...}
    for line in (text or "").splitlines():
        if line.strip().startswith("NARNA_TOOL:"):
            rest = line.split(":", 1)[1].strip()
            parts = rest.split(None, 1)
            name = parts[0]
            args: dict[str, Any] = {}
            if len(parts) > 1:
                try:
                    args = json.loads(parts[1])
                except Exception:
                    args = {"query": parts[1]}
            calls.append({"tool": name, "args": args})
    return calls[:4]


class NarnaAgent:
    """Consumer Ask agent with Hermes-like tools/skills/sessions + ADQA."""

    def __init__(
        self,
        workspace: str | Path | None = None,
        *,
        tenant_id: str | None = None,
        router: ModelRouter | None = None,
        max_tool_rounds: int = 5,
    ) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.tenant_id = tenant_id
        self.router = router or default_router_from_env()
        self.memory = DecisionMemory(self.workspace, tenant_id=tenant_id)
        self.skills = SkillStore(self.workspace)
        self.sessions = AgentSessionStore(self.workspace)
        self.jobs = AgentJobStore(self.workspace)
        self.hub = SkillHub(self.workspace)
        self.fts = AgentMemoryFTS(self.workspace)
        self.tools = AgentToolbelt(
            memory=self.memory,
            skills=self.skills,
            workspace=self.workspace,
            sessions=self.sessions,
            delegate_fn=self._delegate_subask,
            skill_hub=self.hub,
            fts=self.fts,
        )
        self.adqa = ADQAEngine(self.workspace)
        self.max_tool_rounds = max(0, int(max_tool_rounds))
        self._delegate_depth = 0

    def _delegate_subask(self, task: str) -> dict[str, Any]:
        """Hermes-like subagent: one nested ask without further tools."""
        if self._delegate_depth >= 1:
            raise RuntimeError("nested delegate blocked")
        self._delegate_depth += 1
        try:
            return self.ask(
                task,
                channel="delegate",
                use_tools=False,
                capture_skill=False,
                challenge=False,
            )
        finally:
            self._delegate_depth -= 1

    def ask(
        self,
        message: str,
        *,
        session_id: str | None = None,
        files: list[dict[str, Any]] | None = None,
        challenge: bool = False,
        action: str = "agent.ask",
        channel: str = "web",
        external_id: str | None = None,
        use_tools: bool = True,
        capture_skill: bool = True,
    ) -> dict[str, Any]:
        msg = (message or "").strip()
        if not msg:
            raise ValueError("message is required")

        session = self.sessions.get_or_create(
            session_id, channel=channel, external_id=external_id
        )
        sid = str(session["sessionId"])
        self.sessions.append(sid, role="user", content=msg)
        self.fts.index_turn(session_id=sid, role="user", content=msg)
        self.fts.observe_user_message(msg)

        file_bits: list[str] = []
        sources: list[dict[str, str]] = []
        for f in files or []:
            name = str(f.get("name") or "file")
            text = str(f.get("text") or "")[:12000]
            if text:
                file_bits.append(f"--- file: {name} ---\n{text}")
                sources.append({"type": "file", "name": name})

        priors = self.memory.query(action=action, limit=5)
        prior_lines = [
            f"- prior dqs={p.get('dqs')} guardian={p.get('guardian')} lesson={p.get('lesson') or ''}"
            for p in priors
        ]
        skill_lines = [
            f"- {s.get('skillId')}: {s.get('name')}" for s in self.skills.list_skills()[:8]
        ]
        profile = self.fts.get_profile()
        profile_lines = [f"- {k}: {v}" for k, v in list(profile.items())[:8]]
        fts_hits = self.fts.search(msg, limit=4)
        fts_lines = [
            f"- [{h.get('role')}] {h.get('snippet')}" for h in fts_hits
        ]
        tool_catalog = json.dumps(self.tools.specs(), ensure_ascii=False)
        history = self.sessions.history_for_prompt(sid, limit=10)

        system = (
            "You are NARNA, a decision-quality agent with tools. "
            "Use tools when you need facts, URLs, math, sandboxed code/shell, browser pages, "
            "workspace files, memory, skills, or hub skills. "
            "To call a tool, output ONLY a JSON block like:\n"
            '```json\n{"tool":"web_search","args":{"query":"..."}}\n```\n'
            "You may use code_exec / shell_exec / browser_navigate / parallel_delegate when useful. "
            "After tools return, give a final recommendation with risks and missing evidence. "
            "Do not claim absolute certainty. Prefer Decision Memory lessons and user profile notes."
        )

        context_block = "\n".join(file_bits)
        user_blob = (
            f"Prior Decision Memory:\n"
            f"{chr(10).join(prior_lines) if prior_lines else '(none)'}\n\n"
            f"User profile:\n{chr(10).join(profile_lines) if profile_lines else '(none)'}\n\n"
            f"FTS recall:\n{chr(10).join(fts_lines) if fts_lines else '(none)'}\n\n"
            f"Skills:\n{chr(10).join(skill_lines) if skill_lines else '(none)'}\n\n"
            f"Tools available:\n{tool_catalog}\n\n"
            f"Attachments:\n{context_block or '(none)'}\n\n"
            f"User question:\n{msg}"
        )

        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        messages.extend(history[:-1])  # history already includes latest user; avoid dup
        messages.append({"role": "user", "content": user_blob})

        models_used: list[str] = []
        tool_trace: list[dict[str, Any]] = []
        draft = ""

        rounds = self.max_tool_rounds if use_tools else 0
        for _ in range(rounds + 1):
            result = self.router.complete(messages=messages, task="reason")
            models_used.append(result.model)
            draft = result.content
            calls = _parse_tool_calls(draft) if use_tools else []
            if not calls:
                break
            tool_results = []
            for call in calls:
                name = str(call.get("tool") or "")
                args = call.get("args") if isinstance(call.get("args"), dict) else {}
                # allow flat params
                if not args:
                    args = {k: v for k, v in call.items() if k != "tool"}
                out = self.tools.call(name, args)
                tool_trace.append({"tool": name, "args": args, "result": out})
                if name == "web_fetch" and out.get("ok"):
                    sources.append({"type": "url", "name": str(args.get("url") or "")})
                if name == "web_search" and out.get("ok"):
                    for h in (out.get("hits") or [])[:3]:
                        if h.get("url"):
                            sources.append({"type": "search", "name": str(h.get("url"))})
                if name == "skill_get" and out.get("ok"):
                    sid_skill = str((out.get("skill") or {}).get("skillId") or "")
                    if sid_skill:
                        self.skills.bump_use(sid_skill)
                tool_results.append({"tool": name, "result": out})
            messages.append({"role": "assistant", "content": draft})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Tool results (JSON). Now produce the final answer without more tools "
                        "unless critically needed:\n"
                        + json.dumps(tool_results, ensure_ascii=False)[:12000]
                    ),
                }
            )
        else:
            # exhausted rounds with trailing tool call — force final
            result = self.router.complete(
                messages=messages
                + [
                    {
                        "role": "user",
                        "content": "Stop calling tools. Give the final recommendation now.",
                    }
                ],
                task="decide",
            )
            models_used.append(result.model)
            draft = result.content

        challenge_note = ""
        if challenge:
            ch = self.router.challenge(draft=draft, question=msg)
            models_used.append(ch.model)
            challenge_note = ch.content
            draft = (
                f"{draft}\n\n--- Challenger review ---\n{challenge_note}\n\n"
                "Final recommendation incorporates the challenger notes above."
            )

        decision_result = {
            "decision": "ask",
            "recommendation": draft[:2000],
            "riskScore": 0.4 if tool_trace else 0.45,
            "riskBand": "medium",
            "reasons": ["agent.ask pipeline", f"tools={len(tool_trace)}"],
            "requiredApprovals": [],
            "evidence": (
                ["mustProve: attachment.reviewed"]
                if file_bits
                else (["mustProve: tool.evidence"] if tool_trace else ["mustProve: user.context"])
            ),
            "context": {
                "sessionId": sid,
                "memory": {"priors": len(priors)},
                "knowledge": {"entities": [{"id": "ask", "type": "query"}]},
                "toolsUsed": len(tool_trace),
            },
        }
        evidence_present = []
        if file_bits:
            evidence_present.append("attachment.reviewed")
        if tool_trace:
            evidence_present.append("tool.evidence")
        adqa = self.adqa.score(
            decision_result,
            evidence_present=evidence_present,
            agent_id="narna-agent",
            capability="content",
        )

        record = self.memory.record(
            action=action,
            context={"sessionId": sid, "question": msg[:500], "channel": channel},
            reasoning=[draft[:500]],
            guardian=adqa.get("guardian"),
            dqs=adqa.get("dqs"),
            confidence=float(adqa.get("confidence") or 0.5),
            provider=models_used[-1] if models_used else "router",
            decision="recommend",
            adqa=adqa,
            tenant_id=self.tenant_id,
        )

        skill_saved = None
        if capture_skill:
            skill_saved = self.skills.maybe_capture_from_answer(
                question=msg, answer=draft, dqs=adqa.get("dqs")
            )

        self.sessions.append(
            sid,
            role="assistant",
            content=draft,
            meta={
                "decisionId": record.get("decisionId"),
                "dqs": adqa.get("dqs"),
                "guardian": adqa.get("guardian"),
            },
        )
        self.fts.index_turn(
            session_id=sid,
            role="assistant",
            content=draft,
            meta={"decisionId": record.get("decisionId"), "dqs": adqa.get("dqs")},
        )

        return {
            "answer": draft,
            "dqs": adqa.get("dqs"),
            "guardian": adqa.get("guardian"),
            "decisionId": record.get("decisionId"),
            "modelsUsed": models_used,
            "sources": sources,
            "sessionId": sid,
            "adqa": adqa,
            "challenge": challenge_note or None,
            "toolsUsed": tool_trace,
            "skillSaved": skill_saved,
            "channel": channel,
            "standard": "NGS-0029",
        }

    def record_outcome(
        self,
        decision_id: str,
        *,
        status: str = "success",
        detail: str = "",
        success_score: float | None = None,
        lesson: str | None = None,
        skill_id: str | None = None,
    ) -> dict[str, Any]:
        row = self.memory.attach_outcome(
            decision_id,
            status=status,
            detail=detail,
            success_score=success_score,
            lesson=lesson,
        )
        improved = None
        if lesson:
            improved = self.skills.improve_from_outcome(
                skill_id=skill_id,
                lesson=lesson,
                question=str((row.get("context") or {}).get("question") or ""),
            )
        return {**row, "skillImproved": improved}

    def run_due_jobs(self, *, limit: int = 10) -> list[dict[str, Any]]:
        """Execute due scheduled Ask jobs (cron tick)."""
        results: list[dict[str, Any]] = []
        for job in self.jobs.due_jobs()[:limit]:
            out = self.ask(
                str(job.get("prompt") or ""),
                channel=str(job.get("channel") or "job"),
                use_tools=True,
                capture_skill=True,
            )
            self.jobs.mark_ran(str(job["jobId"]), decision_id=out.get("decisionId"))
            results.append({"jobId": job["jobId"], "ask": out})
        return results
