"""Social channel registry — single source for gateway status and delivery."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable


def _env(*keys: str) -> str:
    for key in keys:
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return ""


def _has(*keys: str) -> bool:
    return bool(_env(*keys))


@dataclass(frozen=True)
class ChannelSpec:
    id: str
    name: str
    mode: str  # poll | webhook | stub
    tier: str  # live | beta | planned
    env_keys: tuple[str, ...]
    webhook_path: str | None = None
    enabled_fn: Callable[[], bool] | None = None

    def configured(self) -> bool:
        if self.enabled_fn is not None:
            return self.enabled_fn()
        return _has(*self.env_keys)

    def status_entry(self) -> dict[str, Any]:
        ok = self.configured()
        return {
            "id": self.id,
            "name": self.name,
            "configured": ok,
            "mode": self.mode if ok else "off",
            "tier": self.tier,
            "envKeys": list(self.env_keys),
            "webhookPath": self.webhook_path,
        }


def _split_channels(key: str) -> list[str]:
    raw = os.environ.get(key, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _youtube_poll_ready() -> bool:
    return _has("UAP_YOUTUBE_API_KEY", "YOUTUBE_API_KEY") and bool(
        _split_channels("UAP_YOUTUBE_POLL_CHANNELS")
        or _env("UAP_YOUTUBE_CHANNEL_ID", "YOUTUBE_CHANNEL_ID")
    )


def _import_enabled(module: str, fn: str) -> Callable[[], bool]:
    def _check() -> bool:
        try:
            import importlib

            mod = importlib.import_module(module)
            return bool(getattr(mod, fn)())
        except Exception:
            return False

    return _check


CHANNELS: tuple[ChannelSpec, ...] = (
    ChannelSpec(
        id="telegram",
        name="Telegram",
        mode="poll",
        tier="live",
        env_keys=("UAP_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"),
        webhook_path="/v1/agent/telegram/webhook",
        enabled_fn=_import_enabled("uap.telegram_gateway", "telegram_enabled"),
    ),
    ChannelSpec(
        id="whatsapp",
        name="WhatsApp",
        mode="webhook",
        tier="live",
        env_keys=(
            "UAP_WHATSAPP_TOKEN",
            "UAP_WHATSAPP_PHONE_NUMBER_ID",
            "UAP_TWILIO_ACCOUNT_SID",
            "UAP_TWILIO_AUTH_TOKEN",
            "UAP_TWILIO_WHATSAPP_FROM",
        ),
        webhook_path="/v1/agent/whatsapp/webhook",
        enabled_fn=_import_enabled("uap.whatsapp_gateway", "whatsapp_enabled"),
    ),
    ChannelSpec(
        id="discord",
        name="Discord",
        mode="poll",
        tier="live",
        env_keys=("UAP_DISCORD_BOT_TOKEN",),
        webhook_path="/v1/agent/discord/webhook",
        enabled_fn=_import_enabled("uap.discord_gateway", "discord_enabled"),
    ),
    ChannelSpec(
        id="slack",
        name="Slack",
        mode="webhook",
        tier="live",
        env_keys=("UAP_SLACK_BOT_TOKEN",),
        webhook_path="/v1/agent/slack/events",
        enabled_fn=_import_enabled("uap.slack_gateway", "slack_enabled"),
    ),
    ChannelSpec(
        id="x",
        name="X (Twitter)",
        mode="poll",
        tier="beta",
        env_keys=("UAP_X_BEARER_TOKEN", "X_BEARER_TOKEN"),
        webhook_path="/v1/agent/x/webhook",
        enabled_fn=_import_enabled("uap.x_gateway", "x_enabled"),
    ),
    ChannelSpec(
        id="facebook",
        name="Facebook Messenger",
        mode="webhook",
        tier="beta",
        env_keys=("UAP_FB_PAGE_ACCESS_TOKEN", "FB_PAGE_ACCESS_TOKEN"),
        webhook_path="/v1/agent/facebook/webhook",
        enabled_fn=_import_enabled("uap.facebook_gateway", "facebook_enabled"),
    ),
    ChannelSpec(
        id="youtube",
        name="YouTube",
        mode="poll",
        tier="beta",
        env_keys=("UAP_YOUTUBE_API_KEY", "YOUTUBE_API_KEY"),
        webhook_path="/v1/agent/youtube/webhook",
        enabled_fn=_youtube_poll_ready,
    ),
    ChannelSpec(
        id="instagram",
        name="Instagram",
        mode="webhook",
        tier="beta",
        env_keys=("UAP_IG_PAGE_ACCESS_TOKEN", "IG_PAGE_ACCESS_TOKEN"),
        webhook_path="/v1/agent/instagram/webhook",
        enabled_fn=_import_enabled("uap.instagram_gateway", "instagram_enabled"),
    ),
    ChannelSpec(
        id="tiktok",
        name="TikTok",
        mode="webhook",
        tier="beta",
        env_keys=("UAP_TIKTOK_CLIENT_KEY", "UAP_TIKTOK_CLIENT_SECRET"),
        webhook_path="/v1/agent/tiktok/webhook",
        enabled_fn=_import_enabled("uap.tiktok_gateway", "tiktok_enabled"),
    ),
    ChannelSpec(
        id="linkedin",
        name="LinkedIn",
        mode="webhook",
        tier="beta",
        env_keys=("UAP_LINKEDIN_ACCESS_TOKEN",),
        webhook_path="/v1/agent/linkedin/webhook",
        enabled_fn=_import_enabled("uap.linkedin_gateway", "linkedin_enabled"),
    ),
    ChannelSpec(
        id="signal",
        name="Signal",
        mode="webhook",
        tier="beta",
        env_keys=("UAP_SIGNAL_WEBHOOK_URL", "UAP_SIGNAL_SEND_URL"),
        webhook_path="/v1/agent/signal/webhook",
        enabled_fn=_import_enabled("uap.signal_gateway", "signal_enabled"),
    ),
    ChannelSpec(
        id="email",
        name="Email",
        mode="webhook",
        tier="live",
        env_keys=("UAP_SMTP_HOST", "UAP_SMTP_USER"),
        webhook_path="/v1/agent/email/webhook",
        enabled_fn=_import_enabled("uap.email_gateway", "email_enabled"),
    ),
    ChannelSpec(
        id="line",
        name="LINE",
        mode="webhook",
        tier="beta",
        env_keys=("UAP_LINE_CHANNEL_ACCESS_TOKEN",),
        webhook_path="/v1/agent/line/webhook",
        enabled_fn=_import_enabled("uap.line_gateway", "line_enabled"),
    ),
    ChannelSpec(
        id="wechat",
        name="WeChat",
        mode="webhook",
        tier="planned",
        env_keys=("UAP_WECHAT_APP_ID", "UAP_WECHAT_ACCESS_TOKEN"),
        webhook_path="/v1/agent/wechat/webhook",
        enabled_fn=_import_enabled("uap.wechat_gateway", "wechat_enabled"),
    ),
    ChannelSpec(
        id="imessage",
        name="iMessage",
        mode="webhook",
        tier="beta",
        env_keys=("UAP_BLUEBUBBLES_URL", "UAP_IMESSAGE_WEBHOOK_URL"),
        webhook_path="/v1/agent/imessage/webhook",
        enabled_fn=_import_enabled("uap.imessage_gateway", "imessage_enabled"),
    ),
)


def channel_by_id(channel_id: str) -> ChannelSpec | None:
    cid = (channel_id or "").lower().strip()
    for spec in CHANNELS:
        if spec.id == cid:
            return spec
    return None


def channels_status() -> dict[str, Any]:
    entries = {spec.id: spec.status_entry() for spec in CHANNELS}
    configured = sum(1 for s in CHANNELS if s.configured())
    return {
        "channels": entries,
        "configuredCount": configured,
        "totalCount": len(CHANNELS),
        "standard": "NGS-0029-gateway",
    }


def list_configured_channel_ids() -> list[str]:
    return [spec.id for spec in CHANNELS if spec.configured()]
