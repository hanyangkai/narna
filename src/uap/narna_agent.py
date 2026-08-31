"""NARNA Agent Runtime — NGS-0029 Ask + tools + skills + multi-turn."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .adqa import ADQAEngine
from .agent_jobs import AgentJobStore
from .agent_memory_fts import AgentMemoryFTS
from .agent_memory_md import AgentMemoryMd
from .agent_session import AgentSessionStore
from .agent_skills import SkillStore
from .agent_tools import AgentToolbelt, openai_tools_schema
from .decision_memory import DecisionMemory
from .decision_trace import DecisionTraceStore
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


def _merge_tool_calls(
    native: list[dict[str, Any]] | None,
    parsed: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Prefer OpenAI-native tool_calls; fall back to JSON-fence parse (Hermes interop)."""
    if native:
        return native[:4]
    return parsed


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
        self.traces = DecisionTraceStore(self.workspace, tenant_id=tenant_id)
        self.skills = SkillStore(self.workspace)
        self.sessions = AgentSessionStore(self.workspace)
        self.jobs = AgentJobStore(self.workspace)
        self.hub = SkillHub(self.workspace)
        self.fts = AgentMemoryFTS(self.workspace)
        self.memory_md = AgentMemoryMd(self.workspace)
        self.tools = AgentToolbelt(
            memory=self.memory,
            skills=self.skills,
            workspace=self.workspace,
            sessions=self.sessions,
            delegate_fn=self._delegate_subask,
            skill_hub=self.hub,
            fts=self.fts,
            jobs=self.jobs,
            llm_api_key=getattr(self.router, "api_key", None),
            llm_provider=getattr(self.router, "provider", None),
            llm_base_url=getattr(self.router, "base_url", None),
        )
        self.adqa = ADQAEngine(self.workspace)
        self.max_tool_rounds = max(0, int(max_tool_rounds))
        self.max_delegate_depth = 3
        self._delegate_depth = 0

    def _delegate_subask(self, task: str) -> dict[str, Any]:
        """Hermes-like subagent: nested ask with isolated session + limited tool depth."""
        from .ids import new_id

        if self._delegate_depth >= self.max_delegate_depth:
            raise RuntimeError(f"nested delegate blocked (max {self.max_delegate_depth})")
        self._delegate_depth += 1
        try:
            parent = getattr(self, "_active_session_id", None)
            sub_id = new_id("sub")
            session = self.sessions.get_or_create(
                sub_id, channel="delegate", external_id=None
            )
            if parent:
                session["parentSessionId"] = parent
                self.sessions._write(session)
            return self.ask(
                task,
                session_id=str(session["sessionId"]),
                channel="delegate",
                use_tools=self._delegate_depth < self.max_delegate_depth,
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
        mode: str = "cheap",
    ) -> dict[str, Any]:
        msg = (message or "").strip()
        if not msg:
            raise ValueError("message is required")

        session = self.sessions.get_or_create(
            session_id, channel=channel, external_id=external_id
        )
        sid = str(session["sessionId"])
        self._active_session_id = sid
        self.sessions.append(sid, role="user", content=msg)
        self.fts.index_turn(session_id=sid, role="user", content=msg)
        self.fts.observe_user_message(msg)
        self.memory_md.observe_user_message(msg)
        try:
            from .knowledge import KnowledgeGraph

            KnowledgeGraph(self.workspace).observe_message(msg)
        except Exception:
            pass

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
        mem_md = self.memory_md.read_memory(max_chars=1800)
        user_md = self.memory_md.read_user(max_chars=1200)
        project_md = self.memory_md.read_project(max_chars=1200)
        kg_lines: list[str] = []
        try:
            from .knowledge import KnowledgeGraph

            ents = KnowledgeGraph(self.workspace).query(limit=8)
            kg_lines = [
                f"- {e.get('kind')}:{e.get('name')}" for e in ents if isinstance(e, dict)
            ]
        except Exception:
            pass
        tool_catalog = json.dumps(self.tools.specs(), ensure_ascii=False)
        history = self.sessions.history_for_prompt(sid, limit=10)
        ask_mode = (mode or "cheap").strip().lower()
        if ask_mode not in {"cheap", "quality", "critical"}:
            ask_mode = "cheap"

        system = (
            "You are NARNA, a decision-quality agent with tools. "
            "Use tools when you need facts, URLs, math, sandboxed code/shell, browser pages, "
            "workspace files, memory, skills, or hub skills. "
            "Prefer native function/tool calling when the API supports it. "
            "Otherwise output ONLY a JSON block like:\n"
            '```json\n{"tool":"web_search","args":{"query":"..."}}\n```\n'
            "You may use code_exec / execute_code / shell_exec / browser_navigate / browser_click / "
            "browser_type / browser_vision / parallel_delegate when useful. "
            "If shell_exec returns needsApproval, ask the user before re-calling with approved=true. "
            "After tools return, give a final recommendation with risks and missing evidence. "
            "Do not claim absolute certainty. Prefer Decision Memory lessons and user profile notes."
        )

        context_block = "\n".join(file_bits)
        user_blob = (
            f"Prior Decision Memory:\n"
            f"{chr(10).join(prior_lines) if prior_lines else '(none)'}\n\n"
            f"MEMORY.md:\n{mem_md or '(empty)'}\n\n"
            f"USER.md:\n{user_md or '(empty)'}\n\n"
            f"PROJECT.md:\n{project_md or '(empty)'}\n\n"
            f"Knowledge graph:\n{chr(10).join(kg_lines) if kg_lines else '(none)'}\n\n"
            f"User profile:\n{chr(10).join(profile_lines) if profile_lines else '(none)'}\n\n"
            f"FTS recall:\n{chr(10).join(fts_lines) if fts_lines else '(none)'}\n\n"
            f"Skills:\n{chr(10).join(skill_lines) if skill_lines else '(none)'}\n\n"
            f"Tools available:\n{tool_catalog}\n\n"
            f"Attachments:\n{context_block or '(none)'}\n\n"
            f"User question:\n{msg}"
        )

        messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
        messages.extend(history[:-1])  # history already includes latest user; avoid dup
        messages.append({"role": "user", "content": user_blob})

        models_used: list[str] = []
        tool_trace: list[dict[str, Any]] = []
        draft = ""
        openai_tools = openai_tools_schema(self.tools.specs()) if use_tools else None

        rounds = self.max_tool_rounds if use_tools else 0
        for _ in range(rounds + 1):
            # First round may use multi-model mode; tool follow-ups stay single-pass cheap
            if _ == 0 and ask_mode in {"quality", "critical"} and not tool_trace:
                result = self.router.complete_mode(
                    messages=messages,
                    mode=ask_mode,
                    tools=openai_tools,
                )
            else:
                result = self.router.complete(
                    messages=messages,
                    task="reason",
                    tools=openai_tools,
                )
            models_used.append(result.model)
            draft = result.content
            calls = (
                _merge_tool_calls(result.tool_calls, _parse_tool_calls(draft))
                if use_tools
                else []
            )
            if not calls:
                break
            tool_results = []
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": draft or None}
            if result.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": c.get("id") or f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": c.get("tool"),
                            "arguments": json.dumps(c.get("args") or {}),
                        },
                    }
                    for i, c in enumerate(result.tool_calls)
                ]
            messages.append(assistant_msg)
            for call in calls:
                name = str(call.get("tool") or "")
                args = call.get("args") if isinstance(call.get("args"), dict) else {}
                if not args:
                    args = {k: v for k, v in call.items() if k not in {"tool", "id"}}
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
                if call.get("id"):
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": json.dumps(out, ensure_ascii=False)[:8000],
                        }
                    )
            if not any(c.get("id") for c in calls):
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

        evidence_objs: list[dict[str, Any]] = []
        for s in sources:
            evidence_objs.append(
                {"type": str(s.get("type") or "source"), "ref": str(s.get("name") or "")}
            )
        for t in tool_trace[:15]:
            evidence_objs.append(
                {
                    "type": "tool",
                    "ref": str(t.get("tool") or ""),
                    "ok": (t.get("result") or {}).get("ok"),
                }
            )
        if file_bits:
            evidence_objs.append({"type": "file", "ref": "attachment.reviewed"})

        guardian = str(adqa.get("guardian") or "").lower()
        chosen = "recommend"
        if guardian in {"reject", "block", "deny"}:
            chosen = "reject"
        elif guardian in {"review", "ask", "escalate"}:
            chosen = "defer"

        trace = self.traces.create(
            goal=msg,
            context={
                "sessionId": sid,
                "channel": channel,
                "priors": len(priors),
                "challenge": bool(challenge),
                "mode": ask_mode,
            },
            evidence=evidence_objs,
            options=[
                {"id": "recommend", "label": "Proceed with recommendation"},
                {"id": "defer", "label": "Gather more evidence / review"},
                {"id": "reject", "label": "Do not act"},
            ],
            chosen=chosen,
            rationale=draft[:2000],
            adqa=adqa,
            tools_used=tool_trace,
            models_used=models_used,
            action=action,
            decision_id=str(record.get("decisionId") or ""),
            session_id=sid,
            channel=channel,
            answer=draft,
        )

        skill_saved = None
        hub_published = None
        if capture_skill:
            skill_saved = self.skills.maybe_capture_from_answer(
                question=msg, answer=draft, dqs=adqa.get("dqs")
            )
            try:
                hub_published = self.hub.maybe_autopublish(
                    name=f"auto: {(msg.strip().split(chr(10))[0] or 'skill')[:60]}",
                    body=(
                        f"# Skill from Ask\n\n## Trigger\n{msg[:500]}\n\n"
                        f"## Procedure\n{draft[:2500]}\n"
                    ),
                    dqs=adqa.get("dqs"),
                    tags=["auto", "ask"],
                )
            except Exception:
                hub_published = None
        # Persist high-quality lessons into MEMORY.md + FTS (Honcho-lite v2)
        try:
            dqs_val = int(adqa.get("dqs") or 0)
            if dqs_val >= 70:
                lesson_line = draft.strip().split("\n")[0][:300]
                lesson_text = lesson_line or msg[:200]
                self.memory_md.append_lesson(lesson_text, dqs=dqs_val)
                self.fts.index_lesson(lesson_text, dqs=dqs_val, meta={"action": action})
        except Exception:
            pass

        self.sessions.append(
            sid,
            role="assistant",
            content=draft,
            meta={
                "decisionId": record.get("decisionId"),
                "traceId": trace.get("traceId"),
                "dqs": adqa.get("dqs"),
                "guardian": adqa.get("guardian"),
            },
        )
        self.fts.index_turn(
            session_id=sid,
            role="assistant",
            content=draft,
            meta={
                "decisionId": record.get("decisionId"),
                "traceId": trace.get("traceId"),
                "dqs": adqa.get("dqs"),
            },
        )

        return {
            "answer": draft,
            "dqs": adqa.get("dqs"),
            "guardian": adqa.get("guardian"),
            "decisionId": record.get("decisionId"),
            "traceId": trace.get("traceId"),
            "modelsUsed": models_used,
            "sources": sources,
            "sessionId": sid,
            "adqa": adqa,
            "challenge": challenge_note or None,
            "toolsUsed": tool_trace,
            "skillSaved": skill_saved,
            "hubPublished": hub_published,
            "channel": channel,
            "mode": ask_mode,
            "verdict": {"recommend": "ACT", "defer": "REVIEW", "reject": "REJECT"}.get(
                chosen, "ACT"
            ),
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
        # Mirror outcome onto Decision Trace when present
        try:
            tr = self.traces.get_by_decision(decision_id)
            if tr:
                self.traces.attach_outcome(
                    str(tr["traceId"]),
                    status=status,
                    detail=detail,
                    lesson=lesson,
                    success_score=success_score,
                )
                row["traceId"] = tr.get("traceId")
        except Exception:
            pass
        if lesson:
            try:
                self.memory_md.append_lesson(lesson, dqs=None)
            except Exception:
                pass
        improved = None
        if lesson:
            improved = self.skills.improve_from_outcome(
                skill_id=skill_id,
                lesson=lesson,
                question=str((row.get("context") or {}).get("question") or ""),
            )
        return {**row, "skillImproved": improved}

    def run_due_jobs(self, *, limit: int = 10) -> list[dict[str, Any]]:
        """Execute due scheduled Ask jobs and fan-out results to channels (Hermes cron)."""
        from .job_delivery import deliver_job_result

        results: list[dict[str, Any]] = []
        for job in self.jobs.due_jobs()[:limit]:
            out = self.ask(
                str(job.get("prompt") or ""),
                channel=str(job.get("channel") or "job"),
                use_tools=True,
                capture_skill=True,
            )
            delivery = deliver_job_result(
                channel=str(job.get("channel") or "job"),
                deliver_to=str(job.get("deliverTo") or "") or None,
                out=out,
                job_id=str(job.get("jobId") or ""),
            )
            self.jobs.mark_ran(
                str(job["jobId"]),
                decision_id=out.get("decisionId"),
                delivery=delivery,
            )
            results.append({"jobId": job["jobId"], "ask": out, "delivery": delivery})
        return results

    def replay(self, trace_id: str, *, extra_context: str | None = None) -> dict[str, Any]:
        """Replay a Decision Trace with today's knowledge (NGS-0030)."""
        from .decision_replay import replay_trace

        tr = self.traces.get(trace_id)
        if not tr:
            raise KeyError(f"unknown traceId: {trace_id}")

        def ask_fn(message: str, **kwargs: Any) -> dict[str, Any]:
            return self.ask(message, **kwargs)

        result = replay_trace(tr, ask_fn=ask_fn, extra_context=extra_context)
        # Mark replay linkage on new trace if present
        new_tid = (result.get("replayed") or {}).get("traceId")
        if new_tid:
            new_tr = self.traces.get(str(new_tid))
            if new_tr:
                new_tr["replayOf"] = tr.get("traceId")
                self.traces.save(new_tr)
        return result
