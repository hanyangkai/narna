"""Capability Governor — Guardian Layer 2 (NGS-0015).

Evaluates Capability Passport grants before side effects.
Does not implement full container isolation (host concern).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .hashing import sha256_obj

MODE_RANK = {
    "allow": 0,
    "ask": 1,
    "sandbox": 2,
    "whitelist": 3,
    "multisig": 4,
    "restricted": 5,
    "deny": 6,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_capability_passport(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("CapabilityPassport must be a mapping")
    if raw.get("kind") != "CapabilityPassport":
        raise ValueError("kind must be CapabilityPassport")
    return raw


def default_guardian_grants() -> list[dict[str, Any]]:
    """Conservative defaults when no passport file is bound."""
    return [
        {"capability": "search", "mode": "allow"},
        {"capability": "filesystem", "mode": "sandbox"},
        {"capability": "email", "mode": "ask"},
        {"capability": "terminal", "mode": "sandbox"},
        {"capability": "code", "mode": "sandbox"},
        {"capability": "mcp", "mode": "whitelist"},
        {"capability": "wallet", "mode": "deny"},
        {"capability": "trade", "mode": "multisig", "approvalsRequired": 2},
        {"capability": "create.agent", "mode": "restricted"},
    ]


class CapabilityGovernor:
    """Evaluate capability modes for an agent (Guardian profile)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def _resolve_doc(
        self,
        *,
        path: str | Path | None = None,
        document: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if document is not None:
            return document
        if path:
            return load_capability_passport(Path(path))
        for cand in (
            self.workspace / "capability-passport.yaml",
            self.workspace / ".uap" / "capability-passport.yaml",
            Path(__file__).resolve().parent / "_packages" / "capability-passport-default.yaml",
        ):
            if cand.exists():
                return load_capability_passport(cand)
        return None

    def evaluate(
        self,
        *,
        capability: str,
        agent_id: str | None = None,
        path: str | Path | None = None,
        document: dict[str, Any] | None = None,
        target: str | None = None,
        profile: str = "guardian",
    ) -> dict[str, Any]:
        capability = str(capability or "").strip().lower()
        if not capability:
            raise ValueError("capability is required")

        doc = self._resolve_doc(path=path, document=document)
        if doc is None:
            grants = default_guardian_grants() if profile == "guardian" else []
            meta: dict[str, Any] = {"agentId": agent_id or "anonymous", "version": "default"}
            quotas: dict[str, Any] = {
                "maxSpawnDepth": 1,
                "maxApiCallsPerHour": 100,
                "maxGuPerDay": 10000,
            }
            isolation = {"network": "deny-by-default", "filesystem": "workspace-only"}
            package_hash = None
        else:
            meta = doc.get("metadata") or {}
            spec = doc.get("spec") or {}
            grants = list(spec.get("grants") or [])
            quotas = dict(spec.get("quotas") or {})
            isolation = dict(spec.get("isolation") or {})
            package_hash = sha256_obj(doc)

        matched = None
        exact: dict[str, Any] | None = None
        for g in grants:
            cap = str(g.get("capability") or "").lower()
            if not cap:
                continue
            if cap == capability:
                exact = g
                break
            # namespaced: payment.send matches grant payment
            if capability.startswith(cap + ".") or capability.startswith(cap + "_"):
                if matched is None or MODE_RANK.get(str(g.get("mode")), 0) > MODE_RANK.get(
                    str(matched.get("mode")), 0
                ):
                    matched = g
        matched = exact or matched
        if matched is None:
            # Guardian deny-by-default for unknown capabilities
            decision = "deny" if profile == "guardian" else "ask"
            reasons = [f"no grant for capability={capability} (profile={profile})"]
            approvals: list[str] = []
        else:
            decision = str(matched.get("mode") or "deny").lower()
            reasons = [f"grant {matched.get('capability')}: mode={decision}"]
            approvals = []
            if decision in {"ask", "multisig", "restricted"}:
                n = int(matched.get("approvalsRequired") or (2 if decision == "multisig" else 1))
                approvals = [f"human.approval:{i+1}/{n}" for i in range(n)]
            if decision == "whitelist" and target:
                allowed = [str(x) for x in (matched.get("whitelist") or [])]
                if allowed and target not in allowed:
                    decision = "deny"
                    reasons.append(f"target {target!r} not in whitelist")
            if matched.get("constraints"):
                reasons.append(f"constraints={matched.get('constraints')}")

        # Hard Guardian rules
        if capability in {"create.agent", "spawn.agent"} and decision == "allow":
            decision = "restricted"
            reasons.append("guardian: create.agent cannot be bare allow")
            approvals = approvals or ["governance.council"]

        # L3 collective capability restrictions (signature-applied overlays)
        try:
            from .collective import CollectiveDefense

            overlay = CollectiveDefense.active_restrictions(self.workspace, agent_id)
            if overlay and str(overlay.get("mode") or "").lower() == "deny":
                denied_caps = [str(c).lower() for c in (overlay.get("capabilities") or [])]
                if "*" in denied_caps or any(
                    capability == c or capability.startswith(c) or c in capability
                    for c in denied_caps
                ):
                    decision = "deny"
                    reasons.append(
                        f"collective/kill restrict sig={overlay.get('signatureId') or overlay.get('reason')} "
                        f"patterns={overlay.get('patterns')}"
                    )
        except Exception:
            pass

        # NGS-0018 reputation floor
        try:
            from .reputation import ReputationStore

            decision, rep_reasons = ReputationStore(self.workspace).tighten_decision(
                decision, agent_id
            )
            reasons.extend(rep_reasons)
        except Exception:
            pass

        return {
            "ok": True,
            "decision": decision,
            "capability": capability,
            "agentId": agent_id or meta.get("agentId"),
            "reasons": reasons,
            "requiredApprovals": approvals,
            "quotas": quotas,
            "isolation": isolation,
            "profile": profile,
            "packageHash": package_hash,
            "evaluatedAt": _now(),
            "standard": "NGS-0015",
        }
