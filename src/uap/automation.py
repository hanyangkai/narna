"""Automation — Decision OS stub: trigger → decision → approval → done."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .decision import DecisionEngine
from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AutomationEngine:
    """Run a governed automation pipeline without executing host side-effects."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.decisions = DecisionEngine(self.workspace)

    def run(
        self,
        *,
        trigger: str,
        action: str,
        context: dict[str, Any] | None = None,
        path: str | Path | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """
        Pipeline: Trigger → Decision evaluate → Governance gate → (stub) Execute plan.

        Does NOT send email / write ERP — returns an execution plan for the host.
        """
        run_id = new_id("auto")
        ctx = dict(context or {})
        ctx.setdefault("trigger", trigger)
        decision = self.decisions.evaluate(
            action=action,
            context=ctx,
            path=path,
            provider=provider,
        )
        gate = decision.get("decision")
        steps = [
            {"step": "trigger", "trigger": trigger, "at": _now()},
            {"step": "decision", "result": decision},
            {"step": "governance_gate", "decision": gate},
        ]
        execute_plan: list[dict[str, Any]] = []
        if gate == "allow":
            execute_plan = [
                {"op": "notify", "channel": "email", "template": "decision_allowed"},
                {"op": "erp.write", "status": "approved", "deferred": True},
            ]
            steps.append({"step": "execute_plan", "plan": execute_plan, "status": "ready"})
            status = "ready_to_execute"
        elif gate == "ask":
            execute_plan = [
                {
                    "op": "request_approval",
                    "approvals": decision.get("requiredApprovals") or [],
                }
            ]
            steps.append({"step": "await_approval", "plan": execute_plan})
            status = "awaiting_approval"
        else:
            steps.append({"step": "blocked", "reason": gate})
            status = "blocked"

        return {
            "ok": True,
            "runId": run_id,
            "status": status,
            "trigger": trigger,
            "action": action,
            "decision": decision,
            "executePlan": execute_plan,
            "steps": steps,
            "note": "Host must perform side-effects; NARNA governs only",
            "module": "Automation",
            "evaluatedAt": _now(),
        }
