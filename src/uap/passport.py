from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .hashing import sha256_obj
from .identity import IdentityStore, spec_hash
from .ids import new_id
from .schemas import validator_for
from .spec import AgentSpec
from .trust import compute_trust_score_v0


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def aggregate_history(runs: list[dict[str, Any]]) -> dict[str, Any]:
    success = sum(1 for r in runs if r.get("terminal") == "Completed")
    failure = sum(1 for r in runs if r.get("terminal") == "Failed")
    violations = sum(r.get("violations", 0) for r in runs)
    last = runs[-1] if runs else None
    return {
        "runCount": len(runs),
        "successCount": success,
        "failureCount": failure,
        "violationCount": violations,
        "lastRunAt": last.get("ts") if last else None,
        "lastRunId": last.get("runId") if last else None,
    }


def observed_capabilities(events: list[dict[str, Any]]) -> list[str]:
    caps: set[str] = set()
    for evt in events:
        if evt.get("eventType") == "ToolCallExecuted":
            tool = evt.get("payload", {}).get("toolName", "")
            if "coinbase" in tool or "binance" in tool:
                caps.add("trade")
            if "wallet" in tool:
                caps.add("wallet")
    return sorted(caps)


def build_passport(
    *,
    spec: AgentSpec,
    identity: dict[str, Any] | None = None,
    trust_score: dict[str, Any] | None = None,
    history: dict[str, Any] | None = None,
    derived_from: str | None = None,
    observed: list[str] | None = None,
    ttl_hours: int = 24,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    issued = now.isoformat().replace("+00:00", "Z")
    expires = (now + timedelta(hours=ttl_hours)).isoformat().replace("+00:00", "Z")

    trust = trust_score or {
        "score": 0.5,
        "algorithm": "vap-trust-v0",
        "computedAt": issued,
        "breakdown": {"evidence": 0.5, "policy": 0.5, "execution": 0.5, "feedback": 0.5},
    }
    hist = history or {"runCount": 0, "successCount": 0, "failureCount": 0, "violationCount": 0}

    id_section = identity or {
        "agentId": spec.agent_id,
        "specHash": spec_hash(spec),
    }

    passport = {
        "passportId": new_id("passport"),
        "issuedAt": issued,
        "expiresAt": expires,
        "derivedFrom": derived_from,
        "identity": id_section,
        "capability": {
            "declared": list(spec.raw.get("spec", {}).get("capability", [])),
            "observed": observed or [],
        },
        "permissions": list(spec.raw.get("spec", {}).get("permissions", [])),
        "history": hist,
        "trust": {
            "score": trust.get("score", 0.5),
            "algorithm": trust.get("algorithm", "vap-trust-v0"),
            "computedAt": trust.get("computedAt", issued),
            "breakdown": trust.get("breakdown", {}),
            "trustScoreRef": trust.get("inputsHash"),
        },
    }
    validator_for("passport.schema.json").validate(passport)
    return passport


def refresh_passport(
    *,
    spec: AgentSpec,
    workspace: Path,
    runtime_runs: list[str],
    load_events_fn,
) -> dict[str, Any]:
    identity = IdentityStore(workspace).load()
    run_summaries: list[dict[str, Any]] = []
    all_events: list[dict[str, Any]] = []
    tip = None
    latest_trust = None

    for run_id in runtime_runs:
        events = load_events_fn(run_id)
        if not events:
            continue
        all_events.extend(events)
        tip = events[-1].get("eventHash")
        terminal = next(
            (e.get("eventType") for e in reversed(events) if e.get("eventType") in {"Completed", "Failed"}),
            None,
        )
        run_summaries.append(
            {
                "runId": run_id,
                "terminal": terminal,
                "ts": events[-1].get("ts"),
                "violations": 0,
            }
        )
        bundle_path = workspace / ".uap" / "runs" / run_id / "proof-bundle.json"
        if bundle_path.exists():
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            latest_trust = bundle.get("trustScore")

    if latest_trust is None and all_events:
        latest_trust = compute_trust_score_v0(
            agent_id=spec.agent_id,
            run_id=run_summaries[-1]["runId"] if run_summaries else "none",
            events=all_events[-20:],
        )

    return build_passport(
        spec=spec,
        identity=identity,
        trust_score=latest_trust,
        history=aggregate_history(run_summaries),
        derived_from=tip,
        observed=observed_capabilities(all_events),
    )
