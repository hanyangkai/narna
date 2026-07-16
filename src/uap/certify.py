"""Phase 4 — Certification suite (Verified by NARNA).

Offline by default. Runs deterministic checks against identity, runs,
VAP proof bundles, and passport. Passing agents receive the badge.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .hashing import sha256_obj
from .ids import new_id
from .verify import verify_proof_bundle

BADGE = "Verified by NARNA"
CERT_ALGORITHM = "narna-cert-v0"
DEFAULT_MIN_TRUST = 0.7


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class CheckResult:
    id: str
    name: str
    passed: bool
    detail: str = ""


@dataclass
class CertificationResult:
    certificationId: str
    agentId: str
    status: str  # passed | failed
    badge: str | None
    algorithm: str
    issuedAt: str
    expiresAt: str | None
    trustScore: float | None
    checks: list[CheckResult] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    runId: str | None = None
    proofHash: str | None = None
    passportHash: str | None = None
    localPath: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verified"] = self.status == "passed"
        return d


def _check(cid: str, name: str, passed: bool, detail: str = "") -> CheckResult:
    return CheckResult(id=cid, name=name, passed=passed, detail=detail)


def run_certification(
    *,
    agent_id: str,
    workspace: Path,
    identity: dict[str, Any] | None,
    runs: list[str],
    load_events: Callable[[str], list[dict[str, Any]]],
    passport: dict[str, Any] | None,
    min_trust: float = DEFAULT_MIN_TRUST,
    ttl_days: int = 90,
) -> CertificationResult:
    """Run the NARNA certification suite (offline)."""
    checks: list[CheckResult] = []
    trust_score: float | None = None
    run_id: str | None = None
    proof_hash: str | None = None
    passport_hash: str | None = None

    # 1. Identity
    has_id = bool(identity and identity.get("agentId"))
    checks.append(
        _check(
            "identity",
            "Identity issued",
            has_id,
            f"agentId={identity.get('agentId')}" if has_id else "missing identity",
        )
    )

    # 2. At least one completed run
    completed_runs: list[str] = []
    failed_runs: list[str] = []
    for rid in runs:
        events = load_events(rid)
        types = {e.get("eventType") for e in events}
        if "Completed" in types:
            completed_runs.append(rid)
        if "Failed" in types and "Completed" not in types:
            failed_runs.append(rid)
    checks.append(
        _check(
            "completed_run",
            "At least one Completed run",
            bool(completed_runs),
            f"completed={len(completed_runs)} failed={len(failed_runs)}",
        )
    )

    # 3. Proof bundle + VAP
    bundle: dict[str, Any] | None = None
    for rid in reversed(completed_runs or runs):
        path = workspace / ".uap" / "runs" / rid / "proof-bundle.json"
        if path.exists():
            bundle = json.loads(path.read_text(encoding="utf-8"))
            run_id = rid
            break
    has_proof = bundle is not None
    checks.append(
        _check(
            "proof_bundle",
            "ProofBundle present (VAP)",
            has_proof,
            f"runId={run_id}" if has_proof else "enable_vap() then run()",
        )
    )

    # 4. Proof verifies
    proof_ok = False
    proof_detail = "no bundle"
    if bundle is not None:
        proof_ok, problems = verify_proof_bundle(bundle, hard=False)
        proof_detail = "ok" if proof_ok else "; ".join(problems[:5])
        proof_hash = bundle.get("bundleHash")
        ts = bundle.get("trustScore") or {}
        if isinstance(ts, dict) and ts.get("score") is not None:
            trust_score = float(ts["score"])
        elif isinstance(ts, (int, float)):
            trust_score = float(ts)
    checks.append(_check("proof_verify", "ProofBundle verifies", proof_ok, proof_detail))

    # 5. Trust threshold
    trust_ok = trust_score is not None and trust_score >= min_trust
    checks.append(
        _check(
            "trust_threshold",
            f"Trust score ≥ {min_trust}",
            trust_ok,
            f"score={trust_score}" if trust_score is not None else "no trust score",
        )
    )

    # 6. Passport
    has_passport = bool(passport and passport.get("passportId"))
    if has_passport and passport:
        passport_hash = sha256_obj(passport)
    checks.append(
        _check(
            "passport",
            "Passport issued",
            has_passport,
            f"passportId={passport.get('passportId')}" if has_passport and passport else "missing",
        )
    )

    # 7. Success rate (no hard fail if only one run)
    total = len(completed_runs) + len(failed_runs)
    success_rate = (len(completed_runs) / total) if total else 0.0
    success_ok = total == 0 or success_rate >= 0.5
    checks.append(
        _check(
            "success_rate",
            "Success rate ≥ 50%",
            success_ok,
            f"rate={success_rate:.2f} (n={total})",
        )
    )

    failures = [c.name for c in checks if not c.passed]
    passed = len(failures) == 0
    issued = _now()
    expires = None
    if passed and ttl_days > 0:
        from datetime import timedelta

        expires = (
            datetime.now(timezone.utc) + timedelta(days=ttl_days)
        ).isoformat().replace("+00:00", "Z")

    result = CertificationResult(
        certificationId=new_id("cert"),
        agentId=agent_id,
        status="passed" if passed else "failed",
        badge=BADGE if passed else None,
        algorithm=CERT_ALGORITHM,
        issuedAt=issued,
        expiresAt=expires,
        trustScore=trust_score,
        checks=checks,
        failures=failures,
        runId=run_id,
        proofHash=proof_hash,
        passportHash=passport_hash,
    )
    return result


def save_certificate(workspace: Path, result: CertificationResult) -> Path:
    root = workspace / ".uap" / "certification"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{result.agentId}.json"
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    # also append history
    hist = root / "history.jsonl"
    with hist.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")
    result.localPath = str(path)
    # rewrite with localPath
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return path


def load_certificate(workspace: Path, agent_id: str) -> dict[str, Any] | None:
    path = workspace / ".uap" / "certification" / f"{agent_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
