from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .events import hash_event
from .hashing import ZERO_HASH
from .ids import new_id


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def audit_run(
    *,
    agent_id: str,
    run_id: str,
    events: list[dict[str, Any]],
    verifications: list[dict[str, Any]] | None = None,
    policy_decisions: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    verifications = verifications or []
    policy_decisions = policy_decisions or []
    evidence = evidence or []

    summary: dict[str, int] = {}
    for v in verifications:
        status = str(v.get("status", "unknown"))
        summary[status] = summary.get(status, 0) + 1

    violations: list[str] = []
    prev = ZERO_HASH
    for i, evt in enumerate(events):
        if evt.get("sequence") != i:
            violations.append(f"sequence gap at index {i}")
        body = {k: v for k, v in evt.items() if k != "eventHash"}
        if evt.get("hashPrev") != prev:
            violations.append(f"hashPrev mismatch at index {i}")
        prev = hash_event(body)

    # deny-then-execute detection
    denied = {d["permission"] for d in policy_decisions if d.get("decision") == "deny"}
    for evt in events:
        if evt.get("eventType") == "ToolCallExecuted":
            payload = evt.get("payload", {})
            tool = payload.get("toolName")
            if tool and denied:
                violations.append(f"tool executed after deny: {tool}")

    # missing evidence on irreversible/external tools
    attached = {e.get("payload", {}).get("evidenceId") for e in events if e.get("eventType") == "EvidenceAttached"}
    for evt in events:
        if evt.get("eventType") != "ToolCallExecuted":
            continue
        tool = evt.get("payload", {}).get("toolName", "")
        if tool.startswith("wallet.") and not attached:
            violations.append("irreversible tool without evidence")

    return {
        "auditId": new_id("audit"),
        "agentId": agent_id,
        "runId": run_id,
        "createdAt": _now_rfc3339(),
        "policyDecisions": [d.get("decisionId") for d in policy_decisions],
        "verificationSummary": summary,
        "violations": violations,
        "eventRange": {"fromSequence": 0, "toSequence": max(0, len(events) - 1)},
        "auditor": "vap-engine@0.1.0",
        "evidenceCount": len(evidence),
    }
