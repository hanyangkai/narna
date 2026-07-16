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
    constitution: dict[str, Any] | None = None,
    governance_binding: dict[str, Any] | None = None,
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
    # Drop null optional history fields (schema rejects null)
    hist = {k: v for k, v in hist.items() if v is not None}

    id_section = identity or {
        "agentId": spec.agent_id,
        "specHash": spec_hash(spec),
    }

    trust_block: dict[str, Any] = {
        "score": trust.get("score", 0.5),
        "algorithm": trust.get("algorithm", "vap-trust-v0"),
        "computedAt": trust.get("computedAt", issued),
        "breakdown": trust.get("breakdown", {}),
    }
    if trust.get("inputsHash"):
        trust_block["trustScoreRef"] = trust["inputsHash"]

    # Permissions in AgentSpec may be strings; passport schema expects objects
    raw_perms = list(spec.raw.get("spec", {}).get("permissions", []))
    permissions: list[dict[str, Any]] = []
    for p in raw_perms:
        if isinstance(p, dict) and "name" in p:
            permissions.append(p)
        elif isinstance(p, str):
            permissions.append({"name": p, "mode": "allow"})

    passport = {
        "passportId": new_id("passport"),
        "issuedAt": issued,
        "expiresAt": expires,
        "identity": id_section,
        "capability": {
            "declared": list(spec.raw.get("spec", {}).get("capability", [])),
            "observed": observed or [],
        },
        "permissions": permissions,
        "history": hist,
        "trust": trust_block,
    }
    if derived_from:
        passport["derivedFrom"] = derived_from

    # C1: cite Constitution when available
    const_ref = _constitution_ref(constitution)
    if const_ref:
        passport["constitution"] = const_ref

    gov_ref = _governance_ref(governance_binding)
    if gov_ref:
        passport["governance"] = gov_ref

    validator_for("passport.schema.json").validate(passport)
    return passport


def sign_and_optionally_score(
    passport: dict[str, Any],
    workspace: Path,
    *,
    attach_score: bool = True,
) -> dict[str, Any]:
    """Sign passport and attach NARNA Score snapshot."""
    from .passport_sign import sign_passport

    if attach_score:
        try:
            from .narna_score import compute_narna_score

            score = compute_narna_score(workspace)
            passport = {**passport, "narnaScore": score}
        except Exception:
            pass
    return sign_passport(passport, workspace)


def _governance_ref(binding: dict[str, Any] | None) -> dict[str, str] | None:
    if not binding:
        return None
    pkg_hash = binding.get("packageHash")
    if not pkg_hash:
        return None
    out: dict[str, str] = {
        "packageId": str(binding.get("packageId") or ""),
        "provider": str(binding.get("provider") or "local"),
        "version": str(binding.get("version") or "0.0.0"),
        "packageHash": str(pkg_hash),
    }
    return out


def load_active_governance_binding(workspace: Path) -> dict[str, Any] | None:
    path = workspace / ".uap" / "runtime" / "active-governance.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _constitution_ref(constitution: dict[str, Any] | None) -> dict[str, str] | None:
    if not constitution:
        return None
    meta = constitution.get("metadata") or {}
    cid = meta.get("id")
    if not cid:
        return None
    return {
        "constitutionId": str(cid),
        "constitutionHash": sha256_obj(constitution),
        "version": str(meta.get("version", "0.1.0")),
    }


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

    constitution = None
    const_path = workspace / "constitution.yaml"
    if const_path.exists():
        try:
            from .constitution import load_constitution

            constitution = load_constitution(const_path)
            # Link universal identity → constitution when possible
            store = IdentityStore(workspace)
            uni = store.load_entity(spec.agent_id)
            cid = constitution.get("metadata", {}).get("id")
            if uni and cid and not uni.get("constitutionId"):
                store.issue_entity(
                    kind="Agent",
                    entity_id=spec.agent_id,
                    owner=str(uni.get("owner") or uni.get("creator") or "local"),
                    version=str(uni.get("version") or spec.version),
                    content_hash=str(uni.get("contentHash") or uni.get("specHash") or spec_hash(spec)),
                    created_at=str(uni.get("createdAt") or _now_rfc3339()),
                    origin=uni.get("origin"),
                    license=uni.get("license"),
                    constitution_id=str(cid),
                )
                identity = store.load() or identity
        except Exception:
            constitution = None

    return sign_and_optionally_score(
        build_passport(
            spec=spec,
            identity=identity,
            trust_score=latest_trust,
            history=aggregate_history(run_summaries),
            derived_from=tip,
            observed=observed_capabilities(all_events),
            constitution=constitution,
            governance_binding=load_active_governance_binding(workspace),
        ),
        workspace,
    )
