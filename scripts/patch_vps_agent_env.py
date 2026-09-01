#!/usr/bin/env python3
"""Patch VPS .env from environment variables (used by GitHub Actions deploy)."""

from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    p = Path("/opt/narna/web/deploy/selfhost/.env")
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    lines = text.splitlines()
    kv: dict[str, str] = {}
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        kv[k.strip()] = v.strip().strip('"').strip("'")

    changed = False
    mapping = {
        "UAP_OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
        "UAP_TELEGRAM_BOT_TOKEN": "TELEGRAM_BOT_TOKEN",
        "UAP_DISCORD_BOT_TOKEN": "DISCORD_BOT_TOKEN",
        "UAP_SLACK_BOT_TOKEN": "SLACK_BOT_TOKEN",
        "UAP_TWILIO_ACCOUNT_SID": "TWILIO_ACCOUNT_SID",
        "UAP_TWILIO_AUTH_TOKEN": "TWILIO_AUTH_TOKEN",
        "UAP_TWILIO_WHATSAPP_FROM": "TWILIO_WHATSAPP_FROM",
        "UAP_SIGNAL_WEBHOOK_URL": "SIGNAL_WEBHOOK_URL",
        "UAP_X_BEARER_TOKEN": "X_BEARER_TOKEN",
        "UAP_X_API_SECRET": "X_API_SECRET",
        "UAP_X_BOT_USER_ID": "X_BOT_USER_ID",
        "UAP_FB_PAGE_ACCESS_TOKEN": "FB_PAGE_ACCESS_TOKEN",
        "UAP_FB_VERIFY_TOKEN": "FB_VERIFY_TOKEN",
        "UAP_IG_PAGE_ACCESS_TOKEN": "IG_PAGE_ACCESS_TOKEN",
        "UAP_YOUTUBE_API_KEY": "YOUTUBE_API_KEY",
        "UAP_YOUTUBE_OAUTH_TOKEN": "YOUTUBE_OAUTH_TOKEN",
        "UAP_YOUTUBE_CHANNEL_ID": "YOUTUBE_CHANNEL_ID",
        "UAP_YOUTUBE_POLL_CHANNELS": "YOUTUBE_POLL_CHANNELS",
        "UAP_RESEND_API_KEY": "RESEND_API_KEY",
    }
    for dest, src in mapping.items():
        val = os.environ.get(src, "").strip()
        if val:
            kv[dest] = val
            changed = True
            if dest == "UAP_OPENROUTER_API_KEY":
                kv["UAP_ROUTER_PROVIDER"] = "openrouter"

    # Resend from-address (optional override)
    from_addr = os.environ.get("UAP_RESEND_FROM", "").strip()
    if from_addr:
        kv["UAP_RESEND_FROM"] = from_addr
        changed = True
    site_url = os.environ.get("UAP_SITE_URL", "").strip()
    if site_url:
        kv["UAP_SITE_URL"] = site_url
        changed = True

    if not changed:
        print("no secret patches")
        return

    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            out.append(line)
            continue
        k = s.split("=", 1)[0].strip()
        if k in kv:
            out.append(f"{k}={kv[k]}")
            seen.add(k)
        else:
            out.append(line)
    for k, v in kv.items():
        if k not in seen:
            out.append(f"{k}={v}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("env patched", sorted(k for k in mapping if kv.get(k)))


if __name__ == "__main__":
    main()
