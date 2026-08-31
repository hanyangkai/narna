"""Plan quota enforcement for Cloud SaaS."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .billing import (
    now_utc,
    plan_adqa_hard_cap,
    plan_adqa_soft_cap,
    plan_agent_turns_hard_cap,
    plan_agent_turns_soft_cap,
    plan_event_limit,
    plan_gu_limit,
    reset_if_new_period,
)
from .metrics import METRICS
from .models import Organization


def _downgrade_if_plan_expired(org: Organization) -> None:
    """Paid plans expire after plan_expires_at — drop to free."""
    expires = getattr(org, "plan_expires_at", None)
    if expires is None:
        return
    plan = (org.plan or "free").lower()
    if plan in {"free", ""}:
        return
    now = now_utc()
    if expires.tzinfo is None:
        from datetime import timezone

        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= now:
        org.plan = "free"
        org.seat_count = 1
        org.plan_expires_at = None
        org.period_start_at = now
        org.events_in_period = 0
        org.gu_in_period = 0
        if hasattr(org, "adqa_checks_in_period"):
            org.adqa_checks_in_period = 0
        if hasattr(org, "agent_turns_in_period"):
            org.agent_turns_in_period = 0


def reset_period_if_needed(org: Organization) -> None:
    _downgrade_if_plan_expired(org)
    now = now_utc()
    if org.period_start_at is None or reset_if_new_period(
        period_start_at=org.period_start_at, now=now
    ):
        org.period_start_at = now
        org.events_in_period = 0
        org.gu_in_period = 0
        if hasattr(org, "adqa_checks_in_period"):
            org.adqa_checks_in_period = 0
        if hasattr(org, "agent_turns_in_period"):
            org.agent_turns_in_period = 0


def enforce_plan_limit(
    *,
    org: Organization,
    projected_events: int = 0,
    projected_gu: int = 0,
    projected_adqa: int = 0,
    projected_agent_turns: int = 0,
) -> dict[str, Any] | None:
    """Raise 402 on hard caps. Return soft-warning dict when near/over soft caps."""
    reset_period_if_needed(org)

    gu_limit = plan_gu_limit(org.plan)
    if gu_limit is not None and projected_gu > 0:
        if (int(org.gu_in_period or 0) + projected_gu) > gu_limit:
            METRICS.inc_402()
            raise HTTPException(
                status_code=402,
                detail=f"plan GU limit exceeded: plan={org.plan}, limit={gu_limit} GU/mo",
            )

    limit = plan_event_limit(org.plan)
    if limit is not None and projected_events > 0:
        if (int(org.events_in_period or 0) + projected_events) > limit:
            METRICS.inc_402()
            raise HTTPException(
                status_code=402,
                detail=f"plan limit exceeded: plan={org.plan}, limit={limit} events/mo",
            )

    warning: dict[str, Any] | None = None
    if projected_adqa > 0:
        used = int(getattr(org, "adqa_checks_in_period", 0) or 0)
        hard = plan_adqa_hard_cap(org.plan)
        soft = plan_adqa_soft_cap(org.plan)
        if hard is not None and (used + projected_adqa) > hard:
            METRICS.inc_402()
            raise HTTPException(
                status_code=402,
                detail=(
                    f"ADQA hard cap exceeded: plan={org.plan}, "
                    f"used={used}, limit={hard} checks/mo — use Desktop free: https://narna.org/download"
                ),
            )
        if soft is not None and (used + projected_adqa) > soft:
            warning = {
                "quotaWarning": True,
                "metric": "adqa",
                "used": used,
                "softCap": soft,
                "plan": org.plan,
                "message": f"ADQA soft cap {soft}/mo exceeded — still allowed on {org.plan}",
            }
            METRICS.inc_quota_warning()

    if projected_agent_turns > 0:
        used_t = int(getattr(org, "agent_turns_in_period", 0) or 0)
        hard_t = plan_agent_turns_hard_cap(org.plan)
        soft_t = plan_agent_turns_soft_cap(org.plan)
        if hard_t is not None and (used_t + projected_agent_turns) > hard_t:
            METRICS.inc_402()
            raise HTTPException(
                status_code=402,
                detail=(
                    f"Ask NARNA quota exceeded: plan={org.plan}, "
                    f"used={used_t}, limit={hard_t} turns/mo — Desktop free: https://narna.org/download"
                ),
            )
        if soft_t is not None and (used_t + projected_agent_turns) > soft_t:
            warning = {
                "quotaWarning": True,
                "metric": "agent_turns",
                "used": used_t,
                "softCap": soft_t,
                "plan": org.plan,
                "message": f"Ask soft cap {soft_t}/mo exceeded — still allowed on {org.plan}",
            }
            METRICS.inc_quota_warning()
    return warning


def bump_adqa_usage(*, org: Organization, db: Session, n: int = 1) -> None:
    reset_period_if_needed(org)
    current = int(getattr(org, "adqa_checks_in_period", 0) or 0)
    org.adqa_checks_in_period = current + n
    METRICS.inc_adqa()
    db.add(org)
    db.commit()


def bump_agent_turns(*, org: Organization, db: Session, n: int = 1) -> None:
    reset_period_if_needed(org)
    current = int(getattr(org, "agent_turns_in_period", 0) or 0)
    org.agent_turns_in_period = current + n
    db.add(org)
    db.commit()
