from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canon import canonical_json_bytes
from .hashing import sha256_obj
from .ids import new_id


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_proof_bundle(
    *,
    agent_id: str,
    run_id: str,
    events: list[dict[str, Any]],
    evidence: list[dict[str, Any]] | None = None,
    verifications: list[dict[str, Any]] | None = None,
    audit: dict[str, Any] | None = None,
    trust_score: dict[str, Any] | None = None,
    vap_version: str = "0.1.0",
) -> dict[str, Any]:
    if not events:
        raise ValueError("ProofBundle requires at least 1 event")
    tip_hash = str(events[-1].get("eventHash") or "")
    if not tip_hash.startswith("sha256:") or len(tip_hash) != len("sha256:") + 64:
        raise ValueError("Last event must include valid eventHash")

    bundle: dict[str, Any] = {
        "bundleId": new_id("bundle"),
        "agentId": agent_id,
        "runId": run_id,
        "createdAt": _now_rfc3339(),
        "events": [{k: v for k, v in e.items() if k != "eventHash"} for e in events],
        "evidence": evidence or [],
        "verifications": verifications or [],
        "tipHash": tip_hash,
        "vapVersion": vap_version,
    }
    if audit is not None:
        bundle["audit"] = audit
    if trust_score is not None:
        bundle["trustScore"] = trust_score

    bundle_hash = sha256_obj(bundle)
    bundle["bundleHash"] = bundle_hash
    return bundle


def write_proof_bundle(path: str | Path, bundle: dict[str, Any]) -> None:
    p = Path(path)
    p.write_bytes(canonical_json_bytes(bundle) + b"\n")

