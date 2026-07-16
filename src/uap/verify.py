from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import url2pathname

from .events import hash_event
from .hashing import ZERO_HASH, sha256_obj
from .schemas import validator_for
from .vap.verify_evidence import verify_all


def _load_evidence_blobs(bundle: dict[str, Any]) -> dict[str, bytes]:
    """Load evidence bytes from contentUri when accessible (file://)."""
    blobs: dict[str, bytes] = {}
    for ev in bundle.get("evidence", []):
        uri = ev.get("contentUri", "")
        if uri.startswith("file:"):
            path = Path(url2pathname(urlparse(uri).path))
            if path.exists():
                blobs[ev["evidenceId"]] = path.read_bytes()
    return blobs


def verify_proof_bundle(
    bundle: dict[str, Any],
    *,
    hard: bool = True,
) -> tuple[bool, list[str]]:
    problems: list[str] = []

    v = validator_for("proof-bundle.schema.json")
    errors = sorted(v.iter_errors(bundle), key=lambda e: e.path)
    for e in errors[:50]:
        loc = "/".join(str(x) for x in e.path) or "<root>"
        problems.append(f"schema {loc}: {e.message}")
    if errors:
        return False, problems

    expected_bundle_hash = bundle.get("bundleHash")
    recomputed = sha256_obj({k: v for k, v in bundle.items() if k != "bundleHash"})
    if expected_bundle_hash != recomputed:
        problems.append("bundleHash mismatch")

    events = bundle["events"]
    prev = ZERO_HASH
    last_hash = None
    for i, evt in enumerate(events):
        if evt.get("hashPrev") != prev:
            problems.append(f"event[{i}].hashPrev mismatch")
        h = hash_event(evt)
        prev = h
        last_hash = h
    if last_hash != bundle.get("tipHash"):
        problems.append("tipHash mismatch")

    if hard:
        evidence = bundle.get("evidence", [])
        blobs = _load_evidence_blobs(bundle)
        if evidence and blobs:
            recomputed_verifications = verify_all(evidence, evidence_blobs=blobs)
            embedded = bundle.get("verifications", [])
            if embedded:
                invalid = [v for v in recomputed_verifications if v.get("status") == "invalid"]
                if invalid:
                    problems.append(f"evidence verification invalid: {len(invalid)}")
            else:
                problems.append("proof bundle missing verifications for evidence")

    return len(problems) == 0, problems
