"""NARNA Certification (C3) — L1 / L2 / Enterprise Ready.

Spec: specs/certification/SPEC.md
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .hashing import sha256_obj
from .ids import new_id
from .verify import verify_proof_bundle

CERT_ALGORITHM = "narna-cert-v1"
DEFAULT_MIN_TRUST = 0.7

LEVELS = ("L1", "L2", "L3")
LEVEL_RANK = {"none": 0, "L1": 1, "L2": 2, "L3": 3}

BADGES = {
    "L1": "NARNA Certified",
    "L2": "NARNA Certified+",
    "L3": "Enterprise Ready",
}

LEVEL_LABELS = {
    "L1": "Level 1",
    "L2": "Level 2",
    "L3": "Enterprise Ready",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class CheckResult:
    id: str
    name: str
    passed: bool
    level: str = "L1"
    detail: str = ""


@dataclass
class CertificationResult:
    certificationId: str
    agentId: str
    status: str  # passed | failed (vs target)
    level: str  # highest achieved
    targetLevel: str
    badge: str | None
    levelLabel: str | None
    algorithm: str
    issuedAt: str
    expiresAt: str | None
    trustScore: float | None
    checks: list[CheckResult] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    runId: str | None = None
    proofHash: str | None = None
    passportHash: str | None = None
    constitutionId: str | None = None
    constitutionHash: str | None = None
    localPath: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["verified"] = self.level in LEVELS
        d["entityId"] = self.agentId
        return d


def _check(cid: str, name: str, passed: bool, level: str, detail: str = "") -> CheckResult:
    return CheckResult(id=cid, name=name, passed=passed, level=level, detail=detail)


def _normalize_level(level: str | None) -> str:
    if not level:
        return "L2"
    raw = str(level).strip().upper()
    aliases = {
        "1": "L1",
        "LEVEL1": "L1",
        "LEVEL 1": "L1",
        "2": "L2",
        "LEVEL2": "L2",
        "LEVEL 2": "L2",
        "3": "L3",
        "LEVEL3": "L3",
        "LEVEL 3": "L3",
        "ENTERPRISE": "L3",
        "ENTERPRISE READY": "L3",
        "ENTERPRISE_READY": "L3",
    }
    raw = aliases.get(raw, raw)
    if raw not in LEVELS:
        raise ValueError(f"unknown certification level: {level}")
    return raw


def _level_passed(checks: list[CheckResult], level: str) -> bool:
    needed = [c for c in checks if LEVEL_RANK[c.level] <= LEVEL_RANK[level]]
    return bool(needed) and all(c.passed for c in needed)


def _highest_level(checks: list[CheckResult]) -> str:
    for lvl in reversed(LEVELS):
        if _level_passed(checks, lvl):
            return lvl
    return "none"


def run_certification(
    *,
    agent_id: str,
    workspace: Path,
    identity: dict[str, Any] | None,
    runs: list[str],
    load_events: Callable[[str], list[dict[str, Any]]],
    passport: dict[str, Any] | None,
    constitution: dict[str, Any] | None = None,
    target_level: str = "L2",
    min_trust: float | None = None,
    ttl_days: int = 90,
) -> CertificationResult:
    """Evaluate L1→L3 and return result vs target_level."""
    target = _normalize_level(target_level)
    checks: list[CheckResult] = []
    trust_score: float | None = None
    run_id: str | None = None
    proof_hash: str | None = None
    passport_hash: str | None = None
    constitution_id: str | None = None
    constitution_hash: str | None = None

    # ── L1 ──────────────────────────────────────────────
    const_ok = False
    const_detail = "missing constitution.yaml"
    if constitution and constitution.get("kind") == "Constitution":
        try:
            from .schemas import validator_for

            validator_for("constitution.schema.json").validate(constitution)
            const_ok = True
            meta = constitution.get("metadata") or {}
            constitution_id = str(meta.get("id") or "")
            constitution_hash = sha256_obj(constitution)
            const_detail = f"id={constitution_id}"
        except Exception as e:
            const_detail = str(e)[:120]
    checks.append(_check("constitution", "Constitution valid", const_ok, "L1", const_detail))

    has_id = bool(
        identity
        and (identity.get("agentId") or identity.get("entityId") or identity.get("identityId"))
    )
    checks.append(
        _check(
            "identity",
            "Identity issued",
            has_id,
            "L1",
            f"id={identity.get('agentId') or identity.get('entityId')}" if has_id and identity else "missing",
        )
    )

    has_passport = bool(passport and passport.get("passportId"))
    if has_passport and passport:
        passport_hash = sha256_obj(passport)
    checks.append(
        _check(
            "passport",
            "Passport issued",
            has_passport,
            "L1",
            f"passportId={passport.get('passportId')}" if has_passport and passport else "missing",
        )
    )

    cite = (passport or {}).get("constitution") if passport else None
    cite_ok = bool(
        isinstance(cite, dict)
        and cite.get("constitutionId")
        and str(cite.get("constitutionHash", "")).startswith("sha256:")
    )
    checks.append(
        _check(
            "constitution_cite",
            "Passport cites Constitution",
            cite_ok,
            "L1",
            f"constitutionId={cite.get('constitutionId')}" if cite_ok and isinstance(cite, dict) else "missing citation",
        )
    )

    # Constitution Compatible — supports: loadable (RFC-0009)
    supports: list[str] = []
    if constitution:
        compat = (constitution.get("spec") or {}).get("compatibility") or {}
        if isinstance(compat, dict):
            supports = list(compat.get("supports") or [])
    support_ok = True
    support_detail = "no supports declared"
    if supports:
        try:
            from .governance_runtime import ConstitutionRuntime

            rt = ConstitutionRuntime(workspace)
            loaded_ids: list[str] = []
            missing: list[str] = []
            for sid in supports:
                # map eu-ai-act-v1 → provider eu-ai-act
                provider = sid.rsplit("-v", 1)[0] if "-v" in sid else sid
                try:
                    rt.load(provider=provider)
                    loaded_ids.append(sid)
                except Exception:
                    missing.append(sid)
            support_ok = len(missing) == 0
            support_detail = (
                f"loaded={loaded_ids}" if support_ok else f"missing={missing}"
            )
        except Exception as e:
            support_ok = False
            support_detail = str(e)[:120]
    checks.append(
        _check(
            "constitution_supports",
            "Constitution Compatible supports loadable",
            support_ok if supports else True,
            "L1" if not supports else ("L3" if supports else "L1"),
            support_detail,
        )
    )

    # ── L2 ──────────────────────────────────────────────
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
            "L2",
            f"completed={len(completed_runs)} failed={len(failed_runs)}",
        )
    )

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
            "L2",
            f"runId={run_id}" if has_proof else "enable_vap() then run()",
        )
    )

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
    checks.append(_check("proof_verify", "ProofBundle verifies", proof_ok, "L2", proof_detail))

    threshold = DEFAULT_MIN_TRUST
    if min_trust is not None:
        threshold = float(min_trust)
    elif constitution:
        try:
            threshold = float(constitution.get("spec", {}).get("trust", {}).get("minScore", threshold))
        except (TypeError, ValueError):
            pass
    trust_ok = trust_score is not None and trust_score >= threshold
    checks.append(
        _check(
            "trust_threshold",
            f"Trust score ≥ {threshold}",
            trust_ok,
            "L2",
            f"score={trust_score}" if trust_score is not None else "no trust score",
        )
    )

    total = len(completed_runs) + len(failed_runs)
    success_rate = (len(completed_runs) / total) if total else 0.0
    success_ok = total == 0 or success_rate >= 0.5
    checks.append(
        _check(
            "success_rate",
            "Success rate ≥ 50%",
            success_ok,
            "L2",
            f"rate={success_rate:.2f} (n={total})",
        )
    )

    # ── L3 ──────────────────────────────────────────────
    gov = (constitution or {}).get("spec", {}).get("governance") or {}
    gov_ok = bool(isinstance(gov, dict) and gov.get("orgId"))
    checks.append(
        _check(
            "governance",
            "Governance orgId present",
            gov_ok,
            "L3",
            f"orgId={gov.get('orgId')}" if gov_ok else "add spec.governance.orgId",
        )
    )

    retention = (constitution or {}).get("spec", {}).get("evidence", {}).get("retentionDays")
    try:
        retention_ok = retention is not None and int(retention) >= 90
    except (TypeError, ValueError):
        retention_ok = False
    checks.append(
        _check(
            "retention",
            "Evidence retention ≥ 90 days",
            retention_ok,
            "L3",
            f"retentionDays={retention}" if retention is not None else "missing",
        )
    )

    hr = (constitution or {}).get("spec", {}).get("humanReview") or {}
    hr_req = hr.get("requiredFor") if isinstance(hr, dict) else None
    hr_ok = bool(isinstance(hr_req, list) and len(hr_req) > 0)
    checks.append(
        _check(
            "human_review",
            "Human review requirements set",
            hr_ok,
            "L3",
            f"requiredFor={hr_req}" if hr_ok else "add humanReview.requiredFor",
        )
    )

    rules = (constitution or {}).get("spec", {}).get("policy", {}).get("rules") or []
    hard_rules = [
        r
        for r in rules
        if isinstance(r, dict) and r.get("effect") in {"deny", "ask", "require"}
    ]
    policy_ok = len(hard_rules) >= 1
    checks.append(
        _check(
            "policy_rules",
            "Policy has deny/ask/require rules",
            policy_ok,
            "L3",
            f"rules={len(hard_rules)}" if policy_ok else "add policy.rules",
        )
    )

    achieved = _highest_level(checks)
    target_ok = LEVEL_RANK[achieved] >= LEVEL_RANK[target]
    failures = [
        f"{c.level}:{c.name}"
        for c in checks
        if not c.passed and LEVEL_RANK[c.level] <= LEVEL_RANK[target]
    ]

    issued = _now()
    expires = None
    if achieved != "none" and ttl_days > 0:
        expires = (datetime.now(timezone.utc) + timedelta(days=ttl_days)).isoformat().replace(
            "+00:00", "Z"
        )

    return CertificationResult(
        certificationId=new_id("cert"),
        agentId=agent_id,
        status="passed" if target_ok else "failed",
        level=achieved,
        targetLevel=target,
        badge=BADGES.get(achieved),
        levelLabel=LEVEL_LABELS.get(achieved),
        algorithm=CERT_ALGORITHM,
        issuedAt=issued,
        expiresAt=expires,
        trustScore=trust_score,
        checks=checks,
        failures=failures,
        runId=run_id,
        proofHash=proof_hash,
        passportHash=passport_hash,
        constitutionId=constitution_id or None,
        constitutionHash=constitution_hash,
    )


def save_certificate(workspace: Path, result: CertificationResult) -> Path:
    root = workspace / ".uap" / "certification"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{result.agentId}.json"
    result.localPath = str(path)
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    hist = root / "history.jsonl"
    with hist.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")
    return path


def load_certificate(workspace: Path, agent_id: str) -> dict[str, Any] | None:
    path = workspace / ".uap" / "certification" / f"{agent_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
