"""Natural-language cron → everyMinutes / runAt (Hermes-like)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_nl_schedule(text: str) -> dict[str, Any]:
    """
    Parse phrases like:
      every 30 minutes …
      every hour …
      daily / every day …
      weekly / every week …
      every monday …
      in 10 minutes …
      at 2026-08-27T12:00:00Z …
    Returns {everyMinutes?, runAt?, prompt, channel?, raw}.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("schedule text required")

    channel = "job"
    ch_m = re.search(r"\b(?:to|on|via)\s+(telegram|discord|slack|email|web|whatsapp)\b", raw, re.I)
    if ch_m:
        channel = ch_m.group(1).lower()

    # Strip leading /cron
    body = re.sub(r"^/cron\s+", "", raw, flags=re.I).strip()

    every: int | None = None
    run_at: str | None = None
    prompt = body

    # ISO run-at
    iso_m = re.search(
        r"\bat\s+(\d{4}-\d{2}-\d{2}T[\d:.\-+Z]+)\b",
        body,
        re.I,
    )
    if iso_m:
        run_at = iso_m.group(1)
        prompt = (body[: iso_m.start()] + body[iso_m.end() :]).strip()
        prompt = re.sub(r"^(run|schedule|remind(?:\s+me)?)\s+", "", prompt, flags=re.I).strip()
        return {
            "everyMinutes": None,
            "runAt": run_at,
            "prompt": prompt or body,
            "channel": channel,
            "raw": raw,
        }

    # in N minutes/hours
    in_m = re.search(r"\bin\s+(\d+)\s*(minutes?|mins?|hours?|hrs?)\b", body, re.I)
    if in_m:
        n = int(in_m.group(1))
        unit = in_m.group(2).lower()
        delta = timedelta(hours=n) if unit.startswith("h") else timedelta(minutes=n)
        run_at = _iso(_now() + delta)
        prompt = (body[: in_m.start()] + body[in_m.end() :]).strip()
        prompt = re.sub(r"^(run|schedule|remind(?:\s+me)?)\s+", "", prompt, flags=re.I).strip()
        return {
            "everyMinutes": None,
            "runAt": run_at,
            "prompt": prompt or "scheduled reminder",
            "channel": channel,
            "raw": raw,
        }

    patterns: list[tuple[re.Pattern[str], int]] = [
        (re.compile(r"\bevery\s+(\d+)\s*(minutes?|mins?)\b", re.I), 0),  # special
        (re.compile(r"\bevery\s+(\d+)\s*(hours?|hrs?)\b", re.I), 0),
        (re.compile(r"\bevery\s+hour\b", re.I), 60),
        (re.compile(r"\bhourly\b", re.I), 60),
        (re.compile(r"\bevery\s+day\b|\bdaily\b", re.I), 1440),
        (re.compile(r"\bevery\s+week\b|\bweekly\b", re.I), 10080),
        (re.compile(r"\bevery\s+monday\b", re.I), 10080),
    ]

    for pat, fixed in patterns:
        m = pat.search(body)
        if not m:
            continue
        if fixed:
            every = fixed
        else:
            n = int(m.group(1))
            unit = m.group(2).lower()
            every = n * 60 if unit.startswith("h") else n
        prompt = (body[: m.start()] + body[m.end() :]).strip()
        break

    prompt = re.sub(
        r"^(run|schedule|remind(?:\s+me)?(?:\s+to)?)\s+",
        "",
        prompt,
        flags=re.I,
    ).strip()
    prompt = re.sub(r"^(to|that)\s+", "", prompt, flags=re.I).strip() or body

    if every is None and run_at is None:
        # default: one-shot soon
        run_at = _iso(_now() + timedelta(minutes=1))

    return {
        "everyMinutes": every,
        "runAt": run_at,
        "prompt": prompt[:4000],
        "channel": channel,
        "raw": raw,
    }
