"""Cloud plan quotas — Free · Cloud $20 · Team (seats).

Legacy aliases: pro → cloud, business kept for Stripe/Paddle price IDs.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import os

# Soft caps warn; hard caps → HTTP 402. None = unlimited (still soft-cap warned).
PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "event_limit": 10_000,
        "gu_limit": 1_000,
        "adqa_soft_cap": 100,
        "adqa_hard_cap": 500,
        "agent_turns_soft_cap": 40,
        "agent_turns_hard_cap": 50,
        "seats": 1,
        "enforcement": "hard",
        "usd": 0.0,
        "byo_llm": False,
    },
    "cloud": {
        "event_limit": None,
        "gu_limit": 5_000_000,
        "adqa_soft_cap": 50_000,
        "adqa_hard_cap": None,
        "agent_turns_soft_cap": 4_000,
        "agent_turns_hard_cap": 5_000,
        "seats": 1,
        "enforcement": "soft",
        "usd": 20.0,
        "byo_llm": True,
        "display_name": "personal",
    },
    # Alias used by older checkout / Stripe price ids
    "pro": {
        "event_limit": None,
        "gu_limit": 5_000_000,
        "adqa_soft_cap": 50_000,
        "adqa_hard_cap": None,
        "agent_turns_soft_cap": 4_000,
        "agent_turns_hard_cap": 5_000,
        "seats": 1,
        "enforcement": "soft",
        "usd": 20.0,
        "alias_of": "cloud",
        "byo_llm": True,
    },
    "team": {
        "event_limit": None,
        "gu_limit": 20_000_000,
        "adqa_soft_cap": 200_000,
        "adqa_hard_cap": None,
        "agent_turns_soft_cap": 40_000,
        "agent_turns_hard_cap": 50_000,
        "seats": 3,
        "seat_max": 50,
        "enforcement": "soft",
        "usd": 99.0,  # per seat / mo
        "usd_per_seat": 99.0,
        "byo_llm": True,
    },
    "business": {
        "event_limit": 10_000_000,
        "gu_limit": 2_000_000,
        "adqa_soft_cap": 500_000,
        "adqa_hard_cap": None,
        "agent_turns_soft_cap": 100_000,
        "agent_turns_hard_cap": None,
        "seats": 10,
        "enforcement": "soft",
        "usd": 199.0,
        "byo_llm": True,
    },
}

PLAN_USD_PRICE = {k: float(v.get("usd") or 0.0) for k, v in PLANS.items()}


def normalize_plan(plan: str) -> str:
    p = (plan or "free").strip().lower()
    if p == "pro":
        return "cloud"
    return p if p in PLANS else "free"


def plan_def(plan: str) -> dict[str, Any]:
    return PLANS.get(normalize_plan(plan), PLANS["free"])


def plan_event_limit(plan: str) -> int | None:
    return plan_def(plan).get("event_limit")


def plan_gu_limit(plan: str) -> int | None:
    return plan_def(plan).get("gu_limit")


def plan_adqa_soft_cap(plan: str) -> int | None:
    return plan_def(plan).get("adqa_soft_cap")


def plan_adqa_hard_cap(plan: str) -> int | None:
    return plan_def(plan).get("adqa_hard_cap")


def plan_agent_turns_hard_cap(plan: str) -> int | None:
    return plan_def(plan).get("agent_turns_hard_cap")


def plan_agent_turns_soft_cap(plan: str) -> int | None:
    return plan_def(plan).get("agent_turns_soft_cap")


def plan_allows_byo_llm(plan: str) -> bool:
    return bool(plan_def(plan).get("byo_llm"))


def plan_seats(plan: str) -> int:
    return int(plan_def(plan).get("seats") or 1)


def count_governance_units(events: list[dict]) -> int:
    """Count GU from ingested events (ExecutionUnitStarted payloads)."""
    total = 0
    for evt in events:
        if evt.get("eventType") != "ExecutionUnitStarted":
            continue
        payload = evt.get("payload") or {}
        eu = payload.get("executionUnit") or {}
        total += int(eu.get("guCost") or 1)
    return total


def reset_if_new_period(*, period_start_at: datetime, now: datetime) -> bool:
    return period_start_at.year != now.year or period_start_at.month != now.month


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def plan_usd_price(plan: str) -> float:
    return float(plan_def(plan).get("usd") or 0.0)


def plan_usd_per_seat(plan: str) -> float | None:
    p = plan_def(plan)
    if "usd_per_seat" in p:
        return float(p["usd_per_seat"])
    return None


def plan_seat_max(plan: str) -> int:
    return int(plan_def(plan).get("seat_max") or plan_seats(plan))


def checkout_usd_amount(plan: str, *, seats: int | None = None) -> tuple[float, int]:
    """Return (usd_total, seat_count) for a payable checkout."""
    p = normalize_plan(plan)
    if p == "team":
        per = float(plan_def(p).get("usd_per_seat") or 99.0)
        n = int(seats if seats is not None else plan_seats(p))
        lo = plan_seats(p)
        hi = plan_seat_max(p)
        n = max(lo, min(hi, n))
        return round(per * n, 2), n
    return float(plan_def(p).get("usd") or 0.0), plan_seats(p)


def plan_price_cents(plan: str) -> int:
    p = normalize_plan(plan)
    if p == "cloud":
        return 2000
    if p == "team":
        return 9900  # 1 seat default display; seats billed separately
    if p == "business":
        return 19900
    return 0


def plan_duration_days() -> int:
    return int(os.environ.get("UAP_PLAN_DURATION_DAYS", "30"))


def add_plan_period(start: datetime | None = None) -> datetime:
    base = start or now_utc()
    return base + timedelta(days=plan_duration_days())
