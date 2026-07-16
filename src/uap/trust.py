from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .events import hash_event
from .hashing import ZERO_HASH, sha256_obj


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _chain_intact(events: list[dict[str, Any]]) -> bool:
    prev = ZERO_HASH
    for evt in events:
        body = {k: v for k, v in evt.items() if k != "eventHash"}
        if evt.get("hashPrev") != prev:
            return False
        prev = hash_event(body)
    return True


def compute_trust_score_v0(
    *,
    agent_id: str,
    run_id: str,
    events: list[dict[str, Any]],
    verifications: list[dict[str, Any]] | None = None,
    policy_decisions: list[dict[str, Any]] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    feedback: float | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    weights = weights or {"evidence": 0.4, "policy": 0.2, "execution": 0.2, "feedback": 0.2}
    caps: list[str] = []
    verifications = verifications or []
    policy_decisions = policy_decisions or []
    evidence = evidence or []

    execution = 1.0
    if not _chain_intact(events):
        execution = 0.0
        caps.append("broken_chain")
    for i, evt in enumerate(events):
        if evt.get("sequence") != i:
            execution = 0.0
            caps.append("broken_chain")
            break

    policy = 1.0
    denied = [d for d in policy_decisions if d.get("decision") == "deny"]
    tool_after_deny = any(e.get("eventType") == "ToolCallExecuted" for e in events) and bool(denied)
    if tool_after_deny:
        policy = 0.0
        caps.append("deny_bypass")

    if verifications:
        valid = sum(1 for v in verifications if v.get("status") == "valid")
        evidence_score = valid / len(verifications)
        if any(v.get("status") == "invalid" for v in verifications):
            caps.append("invalid_evidence")
    elif evidence:
        evidence_score = 0.8
    else:
        evidence_score = 0.5

    irreversible_without_receipt = any(
        e.get("eventType") == "ToolCallExecuted"
        and str(e.get("payload", {}).get("toolName", "")).startswith("wallet.")
        for e in events
    ) and not any(ev.get("type") == "receipt" for ev in evidence)
    if irreversible_without_receipt:
        evidence_score = min(evidence_score, 0.2)
        caps.append("missing_receipt")

    fb = 0.5 if feedback is None else max(0.0, min(1.0, feedback))
    breakdown = {
        "evidence": evidence_score,
        "policy": policy,
        "execution": execution,
        "feedback": fb,
    }
    score = sum(breakdown[k] * weights[k] for k in weights)

    if "broken_chain" in caps:
        score = min(score, 0.2)
        breakdown["execution"] = 0.0
    if "deny_bypass" in caps:
        score = min(score, 0.1)
        breakdown["policy"] = 0.0
    if "missing_receipt" in caps:
        score = min(score, max(score, 0.2))

    inputs = {
        "agentId": agent_id,
        "runId": run_id,
        "eventCount": len(events),
        "verificationCount": len(verifications),
        "weights": weights,
        "breakdown": breakdown,
    }

    return {
        "score": round(score, 4),
        "breakdown": breakdown,
        "weights": weights,
        "reasons": [f"{k}={breakdown[k]:.2f}" for k in breakdown],
        "computedAt": _now_rfc3339(),
        "inputsHash": sha256_obj(inputs),
        "algorithm": "vap-trust-v0",
        "agentId": agent_id,
        "runId": run_id,
        "capsApplied": caps,
    }
