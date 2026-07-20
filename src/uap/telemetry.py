"""Privacy-preserving Governance Telemetry — sanitize + contribute builders.

Normative: specs/governance-telemetry/SPEC.md
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"

# Fields / keys that MUST never leave the machine via telemetry
_FORBIDDEN_KEY_RE = re.compile(
    r"(prompt|message|content|input|output|argument|result|body|sql|"
    r"url|path|email|token|secret|password|authorization|cookie|header|"
    r"receipt|evidence|raw)",
    re.I,
)

_CAPABILITY_MAP = (
    (re.compile(r"sql|database|postgres|mysql|query", re.I), "database.query"),
    (re.compile(r"browser|playwright|puppete|selenium", re.I), "browser.navigate"),
    (re.compile(r"search|bing|google|serp", re.I), "search.query"),
    (re.compile(r"email|smtp|sendgrid|mail", re.I), "comms.email"),
    (re.compile(r"wallet|transfer|payment|stripe|paddle|bank", re.I), "finance.transfer"),
    (re.compile(r"file|fs\.|filesystem|s3", re.I), "filesystem"),
    (re.compile(r"http|fetch|request|api", re.I), "network.fetch"),
    (re.compile(r"vision|camera|image", re.I), "perception.vision"),
    (re.compile(r"move|motor|robot|actuator", re.I), "robot.actuate"),
    (re.compile(r"llm|chat|completion|openai|anthropic", re.I), "model.infer"),
)

_AGENT_CLASS_MAP = (
    (re.compile(r"finance|bank|trading|ledger", re.I), "finance"),
    (re.compile(r"browser|web", re.I), "browser"),
    (re.compile(r"research|search|rag", re.I), "research"),
    (re.compile(r"robot|drone|actuator", re.I), "robot"),
    (re.compile(r"medical|clinical|hipaa|phi", re.I), "medical"),
    (re.compile(r"plan", re.I), "planner"),
)

_POLICY_FAMILY_RE = re.compile(
    r"(gdpr|eu-ai-act|hipaa|pci|ccpa|soc2|nist|iso-42001|pipl|lgpd|"
    r"enterprise|local-default|anthropic|financial)",
    re.I,
)


def telemetry_opt_in_from_env() -> bool:
    return os.environ.get("NARNA_TELEMETRY_OPT_IN", os.environ.get("UAP_TELEMETRY_OPT_IN", "0")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def train_opt_in_from_env() -> bool:
    return os.environ.get("NARNA_TELEMETRY_TRAIN_OPT_IN", "0").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def telemetry_salt() -> str:
    return os.environ.get("NARNA_TELEMETRY_SALT", os.environ.get("UAP_TELEMETRY_SALT", "narna-telemetry-v0"))


def hmac_hash(value: str, *, prefix: str) -> str:
    digest = hmac.new(
        telemetry_salt().encode("utf-8"),
        (value or "").encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return f"{prefix}_{digest}"


def capability_family(tool_name: str | None, label: str | None = None) -> str:
    blob = f"{tool_name or ''} {label or ''}".strip()
    if not blob:
        return "unknown"
    for pattern, family in _CAPABILITY_MAP:
        if pattern.search(blob):
            return family
    # Coarse bucket — never emit raw tool name into telemetry
    return "tool.other"


def agent_class(agent_id: str | None, agent_name: str | None = None) -> str:
    blob = f"{agent_id or ''} {agent_name or ''}".strip()
    for pattern, cls in _AGENT_CLASS_MAP:
        if pattern.search(blob):
            return cls
    return "general"


def policy_family(policy_ref: str | None) -> str:
    if not policy_ref:
        return "unspecified"
    m = _POLICY_FAMILY_RE.search(str(policy_ref))
    if m:
        return m.group(1).lower()
    # Hash unknown refs so they aren't identifying strings
    return "policy_" + hashlib.sha256(str(policy_ref).encode()).hexdigest()[:8]


def trust_band(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 80:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def risk_band(level: str | None) -> str | None:
    if not level:
        return None
    level = str(level).lower()
    if level in {"low", "medium", "high", "critical"}:
        return level
    return None


def strip_forbidden(obj: Any) -> Any:
    """Deep-strip forbidden keys from arbitrary JSON-like structures."""
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if _FORBIDDEN_KEY_RE.search(str(k)):
                continue
            out[str(k)] = strip_forbidden(v)
        return out
    if isinstance(obj, list):
        return [strip_forbidden(x) for x in obj]
    if isinstance(obj, str) and len(obj) > 256:
        # Long free-text is content — drop
        return "[redacted]"
    return obj


def _failure_class(event_type: str, payload: dict[str, Any]) -> str | None:
    et = event_type.lower()
    if "loop" in et:
        return "loop"
    if "budget" in et:
        return "budget"
    if "permission" in et or payload.get("decision") == "deny":
        if "permission" in json.dumps(payload).lower():
            return "permission_denied"
        return "policy_violation"
    if "timeout" in et:
        return "timeout"
    if et in {"failed", "aborted"}:
        return "other"
    return None


def build_contribution_from_events(
    *,
    events: list[dict[str, Any]],
    org_id: str | int,
    agent_id: str = "",
    agent_name: str = "",
    trust_score: float | None = None,
    telemetry_opt_in: bool = True,
    train_opt_in: bool = False,
) -> dict[str, Any]:
    """Build a GovernanceTelemetryContribution from a local EventLog (sanitized)."""
    if not telemetry_opt_in:
        raise ValueError("telemetryOptIn is false — contribution forbidden")

    cls = agent_class(agent_id, agent_name)
    tband = trust_band(trust_score)
    session_raw = next((e.get("sessionId") for e in events if e.get("sessionId")), None)

    # Index EU starts for graph order
    nodes: list[dict[str, Any]] = []
    eu_index: dict[str, int] = {}
    edges: list[dict[str, int]] = []
    human_approvals = 0
    denies = 0
    total_gu = 0

    # Policy decisions keyed by sequence for attachment
    last_decision: dict[str, Any] | None = None

    for evt in events:
        et = str(evt.get("eventType") or "")
        payload = evt.get("payload") if isinstance(evt.get("payload"), dict) else {}

        if et in {"PolicyEvaluated", "GovernanceEvaluated"}:
            decision = payload.get("decision")
            if isinstance(decision, dict):
                last_decision = decision
                if decision.get("decision") == "deny":
                    denies += 1
                if decision.get("decision") in {"ask", "require"}:
                    human_approvals += 1
            continue

        if et == "ExecutionUnitStarted":
            eu = payload.get("executionUnit") if isinstance(payload.get("executionUnit"), dict) else payload
            unit_id = str(eu.get("unitId") or eu.get("executionUnitId") or "")
            kind = str(eu.get("unitKind") or "tool").lower()
            if kind not in {"tool", "llm", "subagent", "mcp", "workflow"}:
                kind = "other"
            gu = int(eu.get("guCost") or 1)
            total_gu += gu
            tool = eu.get("toolName") or eu.get("label")
            node = {
                "agentClass": cls,
                "unitKind": kind,
                "capabilityFamily": capability_family(
                    str(tool) if tool else None,
                    str(eu.get("label") or "") or None,
                ),
                "policyFamily": policy_family(
                    (last_decision or {}).get("policyRef") if last_decision else None
                ),
                "decision": (last_decision or {}).get("decision") if last_decision else None,
                "humanApproval": bool(
                    last_decision and last_decision.get("decision") in {"ask", "require"}
                ),
                "outcome": "unknown",
                "riskBand": risk_band(eu.get("riskLevel") or (last_decision or {}).get("riskLevel")),
                "failureClass": None,
                "guCost": gu,
                "trustBand": tband,
            }
            idx = len(nodes)
            nodes.append(node)
            if unit_id:
                eu_index[unit_id] = idx
            parent = eu.get("parentUnitId") or eu.get("parentExecutionUnitId")
            if parent and str(parent) in eu_index:
                edges.append({"from": eu_index[str(parent)], "to": idx})
            continue

        if et in {"ExecutionUnitCompleted", "Completed"}:
            # Mark last unknown node success if we can
            for n in reversed(nodes):
                if n["outcome"] == "unknown":
                    n["outcome"] = "success"
                    break
            continue

        if et in {"Failed", "Aborted", "BudgetExceeded", "LoopDetected"}:
            fc = _failure_class(et, payload)
            for n in reversed(nodes):
                if n["outcome"] == "unknown":
                    n["outcome"] = "failure" if et == "Failed" else ("aborted" if et == "Aborted" else "failure")
                    n["failureClass"] = fc
                    break

    if not nodes:
        # Still contribute a session-level summary node from terminal state
        state = "unknown"
        for evt in reversed(events):
            if evt.get("eventType") in {"Completed", "Failed", "Aborted"}:
                state = str(evt["eventType"]).lower()
                break
        nodes.append(
            {
                "agentClass": cls,
                "unitKind": "other",
                "capabilityFamily": "session",
                "policyFamily": "unspecified",
                "decision": None,
                "humanApproval": False,
                "outcome": "success" if state == "completed" else ("failure" if state == "failed" else "unknown"),
                "riskBand": None,
                "failureClass": None,
                "guCost": 0,
                "trustBand": tband,
            }
        )

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "apiVersion": "narna.ai/v1alpha1",
        "kind": "GovernanceTelemetryContribution",
        "metadata": {
            "schemaVersion": SCHEMA_VERSION,
            "contributedAt": now,
            "consent": {
                "telemetryOptIn": True,
                "trainOptIn": bool(train_opt_in),
            },
        },
        "spec": {
            "tenantHash": hmac_hash(str(org_id), prefix="th"),
            "sessionHash": hmac_hash(str(session_raw), prefix="sh") if session_raw else None,
            "nodes": nodes,
            "edges": edges,
            "totals": {
                "gu": total_gu,
                "nodes": len(nodes),
                "humanApprovals": human_approvals,
                "denies": denies,
            },
        },
    }


def build_contribution_from_run_dir(
    *,
    workspace: Path,
    run_id: str,
    org_id: str | int,
    agent_id: str = "",
    agent_name: str = "",
    telemetry_opt_in: bool | None = None,
    train_opt_in: bool | None = None,
) -> dict[str, Any]:
    opt_in = telemetry_opt_in if telemetry_opt_in is not None else telemetry_opt_in_from_env()
    train = train_opt_in if train_opt_in is not None else train_opt_in_from_env()
    runs_dir = workspace / ".uap" / "runs" / run_id
    events_path = runs_dir / "events.jsonl"
    if not events_path.exists():
        raise FileNotFoundError(f"run not found: {run_id}")
    events: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    trust: float | None = None
    proof_path = runs_dir / "proof-bundle.json"
    if proof_path.exists():
        pb = json.loads(proof_path.read_text(encoding="utf-8"))
        ts = pb.get("trustScore")
        if isinstance(ts, dict) and "score" in ts:
            trust = float(ts["score"])
        elif isinstance(ts, (int, float)):
            trust = float(ts)
    return build_contribution_from_events(
        events=events,
        org_id=org_id,
        agent_id=agent_id or (events[0].get("agentId", "") if events else ""),
        agent_name=agent_name,
        trust_score=trust,
        telemetry_opt_in=opt_in,
        train_opt_in=train,
    )
