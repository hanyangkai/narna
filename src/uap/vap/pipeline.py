from __future__ import annotations

from pathlib import Path
from typing import Any

from ..audit import audit_run
from ..proof import build_proof_bundle
from ..trust import compute_trust_score_v0
from .verify_evidence import verify_all


def run_vap_pipeline(
    *,
    agent_id: str,
    run_id: str,
    events: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    evidence_blobs: dict[str, bytes],
    policy_decisions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    verifications = verify_all(evidence, evidence_blobs=evidence_blobs)
    audit = audit_run(
        agent_id=agent_id,
        run_id=run_id,
        events=events,
        verifications=verifications,
        policy_decisions=policy_decisions,
        evidence=evidence,
    )
    trust = compute_trust_score_v0(
        agent_id=agent_id,
        run_id=run_id,
        events=events,
        verifications=verifications,
        policy_decisions=policy_decisions,
        evidence=evidence,
    )
    bundle = build_proof_bundle(
        agent_id=agent_id,
        run_id=run_id,
        events=events,
        evidence=evidence,
        verifications=verifications,
        audit=audit,
        trust_score=trust,
    )
    return {
        "verifications": verifications,
        "audit": audit,
        "trustScore": trust,
        "proofBundle": bundle,
    }
