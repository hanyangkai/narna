from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .hashing import sha256_obj
from .ids import new_id
from .permissions import check_constraints, find_grant


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_policy_ref(ref: str, workspace: Path) -> Path:
    name = ref.split("@")[0].split("/")[-1]
    here = Path(__file__).resolve().parent
    candidates = [
        workspace / "policies" / f"{name}.yaml",
        here / "_policies" / f"{name}.yaml",
    ]
    for parent in here.parents:
        candidate = parent / "policies" / f"{name}.yaml"
        if candidate not in candidates:
            candidates.append(candidate)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"policy pack not found for ref: {ref}")


def load_policy_pack(ref: str, workspace: Path) -> dict[str, Any]:
    path = resolve_policy_ref(ref, workspace)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("policy pack must be a mapping")
    return raw


class PolicyEngine:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def evaluate(
        self,
        *,
        policy_ref: str,
        agent_permissions: list[dict[str, Any]],
        permission: str,
        parameters: dict[str, Any] | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        parameters = parameters or {}
        pack = load_policy_pack(policy_ref, self.workspace)
        rules = {r["permission"]: r for r in pack.get("rules", [])}

        grant = find_grant(agent_permissions, permission)
        rule = rules.get(permission)

        # deny-by-default
        if grant is None and rule is None:
            return self._decision(
                decision="deny",
                permission=permission,
                parameters=parameters,
                policy_ref=policy_ref,
                reasons=["permission not declared and no policy rule"],
                agent_id=agent_id,
                run_id=run_id,
            )

        mode = (grant or {}).get("mode")
        if mode == "deny":
            return self._decision(
                decision="deny",
                permission=permission,
                parameters=parameters,
                policy_ref=policy_ref,
                reasons=["explicit deny in AgentSpec"],
                agent_id=agent_id,
                run_id=run_id,
            )

        decision = (rule or {}).get("decision") or mode or "deny"
        constraints = {}
        if grant and grant.get("constraints"):
            constraints.update(grant["constraints"])
        if rule and rule.get("constraints"):
            constraints.update(rule["constraints"])

        ok, reasons = check_constraints(constraints or None, parameters)
        if not ok:
            return self._decision(
                decision="deny",
                permission=permission,
                parameters=parameters,
                policy_ref=policy_ref,
                reasons=reasons,
                agent_id=agent_id,
                run_id=run_id,
                constraints_applied=constraints,
            )

        if decision == "ask":
            reasons = ["permission mode is ask", "awaiting human/org resolution"]
        elif decision == "allow":
            reasons = ["permission allowed by policy"]
        else:
            reasons = ["deny-by-default"]

        return self._decision(
            decision=decision,
            permission=permission,
            parameters=parameters,
            policy_ref=policy_ref,
            reasons=reasons,
            agent_id=agent_id,
            run_id=run_id,
            constraints_applied=constraints,
        )

    def _decision(
        self,
        *,
        decision: str,
        permission: str,
        parameters: dict[str, Any],
        policy_ref: str,
        reasons: list[str],
        agent_id: str | None,
        run_id: str | None,
        constraints_applied: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = {
            "permission": permission,
            "parameters": parameters,
            "policyRef": policy_ref,
        }
        return {
            "decisionId": new_id("pd"),
            "decision": decision,
            "permission": permission,
            "parameters": parameters,
            "reasons": reasons,
            "policyRef": policy_ref,
            "evaluatedAt": _now_rfc3339(),
            "inputHash": sha256_obj(normalized),
            "agentId": agent_id,
            "runId": run_id,
            "constraintsApplied": constraints_applied or {},
        }
