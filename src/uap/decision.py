"""Decision Engine — Decision OS evaluate path (NGS-0014).

Produces DecisionResult: decision + riskScore + reasons + approvals + evidence + auditRef.
Does not execute host side-effects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .governance_runtime import (
    ConstitutionRuntime,
    extract_rules,
    load_package_file,
    match_rule,
    package_hash,
    resolve_provider_package,
)
from .hashing import sha256_obj

RISK_BAND_SCORE = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 0.92,
}

EFFECT_RANK = {"allow": 0, "require": 1, "ask": 2, "deny": 3}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def risk_band_from_score(score: float) -> str:
    if score >= 0.9:
        return "critical"
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def score_from_band(band: str | None) -> float:
    return RISK_BAND_SCORE.get(str(band or "medium").lower(), 0.5)


class DecisionEngine:
    """Evaluate an action/question against a Decision Package (+ composed packs)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.gov = ConstitutionRuntime(self.workspace)

    def load(
        self,
        *,
        path: str | Path | None = None,
        provider: str | None = None,
        version: str | None = None,
    ) -> dict[str, Any]:
        """Load Decision Package and set active governance binding."""
        return self.gov.load(path=path, provider=provider, version=version)

    def _resolve_decision_doc(
        self,
        *,
        path: str | Path | None = None,
        provider: str | None = None,
        version: str | None = None,
        document: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if document is not None:
            meta = document.get("metadata") or {}
            binding = {
                "packageId": meta.get("id"),
                "provider": meta.get("provider") or provider,
                "version": meta.get("version") or version,
                "packageHash": package_hash(document),
                "packageKind": document.get("kind"),
            }
            return document, binding

        if path or provider:
            result = self.gov.load(path=path, provider=provider, version=version)
            doc = result["document"]
            binding = result["binding"]
            return doc, binding

        doc = self.gov.active_document()
        binding = self.gov.active() or {}
        if doc is None:
            # default seed
            resolved = resolve_provider_package(
                "legal-decision", None, workspace=self.workspace
            )
            doc = load_package_file(resolved)
            meta = doc.get("metadata") or {}
            binding = {
                "packageId": meta.get("id"),
                "provider": meta.get("provider"),
                "version": meta.get("version"),
                "packageHash": package_hash(doc),
                "path": str(resolved),
                "packageKind": doc.get("kind"),
            }
        return doc, binding

    def _composed_rules(self, doc: dict[str, Any]) -> list[dict[str, Any]]:
        rules = list(extract_rules(doc))
        composes = (doc.get("spec") or {}).get("composes") or []
        for item in composes:
            if not isinstance(item, dict):
                continue
            provider = item.get("provider")
            if not provider:
                continue
            try:
                path = resolve_provider_package(
                    str(provider),
                    item.get("version"),
                    workspace=self.workspace,
                )
                composed = load_package_file(path)
                rules.extend(extract_rules(composed))
            except Exception:
                continue
        return rules

    def _merge_decision(
        self,
        *,
        local_effect: str | None,
        composed_effect: str | None,
    ) -> str:
        a = EFFECT_RANK.get(str(local_effect or "allow").lower(), 0)
        b = EFFECT_RANK.get(str(composed_effect or "allow").lower(), 0)
        winner = max(a, b)
        for name, rank in EFFECT_RANK.items():
            if rank == winner:
                return name
        return "deny"

    def evaluate(
        self,
        *,
        action: str,
        question: str | None = None,
        path: str | Path | None = None,
        provider: str | None = None,
        version: str | None = None,
        document: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        session_id: str | None = None,
        evidence_present: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return a DecisionResult. Never executes host side-effects."""
        action = str(action or "").strip()
        if not action:
            raise ValueError("action is required")

        context = dict(context or {})
        # Enrich from Knowledge + Durable Memory (Decision OS Context Engine)
        try:
            from .durable_memory import DurableMemory
            from .knowledge import KnowledgeGraph

            kg_ctx = KnowledgeGraph(self.workspace).context_for(context)
            mem_ctx = DurableMemory(self.workspace).context_for(context)
            context["_knowledge"] = kg_ctx
            context["_memory"] = mem_ctx
            if kg_ctx.get("entities"):
                # surface entity risk flags into soft reasons later
                context.setdefault("_entityNames", [e.get("name") for e in kg_ctx["entities"]])
        except Exception:
            pass
        # CMEM feedstock (continuity memory) — never replaces Decision Memory
        try:
            from .cmem_bridge import CmemBridge

            context = CmemBridge(self.workspace).enrich_context(action, context)
        except Exception:
            pass

        doc, binding = self._resolve_decision_doc(
            path=path, provider=provider, version=version, document=document
        )
        if doc.get("kind") not in {"DecisionPackage", "GovernancePackage", "Constitution"}:
            raise ValueError("active document is not a DecisionPackage or GovernancePackage")

        spec = doc.get("spec") or {}
        decision_cfg = spec.get("decision") if isinstance(spec.get("decision"), dict) else {}
        if not decision_cfg and doc.get("kind") != "DecisionPackage":
            decision_cfg = {
                "actions": [action],
                "requireRiskScore": True,
                "requireReasons": True,
                "requireEvidence": True,
                "requireApprovals": True,
            }

        require_risk = bool(decision_cfg.get("requireRiskScore", True))
        require_reasons = bool(decision_cfg.get("requireReasons", True))
        require_evidence = bool(decision_cfg.get("requireEvidence", True))
        require_approvals = bool(decision_cfg.get("requireApprovals", True))
        hints = decision_cfg.get("recommendationHints") or {}

        local_rules = extract_rules(doc)
        all_rules = self._composed_rules(doc)

        must_prove = list(((spec.get("evidence") or {}).get("mustProve")) or [])
        evidence_present = evidence_present or []
        missing = [e for e in must_prove if e not in evidence_present]

        def _applicable(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
            out: list[dict[str, Any]] = []
            for r in rules:
                when = str(r.get("when") or "")
                if when == "evidence.missing" and not missing:
                    continue
                if when == "evidence.missing" and missing:
                    out.append(r)
                    continue
                out.append(r)
            return out

        local_match = match_rule(_applicable(local_rules), action)
        composed_only = [r for r in all_rules if r not in local_rules]
        composed_match = match_rule(_applicable(composed_only), action)

        local_effect = (local_match or {}).get("effect")
        composed_effect = (composed_match or {}).get("effect")
        if local_match is None and composed_match is None:
            if action.endswith(".sign") or "consequential" in action:
                decision = "ask"
            else:
                decision = "allow"
        else:
            decision = self._merge_decision(
                local_effect=str(local_effect) if local_effect else None,
                composed_effect=str(composed_effect) if composed_effect else None,
            )

        reasons: list[str] = []
        if local_match:
            reasons.append(
                f"decision rule {local_match.get('id')}: {local_match.get('effect')}"
                + (f" — {local_match.get('description')}" if local_match.get("description") else "")
            )
        if composed_match and composed_match is not local_match:
            reasons.append(
                f"composed rule {composed_match.get('id')}: {composed_match.get('effect')}"
                + (
                    f" — {composed_match.get('description')}"
                    if composed_match.get("description")
                    else ""
                )
            )
        if missing and require_evidence:
            reasons.append(f"missing evidence: {', '.join(missing)}")
        for c in (spec.get("constraints") or [])[:3]:
            if isinstance(c, str):
                reasons.append(f"constraint: {c}")
        if not reasons and require_reasons:
            reasons.append("no matching rule — default decision policy applied")

        # Context Engine signals
        ents = (context.get("_knowledge") or {}).get("entities") or []
        if ents:
            reasons.append(f"knowledge context: {len(ents)} related entities")
        mem_slices = (context.get("_memory") or {}).get("slices") or []
        if mem_slices:
            reasons.append(f"memory context: {len(mem_slices)} durable scopes")

        # Risk score
        base = score_from_band(spec.get("riskLevel"))
        weights: list[float] = []
        for m in (local_match, composed_match):
            if not m:
                continue
            if m.get("riskWeight") is not None:
                try:
                    weights.append(float(m["riskWeight"]))
                except (TypeError, ValueError):
                    pass
            elif str(m.get("effect")) == "deny":
                weights.append(0.95)
            elif str(m.get("effect")) in {"ask", "require"}:
                weights.append(0.8)
        risk_score = max([base, *weights]) if weights else base
        if decision == "deny":
            risk_score = max(risk_score, 0.9)
        elif decision in {"ask", "require"}:
            risk_score = max(risk_score, 0.7)
        risk_score = round(min(1.0, max(0.0, float(risk_score))), 4)
        risk_band = risk_band_from_score(risk_score)

        # Approvals
        hr = spec.get("humanReview") or {}
        required_for = list(hr.get("requiredFor") or [])
        roles = list(hr.get("roles") or [])
        required_approvals: list[str] = []
        if decision in {"ask", "require"} or action in required_for:
            if roles:
                required_approvals.extend(str(r) for r in roles)
            else:
                required_approvals.append("human.review")
            for item in required_for:
                if item == action or action.startswith(str(item)):
                    if str(item) not in required_approvals:
                        required_approvals.append(str(item))

        evidence_out: list[str] = []
        if require_evidence:
            evidence_out.extend(f"mustProve: {e}" for e in must_prove)
            for e in ((spec.get("evidence") or {}).get("mustLog") or []):
                evidence_out.append(f"mustLog: {e}")

        recommendation = None
        if isinstance(hints, dict) and hints.get(decision):
            recommendation = str(hints[decision])
        elif decision == "deny":
            recommendation = "Do not proceed — governance denied this action."
        elif decision == "ask":
            recommendation = "Hold for human approval before irreversible side effects."
        elif decision == "require":
            recommendation = "Provide required evidence / oversight, then re-evaluate."
        else:
            recommendation = "Proceed under active Decision Package constraints."

        if question and decision == "ask":
            recommendation = f"{recommendation} Question: {question}"

        result: dict[str, Any] = {
            "decision": decision,
            "recommendation": recommendation,
            "action": action,
            "question": question,
            "packageId": binding.get("packageId"),
            "provider": binding.get("provider"),
            "version": binding.get("version"),
            "evaluatedAt": _now(),
            "auditRef": {
                "packageId": binding.get("packageId"),
                "packageHash": binding.get("packageHash"),
                "sessionId": session_id,
                "contextHash": sha256_obj(context or {}),
                "standard": "NGS-0014",
            },
            "ok": True,
        }
        if require_risk:
            result["riskScore"] = risk_score
            result["riskBand"] = risk_band
        if require_reasons:
            result["reasons"] = reasons
        if require_approvals or required_approvals:
            result["requiredApprovals"] = required_approvals
        if require_evidence:
            result["evidence"] = evidence_out
        result["context"] = {
            "knowledge": context.get("_knowledge"),
            "memory": context.get("_memory"),
            "cmem": context.get("_cmem"),
            "decisionMemory": context.get("decisionMemory"),
        }
        # ADQA — Decision Quality Score (NGS-0024)
        try:
            from .adqa import ADQAEngine

            result["adqa"] = ADQAEngine(self.workspace).score(
                result,
                evidence_present=evidence_present,
                capability=action,
            )
        except Exception as e:
            result["adqa"] = {"ok": False, "error": str(e), "standard": "NGS-0024"}
        return result
