from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

PLANS = {
    "free": {"event_limit": 10_000},
    "pro": {"event_limit": 500_000},
    "team": {"event_limit": 2_000_000},
    "business": {"event_limit": 10_000_000},
}

PLAN_USD_PRICE = {
    "free": 0.0,
    "pro": 19.0,
    "team": 49.0,
    "business": 199.0,
}


def plan_event_limit(plan: str) -> int | None:
    p = PLANS.get(plan)
    return p["event_limit"] if p else None


def reset_if_new_period(*, period_start_at: datetime, now: datetime) -> bool:
    return (
        period_start_at.year != now.year
        or period_start_at.month != now.month
    )


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def plan_usd_price(plan: str) -> float:
    return float(PLAN_USD_PRICE.get(plan, 0.0))

