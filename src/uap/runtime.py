from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .benchmark import BenchmarkStore
from .errors import AuthorizationError, EvidenceError, UapRuntimeError
from .event_log import EventLog
from .evidence import EvidenceStore
from .hashing import sha256_obj
from .ids import new_id
from .memory import LocalMemoryAdapter
from .model import create_model_adapter
from .policy import PolicyEngine
from .governance_runtime import ConstitutionRuntime
from .spec import AgentSpec, load_agent_spec
from .state import RunState, transition
from .tools import execute_tool, load_tool_definition
from .vap.pipeline import run_vap_pipeline
from .vap.verify_evidence import verify_freshness, verify_hash_match, verify_receipt_presence


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class RunResult:
    run_id: str
    tip_hash: str
    events_path: Path
    state: str
    pending_ask: dict[str, Any] | None = None
    # Phase 2 — populated when VAP is enabled
    vap_enabled: bool = False
    trust_score: float | None = None
    audit_id: str | None = None
    proof_path: Path | None = None
    verifications: list[dict[str, Any]] = field(default_factory=list)
    vap: dict[str, Any] | None = None


@dataclass
class RunContext:
    run_id: str
    run_dir: Path
    state: RunState = RunState.CREATED
    pending_ask: dict[str, Any] | None = None
    policy_decisions: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    evidence_blobs: dict[str, bytes] = field(default_factory=dict)
    action_verifications: list[dict[str, Any]] = field(default_factory=list)


class LocalRuntime:
    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace or Path.cwd()
        self.root = self.workspace / ".uap"
        self.runs_dir = self.root / "runs"
        self.policy = PolicyEngine(self.workspace)
        self.governance = ConstitutionRuntime(self.workspace)
        self.evidence_store = EvidenceStore(self.workspace)
        # Phase 2: Verify → Audit → Prove (off by default for Phase 1 lightness)
        self.vap_enabled = False

    def enable_vap(self, enabled: bool = True) -> None:
        self.vap_enabled = enabled

    def init(self) -> None:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        (self.root / "registry").mkdir(parents=True, exist_ok=True)
        (self.root / "marketplace").mkdir(parents=True, exist_ok=True)

    def run(
        self,
        spec: AgentSpec,
        *,
        user_input: str | None = None,
        auto_approve_ask: bool = False,
        spec_path: str | Path | None = None,
    ) -> RunResult:
        self.init()
        run_id = new_id("run")
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=False)
        ctx = RunContext(run_id=run_id, run_dir=run_dir)
        log = EventLog(run_dir / "events.jsonl")
        return self._execute_run(
            spec=spec,
            ctx=ctx,
            log=log,
            user_input=user_input,
            auto_approve_ask=auto_approve_ask,
            spec_path=spec_path,
        )

    def resolve_ask(self, run_id: str, *, approved: bool, spec_path: str | Path) -> RunResult:
        pending_path = self.runs_dir / run_id / "pending-ask.json"
        if not pending_path.exists():
            raise UapRuntimeError(f"no pending ask for run {run_id}")
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        spec = load_agent_spec(spec_path)
        run_dir = self.runs_dir / run_id
        log = EventLog(run_dir / "events.jsonl")
        ctx = RunContext(run_id=run_id, run_dir=run_dir, state=RunState.RUNNING)

        if not approved:
            ctx.state = RunState.FAILING
            log.append(
                event_id=new_id("evt"),
                event_type="Failed",
                agent_id=spec.agent_id,
                run_id=run_id,
                ts=_now_rfc3339(),
                payload={"reason": "ask denied", "state": RunState.FAILED.value},
            )
            ctx.state = RunState.FAILED
            pending_path.unlink(missing_ok=True)
            log.flush()
            return RunResult(
                run_id=run_id,
                tip_hash=log.tip_hash,
                events_path=log.path,
                state=ctx.state.value,
            )

        self._execute_tool_flow(
            spec=spec,
            ctx=ctx,
            log=log,
            tool_name=pending["tool"],
            tool_input=pending["input"],
            auto_approve_ask=True,
        )
        pending_path.unlink(missing_ok=True)
        return self._complete_run(spec=spec, ctx=ctx, log=log)

    def _execute_run(
        self,
        *,
        spec: AgentSpec,
        ctx: RunContext,
        log: EventLog,
        user_input: str | None,
        auto_approve_ask: bool,
        spec_path: str | Path | None,
    ) -> RunResult:
        try:
            ctx.state = transition(ctx.state, RunState.STARTING)
            log.append(
                event_id=new_id("evt"),
                event_type="AgentStarted",
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
                ts=_now_rfc3339(),
                payload={"agentName": spec.name, "agentVersion": spec.version},
            )
            ctx.state = transition(ctx.state, RunState.RUNNING)
            memory = LocalMemoryAdapter(self.workspace, spec.agent_id)
            model = create_model_adapter(spec.raw.get("spec", {}).get("model"))

            if user_input:
                intent = model.understand(user_input)
                log.append(
                    event_id=new_id("evt"),
                    event_type="ModelGenerated",
                    agent_id=spec.agent_id,
                    run_id=ctx.run_id,
                    ts=_now_rfc3339(),
                    payload={"artifactHash": intent.artifact_hash, "proposedTool": intent.tool_name},
                )
                log.append(
                    event_id=new_id("evt"),
                    event_type="MemoryRead",
                    agent_id=spec.agent_id,
                    run_id=ctx.run_id,
                    ts=_now_rfc3339(),
                    payload={"keys": ["lastQuery"]},
                )
                if intent.tool_name and intent.tool_input:
                    try:
                        self._execute_tool_flow(
                            spec=spec,
                            ctx=ctx,
                            log=log,
                            tool_name=intent.tool_name,
                            tool_input=intent.tool_input,
                            auto_approve_ask=auto_approve_ask,
                        )
                    except UapRuntimeError as e:
                        if str(e) == "awaiting_input":
                            pending_path = ctx.run_dir / "pending-ask.json"
                            pending_path.write_text(
                                json.dumps(
                                    {
                                        "tool": ctx.pending_ask["tool"],
                                        "input": ctx.pending_ask["input"],
                                        "permission": ctx.pending_ask["permission"],
                                        "userInput": user_input,
                                    },
                                    indent=2,
                                ),
                                encoding="utf-8",
                            )
                            log.flush()
                            return RunResult(
                                run_id=ctx.run_id,
                                tip_hash=log.tip_hash,
                                events_path=log.path,
                                state=RunState.AWAITING_INPUT.value,
                                pending_ask=ctx.pending_ask,
                            )
                        raise
                memory.write({"lastQuery": user_input})
                log.append(
                    event_id=new_id("evt"),
                    event_type="MemoryWrite",
                    agent_id=spec.agent_id,
                    run_id=ctx.run_id,
                    ts=_now_rfc3339(),
                    payload={"keys": ["lastQuery"]},
                )

            return self._complete_run(spec=spec, ctx=ctx, log=log)
        except AuthorizationError as e:
            return self._fail(spec, ctx, log, str(e))
        except EvidenceError as e:
            return self._fail(spec, ctx, log, str(e))
        except Exception as e:
            return self._fail(spec, ctx, log, f"runtime error: {e}")

    def _complete_run(self, *, spec: AgentSpec, ctx: RunContext, log: EventLog) -> RunResult:
        ctx.state = transition(RunState.RUNNING, RunState.COMPLETING)

        vap: dict[str, Any] | None = None
        proof_path: Path | None = None
        trust_score: float | None = None
        audit_id: str | None = None
        verifications: list[dict[str, Any]] = list(ctx.action_verifications)

        if self.vap_enabled:
            events = log.export()
            vap = run_vap_pipeline(
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
                events=events,
                evidence=ctx.evidence,
                evidence_blobs=ctx.evidence_blobs,
                policy_decisions=ctx.policy_decisions,
            )
            for v in vap["verifications"]:
                log.append(
                    event_id=new_id("evt"),
                    event_type="Verified",
                    agent_id=spec.agent_id,
                    run_id=ctx.run_id,
                    ts=_now_rfc3339(),
                    payload={"verification": v},
                )
            log.append(
                event_id=new_id("evt"),
                event_type="AuditRecorded",
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
                ts=_now_rfc3339(),
                payload={"auditId": vap["audit"]["auditId"]},
            )
            log.append(
                event_id=new_id("evt"),
                event_type="TrustScored",
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
                ts=_now_rfc3339(),
                payload={"score": vap["trustScore"]["score"]},
            )
            proof_path = ctx.run_dir / "proof-bundle.json"
            proof_path.write_text(
                json.dumps(vap["proofBundle"], indent=2), encoding="utf-8"
            )
            BenchmarkStore(self.workspace).record(
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
                trust_score=vap["trustScore"],
            )
            trust_score = float(vap["trustScore"]["score"])
            audit_id = str(vap["audit"]["auditId"])
            verifications = vap["verifications"]

        ctx.state = transition(RunState.COMPLETING, RunState.COMPLETED)
        log.append(
            event_id=new_id("evt"),
            event_type="Completed",
            agent_id=spec.agent_id,
            run_id=ctx.run_id,
            ts=_now_rfc3339(),
            payload={
                "status": "ok",
                "vap": self.vap_enabled,
                "trustScore": trust_score,
            },
        )
        log.flush()
        return RunResult(
            run_id=ctx.run_id,
            tip_hash=log.tip_hash,
            events_path=log.path,
            state=ctx.state.value,
            vap_enabled=self.vap_enabled,
            trust_score=trust_score,
            audit_id=audit_id,
            proof_path=proof_path,
            verifications=verifications,
            vap=vap,
        )

    def _fail(self, spec: AgentSpec, ctx: RunContext, log: EventLog, reason: str) -> RunResult:
        log.append(
            event_id=new_id("evt"),
            event_type="Failed",
            agent_id=spec.agent_id,
            run_id=ctx.run_id,
            ts=_now_rfc3339(),
            payload={"reason": reason},
        )
        ctx.state = RunState.FAILED
        log.flush()
        return RunResult(
            run_id=ctx.run_id,
            tip_hash=log.tip_hash,
            events_path=log.path,
            state=ctx.state.value,
        )

    def _execute_tool_flow(
        self,
        *,
        spec: AgentSpec,
        ctx: RunContext,
        log: EventLog,
        tool_name: str,
        tool_input: dict[str, Any],
        auto_approve_ask: bool,
    ) -> None:
        defn = load_tool_definition(tool_name)
        policy_ref = spec.raw["spec"]["policy"]["ref"]
        permissions = spec.raw["spec"].get("permissions", [])

        for perm in defn.get("requiredPermissions", []):
            # Constitution Runtime Execute (package rules + fleet) — deny wins
            gov = self.governance.execute(action=perm, agent_id=spec.agent_id)
            if gov.get("packageId"):
                log.append(
                    event_id=new_id("evt"),
                    event_type="GovernanceEvaluated",
                    agent_id=spec.agent_id,
                    run_id=ctx.run_id,
                    ts=_now_rfc3339(),
                    payload={"decision": gov},
                )
            if gov["decision"] == "deny":
                raise AuthorizationError(f"governance denied: {perm} ({'; '.join(gov.get('reasons') or [])})")
            if gov["decision"] == "ask" and not auto_approve_ask:
                ctx.pending_ask = {"tool": tool_name, "input": tool_input, "permission": perm}
                log.append(
                    event_id=new_id("evt"),
                    event_type="ActionExecuted",
                    agent_id=spec.agent_id,
                    run_id=ctx.run_id,
                    ts=_now_rfc3339(),
                    payload={"status": "awaiting_input", "tool": tool_name, "governance": gov},
                )
                raise UapRuntimeError("awaiting_input")

            decision = self.policy.evaluate(
                policy_ref=policy_ref,
                agent_permissions=permissions,
                permission=perm,
                parameters=tool_input,
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
            )
            ctx.policy_decisions.append(decision)
            log.append(
                event_id=new_id("evt"),
                event_type="PolicyEvaluated",
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
                ts=_now_rfc3339(),
                payload={"decision": decision},
            )
            if decision["decision"] == "deny":
                raise AuthorizationError(f"denied: {perm}")
            if decision["decision"] == "ask" and not auto_approve_ask:
                ctx.pending_ask = {"tool": tool_name, "input": tool_input, "permission": perm}
                log.append(
                    event_id=new_id("evt"),
                    event_type="ActionExecuted",
                    agent_id=spec.agent_id,
                    run_id=ctx.run_id,
                    ts=_now_rfc3339(),
                    payload={"status": "awaiting_input", "tool": tool_name},
                )
                raise UapRuntimeError("awaiting_input")

        req_evt = log.append(
            event_id=new_id("evt"),
            event_type="ToolCallRequested",
            agent_id=spec.agent_id,
            run_id=ctx.run_id,
            ts=_now_rfc3339(),
            payload={
                "toolName": tool_name,
                "inputHash": sha256_obj(tool_input),
                "input": tool_input,
            },
        )
        output, evidence = execute_tool(
            tool_name,
            tool_input,
            evidence_store=self.evidence_store,
            provenance={
                "agentId": spec.agent_id,
                "runId": ctx.run_id,
                "toolName": tool_name,
                "permission": defn.get("requiredPermissions", [""])[0],
                "parentEventId": req_evt["eventId"],
            },
        )
        if defn.get("sideEffect") in {"external", "irreversible"} and evidence is None:
            raise EvidenceError(f"missing evidence for {tool_name}")

        exec_evt = log.append(
            event_id=new_id("evt"),
            event_type="ToolCallExecuted",
            agent_id=spec.agent_id,
            run_id=ctx.run_id,
            ts=_now_rfc3339(),
            payload={
                "toolName": tool_name,
                "status": "ok",
                "outputHash": sha256_obj(output),
                "durationMs": 1,
            },
        )
        if evidence:
            ctx.evidence.append(evidence)
            _, blob = self.evidence_store.load(evidence["evidenceId"])
            ctx.evidence_blobs[evidence["evidenceId"]] = blob
            log.append(
                event_id=new_id("evt"),
                event_type="EvidenceAttached",
                agent_id=spec.agent_id,
                run_id=ctx.run_id,
                ts=_now_rfc3339(),
                payload={
                    "evidenceId": evidence["evidenceId"],
                    "contentHash": evidence["contentHash"],
                    "parentEventId": exec_evt["eventId"],
                },
            )
            # Phase 2: verify each action's evidence immediately
            if self.vap_enabled:
                action_vs = [
                    verify_hash_match(evidence, blob),
                    verify_freshness(evidence),
                ]
                if evidence.get("type") == "receipt":
                    action_vs.append(verify_receipt_presence(evidence))
                for v in action_vs:
                    ctx.action_verifications.append(v)
                    log.append(
                        event_id=new_id("evt"),
                        event_type="Verified",
                        agent_id=spec.agent_id,
                        run_id=ctx.run_id,
                        ts=_now_rfc3339(),
                        payload={
                            "verification": v,
                            "scope": "action",
                            "tool": tool_name,
                        },
                    )
        log.append(
            event_id=new_id("evt"),
            event_type="ActionExecuted",
            agent_id=spec.agent_id,
            run_id=ctx.run_id,
            ts=_now_rfc3339(),
            payload={"tool": tool_name, "status": "ok", "output": output},
        )

    def load_events(self, run_id: str) -> list[dict[str, Any]]:
        path = self.runs_dir / run_id / "events.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        return EventLog.load_static(path)

    def list_runs(self) -> list[str]:
        if not self.runs_dir.exists():
            return []
        return sorted([p.name for p in self.runs_dir.iterdir() if p.is_dir()])
