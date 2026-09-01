"""Pro feature gates — Desktop free; cloud Pro unlocks premium connectivity."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from .billing import normalize_plan, plan_def, plan_sync_push_cap
from .models import Organization

PAID_PLANS = frozenset({"cloud", "team", "business"})

# Boolean or numeric limits per normalized plan name.
FEATURE_MATRIX: dict[str, dict[str, Any]] = {
    "cloud_sync": {"free": False, "cloud": True, "team": True, "business": True},
    "recurring_jobs": {"free": False, "cloud": True, "team": True, "business": True},
    "quality_mode": {"free": False, "cloud": True, "team": True, "business": True},
    "critical_mode": {"free": False, "cloud": True, "team": True, "business": True},
    "hosted_channels": {"free": False, "cloud": True, "team": True, "business": True},
    "decision_replay_cloud": {"free": False, "cloud": True, "team": True, "business": True},
    "private_skill_publish": {"free": False, "cloud": True, "team": True, "business": True},
    "trace_retention_days": {"free": 7, "cloud": 365, "team": 365, "business": 365},
}


def is_paid_plan(plan: str) -> bool:
    return normalize_plan(plan) in PAID_PLANS


def feature_enabled(plan: str, feature: str) -> bool:
    row = FEATURE_MATRIX.get(feature, {})
    p = normalize_plan(plan)
    val = row.get(p, row.get("free", False))
    return bool(val)


def feature_limit(plan: str, feature: str) -> int | None:
    row = FEATURE_MATRIX.get(feature, {})
    p = normalize_plan(plan)
    val = row.get(p, row.get("free"))
    if val is None:
        return None
    return int(val) if isinstance(val, (int, float)) else None


def plan_features_payload(plan: str) -> dict[str, Any]:
    p = normalize_plan(plan)
    paid = is_paid_plan(p)
    return {
        "plan": p,
        "isPro": paid,
        "displayName": plan_def(p).get("display_name") or ("Pro" if paid else "Free"),
        "cloudSync": feature_enabled(p, "cloud_sync"),
        "recurringJobs": feature_enabled(p, "recurring_jobs"),
        "qualityMode": feature_enabled(p, "quality_mode"),
        "criticalMode": feature_enabled(p, "critical_mode"),
        "hostedChannels": feature_enabled(p, "hosted_channels"),
        "decisionReplayCloud": feature_enabled(p, "decision_replay_cloud"),
        "privateSkillPublish": feature_enabled(p, "private_skill_publish"),
        "traceRetentionDays": feature_limit(p, "trace_retention_days"),
        "syncPushLimit": plan_sync_push_cap(p),
        "upgradeUrl": "https://narna.org/checkout",
    }


def require_feature(org: Organization, feature: str, *, detail: str | None = None) -> None:
    p = normalize_plan(org.plan)
    if feature_enabled(p, feature):
        return
    msg = detail or (
        f"Pro required for {feature.replace('_', ' ')} — upgrade at https://narna.org/checkout"
    )
    raise HTTPException(
        status_code=402,
        detail=msg,
        headers={"X-Narna-Upgrade": "https://narna.org/checkout"},
    )


def require_paid(org: Organization, *, detail: str | None = None) -> None:
    if is_paid_plan(org.plan):
        return
    raise HTTPException(
        status_code=402,
        detail=detail or "Pro plan required — upgrade at https://narna.org/checkout",
        headers={"X-Narna-Upgrade": "https://narna.org/checkout"},
    )
