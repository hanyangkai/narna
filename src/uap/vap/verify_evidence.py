from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ..hashing import sha256_hex
from .price_extract import extract_price


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verify_hash_match(evidence: dict[str, Any], content: bytes) -> dict[str, Any]:
    expected = evidence.get("contentHash", "")
    actual = "sha256:" + sha256_hex(content)
    status = "valid" if expected == actual else "invalid"
    return {
        "evidenceId": evidence["evidenceId"],
        "verifierId": "hash_match",
        "status": status,
        "checkedAt": _now_rfc3339(),
        "details": {"expected": expected, "actual": actual},
        "scoreContribution": 1.0 if status == "valid" else 0.0,
    }


def verify_freshness(evidence: dict[str, Any], *, max_age_seconds: int = 300) -> dict[str, Any]:
    captured = evidence.get("capturedAt")
    if not captured:
        return {
            "evidenceId": evidence["evidenceId"],
            "verifierId": "freshness",
            "status": "invalid",
            "checkedAt": _now_rfc3339(),
            "details": {"reason": "missing capturedAt"},
            "scoreContribution": 0.0,
        }
    captured_dt = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - captured_dt).total_seconds()
    status = "valid" if age <= max_age_seconds else "expired"
    return {
        "evidenceId": evidence["evidenceId"],
        "verifierId": "freshness",
        "status": status,
        "checkedAt": _now_rfc3339(),
        "details": {"ageSeconds": age, "maxAgeSeconds": max_age_seconds},
        "scoreContribution": 1.0 if status == "valid" else 0.0,
    }


def verify_receipt_presence(evidence: dict[str, Any]) -> dict[str, Any]:
    status = "valid" if evidence.get("type") == "receipt" else "invalid"
    return {
        "evidenceId": evidence["evidenceId"],
        "verifierId": "receipt_presence",
        "status": status,
        "checkedAt": _now_rfc3339(),
        "details": {"type": evidence.get("type")},
        "scoreContribution": 1.0 if status == "valid" else 0.0,
    }


def verify_multi_source_agreement(
    evidences: list[dict[str, Any]],
    *,
    evidence_blobs: dict[str, bytes],
    tolerance_pct: float = 0.5,
) -> dict[str, Any]:
    prices: list[float] = []
    for ev in evidences:
        if ev.get("type") != "api_response":
            continue
        blob = evidence_blobs.get(ev["evidenceId"], b"")
        price = extract_price(ev, blob)
        if price is not None:
            prices.append(price)
    if len(prices) < 2:
        return {
            "evidenceId": evidences[0]["evidenceId"] if evidences else "none",
            "verifierId": "multi_source_agreement",
            "status": "skipped",
            "checkedAt": _now_rfc3339(),
            "details": {"reason": "insufficient sources"},
            "scoreContribution": 0.5,
        }
    lo, hi = min(prices), max(prices)
    diff_pct = ((hi - lo) / lo) * 100 if lo else 100.0
    status = "valid" if diff_pct <= tolerance_pct else "invalid"
    return {
        "evidenceId": "multi_source",
        "verifierId": "multi_source_agreement",
        "status": status,
        "checkedAt": _now_rfc3339(),
        "details": {"diffPct": diff_pct, "tolerancePct": tolerance_pct, "prices": prices},
        "scoreContribution": 1.0 if status == "valid" else 0.0,
    }


def verify_all(
    evidences: list[dict[str, Any]],
    *,
    evidence_blobs: dict[str, bytes],
    max_age_seconds: int = 300,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    api_evidences: list[dict[str, Any]] = []
    for ev in evidences:
        blob = evidence_blobs.get(ev["evidenceId"], b"")
        results.append(verify_hash_match(ev, blob))
        results.append(verify_freshness(ev, max_age_seconds=max_age_seconds))
        if ev.get("type") == "receipt":
            results.append(verify_receipt_presence(ev))
        if ev.get("type") == "api_response":
            api_evidences.append(ev)
    if len(api_evidences) >= 2:
        results.append(
            verify_multi_source_agreement(api_evidences, evidence_blobs=evidence_blobs)
        )
    return results
