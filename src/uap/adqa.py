"""ADQA — Autonomous Decision Quality Assurance (NGS-0024).

Scores proposed decisions: 10 attributes → DQS → Decision Guardian.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ATTRIBUTE_KEYS = (
    "evidence",
    "policy",
    "context",
    "memory",
    "risk",
    "alignment",
    "capability",
    "compliance",
    "confidence",
    "explanation",
)

# Equal weight v0; later: pack-specific weights
WEIGHTS: dict[str, float] = {k: 1.0 for k in ATTRIBUTE_KEYS}

CONSTITUTION_KEYS = (
    "truth",
    "logic",
    "alignment",
    "safety",
    "authority",
    "accountability",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clamp(n: float) -> int:
    return int(max(0, min(100, round(n))))


class ADQAEngine:
    """Compute Decision Quality Score from a DecisionResult (+ optional extras)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def score(
        self,
        decision_result: dict[str, Any],
        *,
        evidence_present: list[str] | None = None,
        agent_id: str | None = None,
        capability: str | None = None,
    ) -> dict[str, Any]:
        evidence_present = evidence_present or []
        decision = str(decision_result.get("decision") or "ask").lower()
        reasons = list(decision_result.get("reasons") or [])
        risk_score = float(decision_result.get("riskScore") or 0.5)
        risk_band = str(decision_result.get("riskBand") or "medium")
        required_approvals = list(decision_result.get("requiredApprovals") or [])
        evidence_meta = list(decision_result.get("evidence") or [])
        ctx = decision_result.get("context") or {}
        kg = ctx.get("knowledge") or {}
        mem = ctx.get("memory") or {}
        recommendation = str(decision_result.get("recommendation") or "")

        must_prove = [
            e.replace("mustProve: ", "") for e in evidence_meta if str(e).startswith("mustProve:")
        ]
        missing = [e for e in must_prove if e not in evidence_present]
        if not must_prove and "missing evidence" in " ".join(reasons).lower():
            # parse soft
            missing = ["unspecified"]

        # --- attribute scores ---
        if must_prove:
            ev = 100.0 * (1.0 - len(missing) / max(1, len(must_prove)))
        elif evidence_present:
            ev = 90.0
        else:
            ev = 55.0

        # Policy: strong if package matched cleanly
        policy = 100.0
        if decision == "deny":
            policy = 40.0
        elif any("no matching rule" in r for r in reasons):
            policy = 70.0
        elif decision in {"ask", "require"}:
            policy = 85.0

        ents = kg.get("entities") or []
        context_score = 88.0 if ents else (72.0 if ctx else 50.0)
        if ents:
            context_score = min(100.0, 70.0 + 5.0 * min(6, len(ents)))

        slices = mem.get("slices") or []
        dmem = ctx.get("decisionMemory") or {}
        lessons = list(dmem.get("lessons") or [])
        prior = dmem.get("prior") or {}
        cmem = ctx.get("cmem") or {}
        cmem_hits = int(cmem.get("count") or mem.get("cmemHits") or 0)
        memory_score = 60.0
        if slices:
            memory_score = 85.0
        if cmem_hits:
            memory_score = min(100.0, max(memory_score, 78.0) + 4.0 * min(4, cmem_hits))
        if lessons:
            memory_score = min(100.0, memory_score + 8.0 * min(3, len(lessons)))
        # Successful past outcomes boost memory quality for this action
        if prior.get("avgSuccess") is not None:
            memory_score = min(100.0, memory_score + 10.0 * float(prior["avgSuccess"]))

        # Risk: invert risk_score (low risk → high quality)
        risk_attr = _clamp(100.0 * (1.0 - risk_score))
        if risk_band == "critical":
            risk_attr = min(risk_attr, 25)
        elif risk_band == "high":
            risk_attr = min(risk_attr, 45)

        alignment = 94.0
        if decision == "deny":
            alignment = 50.0
        elif decision == "ask":
            alignment = 80.0

        # Capability check only when an agent identity is in scope
        cap_score = 100.0
        if agent_id:
            try:
                from .capability_gov import CapabilityGovernor

                cap = capability or str(decision_result.get("action") or "content")
                coarse = "contract" if "contract" in cap or "sign" in cap else "content"
                if "payment" in cap or "trade" in cap:
                    coarse = "payment"
                cr = CapabilityGovernor(self.workspace).evaluate(
                    capability=coarse, agent_id=agent_id, profile="guardian"
                )
                mode = str(cr.get("decision") or "allow")
                if mode == "deny":
                    cap_score = 20.0
                elif mode in {"ask", "restricted", "multisig"}:
                    cap_score = 65.0
                elif mode == "sandbox":
                    cap_score = 75.0
            except Exception:
                cap_score = 80.0
        elif capability:
            # action-level hint without agent → soft score, not a hard authority fail
            cap_score = 85.0
        compliance = 90.0
        if decision_result.get("provider"):
            compliance = 95.0
        if decision == "deny":
            compliance = 55.0

        # Confidence: higher when evidence complete + low risk + clear decision
        confidence = 78.0
        if not missing and decision == "allow" and risk_score < 0.4:
            confidence = 92.0
        elif decision == "ask" or missing:
            confidence = 62.0
        elif decision == "deny":
            confidence = 70.0

        explanation = 50.0
        if reasons:
            explanation = min(100.0, 55.0 + 8.0 * min(5, len(reasons)))
        if recommendation:
            explanation = min(100.0, explanation + 15.0)

        attrs = {
            "evidence": _clamp(ev),
            "policy": _clamp(policy),
            "context": _clamp(context_score),
            "memory": _clamp(memory_score),
            "risk": _clamp(risk_attr),
            "alignment": _clamp(alignment),
            "capability": _clamp(cap_score),
            "compliance": _clamp(compliance),
            "confidence": _clamp(confidence),
            "explanation": _clamp(explanation),
        }

        total_w = sum(WEIGHTS.values())
        dqs = _clamp(sum(attrs[k] * WEIGHTS[k] for k in ATTRIBUTE_KEYS) / total_w)

        constitution = self._constitution(
            decision_result,
            attrs=attrs,
            missing=missing,
            agent_id=agent_id,
        )
        hard_fail = any(v == "fail" for v in constitution.values())

        guardian = self._guardian(
            dqs=dqs,
            decision=decision,
            hard_fail=hard_fail,
            required_approvals=required_approvals,
            risk_band=risk_band,
        )
        # Outcome Learning prior can tighten or soften guardian
        hint = str(prior.get("hint") or "")
        if hint == "escalate" and guardian == "approve":
            guardian = "escalate"
        elif hint == "favor_approve" and guardian == "revise" and dqs >= 70:
            guardian = "approve"

        return {
            "ok": True,
            "dqs": dqs,
            "attributes": attrs,
            "guardian": guardian,
            "constitution": constitution,
            "decision": decision,
            "action": decision_result.get("action"),
            "provider": decision_result.get("provider"),
            "lessonsUsed": lessons[:5],
            "learningPrior": prior or None,
            "scoredAt": _now(),
            "standard": "NGS-0024",
            "tagline": "The Trust Layer for AI Decisions.",
        }

    def _constitution(
        self,
        result: dict[str, Any],
        *,
        attrs: dict[str, int],
        missing: list[str],
        agent_id: str | None,
    ) -> dict[str, str]:
        decision = str(result.get("decision") or "")
        out: dict[str, str] = {}
        out["truth"] = "fail" if missing and decision == "allow" else ("warn" if missing else "pass")
        out["logic"] = "pass" if attrs["explanation"] >= 50 else "warn"
        out["alignment"] = "fail" if attrs["alignment"] < 40 else ("warn" if attrs["alignment"] < 70 else "pass")
        # Safety: high risk or deny without clear reasons
        risk = float(result.get("riskScore") or 0)
        out["safety"] = "fail" if risk >= 0.95 and decision == "allow" else ("warn" if risk >= 0.8 else "pass")
        out["authority"] = "fail" if attrs["capability"] < 30 else ("warn" if attrs["capability"] < 70 else "pass")
        out["accountability"] = (
            "pass"
            if result.get("auditRef") or result.get("packageId")
            else "warn"
        )
        if agent_id:
            out["accountability"] = "pass"
        return out

    def _guardian(
        self,
        *,
        dqs: int,
        decision: str,
        hard_fail: bool,
        required_approvals: list[str],
        risk_band: str,
    ) -> str:
        if hard_fail or decision == "deny" or dqs < 60:
            return "reject"
        if decision in {"ask", "require"} or required_approvals or risk_band in {"high", "critical"}:
            return "escalate"
        if dqs < 80:
            return "revise"
        return "approve"

    def check_proposed(
        self,
        *,
        action: str,
        provider: str | None = None,
        evidence_present: list[str] | None = None,
        context: dict[str, Any] | None = None,
        agent_id: str | None = None,
        question: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        """Run DecisionEngine then ADQA score; optionally persist Decision Memory."""
        from .decision import DecisionEngine
        from .outcome_learning import OutcomeLearningEngine

        context = dict(context or {})
        # Enrich with Decision Memory lessons + learning priors
        try:
            enrich = OutcomeLearningEngine(self.workspace).enrich_adqa_context(action)
            context.update(enrich)
        except Exception:
            pass
        # CMEM continuity feedstock (optional URL / local bridge)
        try:
            from .cmem_bridge import CmemBridge

            context = CmemBridge(self.workspace).enrich_context(action, context)
        except Exception:
            pass
        # DQS Network peer priors (opt-in multi-org)
        try:
            from .dqs_network import DqsNetwork

            net = DqsNetwork(self.workspace).enrich_adqa_context(action)
            if net.get("decisionMemory"):
                dmem = dict(context.get("decisionMemory") or {})
                lessons = list(dmem.get("lessons") or [])
                lessons.extend(net["decisionMemory"].get("lessons") or [])
                dmem["lessons"] = lessons
                dmem["networkPrior"] = net["decisionMemory"].get("networkPrior")
                context["decisionMemory"] = dmem
        except Exception:
            pass

        result = DecisionEngine(self.workspace).evaluate(
            action=action,
            provider=provider,
            evidence_present=evidence_present,
            context=context,
            question=question,
        )
        # Ensure decisionMemory visible to scorer
        ctx = result.setdefault("context", {})
        if isinstance(ctx, dict) and context.get("decisionMemory"):
            ctx["decisionMemory"] = context["decisionMemory"]

        adqa = self.score(
            result,
            evidence_present=evidence_present,
            agent_id=agent_id,
            capability=action,
        )
        out: dict[str, Any] = {
            "decisionResult": result,
            "adqa": adqa,
            "standard": "NGS-0024",
        }
        if persist:
            try:
                from .decision_memory import DecisionMemory

                mem = DecisionMemory(self.workspace).record(
                    action=action,
                    context={k: v for k, v in context.items() if not str(k).startswith("_")},
                    reasoning=list(result.get("reasons") or [])[:5],
                    provider=provider or result.get("provider"),
                    decision=result.get("decision"),
                    adqa=adqa,
                    confidence=adqa.get("attributes", {}).get("confidence", 0) / 100.0,
                )
                out["decisionMemoryId"] = mem["decisionId"]
                adqa["decisionMemoryId"] = mem["decisionId"]
            except Exception as e:
                out["decisionMemoryError"] = str(e)
        return out
