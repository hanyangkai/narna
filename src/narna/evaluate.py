"""Public one-liner SDK — wrap any agent decision with NARNA ADQA."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def evaluate(
    decision: dict[str, Any] | None = None,
    *,
    action: str | None = None,
    evidence: list[str] | None = None,
    context: dict[str, Any] | None = None,
    question: str | None = None,
    workspace: str | Path | None = None,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Score a proposed decision with ADQA (DQS + Guardian).

    Usage::

        from narna import evaluate
        result = evaluate({"action": "contract.sign", "evidence": ["contract.reviewed"]})
        # or
        result = evaluate(action="deploy.prod", evidence=["tests.passed"])
    """
    from uap.adqa import ADQAEngine

    payload = dict(decision or {})
    act = action or str(payload.get("action") or "").strip()
    if not act:
        raise ValueError("action required")
    ev = evidence if evidence is not None else payload.get("evidence") or payload.get("evidencePresent") or []
    if isinstance(ev, str):
        ev = [x.strip() for x in ev.split(",") if x.strip()]
    ctx = context if context is not None else payload.get("context")
    if not isinstance(ctx, dict):
        ctx = {}
    q = question or payload.get("question")

    out = ADQAEngine(workspace or Path.cwd()).check_proposed(
        action=act,
        provider=str(payload.get("provider") or "legal-decision"),
        evidence_present=[str(x) for x in ev],
        context=ctx,
        agent_id=agent_id or str(payload.get("agentId") or "") or None,
        question=str(q) if q else None,
    )
    # check_proposed nests ADQA under "adqa" key when decision package attached
    nested = out.get("adqa") if isinstance(out.get("adqa"), dict) else {}
    dqs = out.get("dqs")
    if dqs is None:
        dqs = nested.get("dqs")
    guardian = out.get("guardian") or nested.get("guardian")
    guardian_l = str(guardian or "").lower()
    if guardian_l in {"reject", "block", "deny"} or str(out.get("decision") or "").lower() == "deny":
        verdict = "REJECT"
    elif guardian_l in {"revise", "review", "ask", "escalate"} or (
        isinstance(dqs, (int, float)) and dqs < 70
    ):
        verdict = "REVIEW"
    else:
        verdict = "ACT"
    return {
        "ok": True,
        "action": act,
        "dqs": dqs,
        "guardian": guardian,
        "verdict": verdict,
        "adqa": nested or out,
        "standard": "NGS-0024",
    }
