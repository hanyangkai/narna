"""Local gateway channel tokens — ~/.narna/gateway.json (Hermes-like desktop setup)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .narna_config import default_home

# config key → env var(s) first wins
GATEWAY_ENV_MAP: dict[str, tuple[str, ...]] = {
    "telegramBotToken": ("UAP_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"),
    "discordBotToken": ("UAP_DISCORD_BOT_TOKEN",),
    "slackBotToken": ("UAP_SLACK_BOT_TOKEN",),
    "whatsappTwilioSid": ("UAP_TWILIO_ACCOUNT_SID", "TWILIO_ACCOUNT_SID"),
    "whatsappTwilioToken": ("UAP_TWILIO_AUTH_TOKEN", "TWILIO_AUTH_TOKEN"),
    "whatsappFrom": ("UAP_TWILIO_WHATSAPP_FROM", "TWILIO_WHATSAPP_FROM"),
    "whatsappCloudToken": ("UAP_WHATSAPP_TOKEN",),
    "whatsappPhoneNumberId": ("UAP_WHATSAPP_PHONE_NUMBER_ID",),
    "whatsappVerifyToken": ("UAP_WHATSAPP_VERIFY_TOKEN",),
    "xBearerToken": ("UAP_X_BEARER_TOKEN", "X_BEARER_TOKEN"),
    "fbPageToken": ("UAP_FB_PAGE_ACCESS_TOKEN", "FB_PAGE_ACCESS_TOKEN"),
    "fbVerifyToken": ("UAP_FB_VERIFY_TOKEN", "FB_VERIFY_TOKEN"),
    "igPageToken": ("UAP_IG_PAGE_ACCESS_TOKEN", "IG_PAGE_ACCESS_TOKEN"),
    "youtubeApiKey": ("UAP_YOUTUBE_API_KEY", "YOUTUBE_API_KEY"),
    "discordPollChannels": ("UAP_DISCORD_POLL_CHANNELS",),
    "slackPollChannels": ("UAP_SLACK_POLL_CHANNELS",),
}

KNOWN_GATEWAY_KEYS = tuple(GATEWAY_ENV_MAP.keys()) + ("gatewayEnabled",)


def gateway_path(home: Path | None = None) -> Path:
    return (Path(home) if home else default_home()) / "gateway.json"


def load_gateway_config(home: Path | None = None) -> dict[str, Any]:
    path = gateway_path(home)
    if not path.exists():
        return {"gatewayEnabled": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"gatewayEnabled": False}
    except Exception:
        return {"gatewayEnabled": False}


def save_gateway_config(data: dict[str, Any], home: Path | None = None) -> Path:
    root = Path(home) if home else default_home()
    root.mkdir(parents=True, exist_ok=True)
    prev = load_gateway_config(root)
    merged = {**prev, **{k: v for k, v in data.items() if k in KNOWN_GATEWAY_KEYS}}
    path = gateway_path(root)
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def apply_gateway_to_env(home: Path | None = None) -> dict[str, Any]:
    cfg = load_gateway_config(home)
    for key, env_keys in GATEWAY_ENV_MAP.items():
        val = cfg.get(key)
        if val is None or str(val).strip() == "":
            continue
        for ek in env_keys:
            os.environ.setdefault(ek, str(val).strip())
    return cfg


def gateway_config_masked(home: Path | None = None) -> dict[str, Any]:
    cfg = load_gateway_config(home)
    out: dict[str, Any] = {"gatewayEnabled": bool(cfg.get("gatewayEnabled"))}
    for key in GATEWAY_ENV_MAP:
        val = str(cfg.get(key) or "")
        if not val:
            out[key] = None
            out[f"{key}Set"] = False
        elif len(val) > 8:
            out[key] = val[:4] + "…" + val[-4:]
            out[f"{key}Set"] = True
        else:
            out[key] = "***"
            out[f"{key}Set"] = True
    return out
