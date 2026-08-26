"""Unified multi-channel gateway runner (Hermes-like process).

Webhook mode remains primary for Cloud. This runner is for self-host /
local long-poll loops when bot tokens are present.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable


AskFn = Callable[[str, str, str | None], dict[str, Any]]
# ask(message, channel, external_id) -> agent result


@dataclass
class GatewayConfig:
    telegram_token: str | None = None
    poll_seconds: float = 2.0
    channels: list[str] = field(default_factory=lambda: ["telegram"])


def config_from_env() -> GatewayConfig:
    return GatewayConfig(
        telegram_token=os.environ.get("UAP_TELEGRAM_BOT_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN"),
        poll_seconds=float(os.environ.get("UAP_GATEWAY_POLL_SECONDS") or 2),
    )


class UnifiedGateway:
    """Single process that fans inbound channel messages into NarnaAgent.ask."""

    def __init__(
        self,
        *,
        ask_fn: AskFn,
        config: GatewayConfig | None = None,
    ) -> None:
        self.ask_fn = ask_fn
        self.config = config or config_from_env()
        self._tg_offset = 0
        self._running = False
        self.stats: dict[str, int] = {"polled": 0, "handled": 0, "errors": 0}

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "telegramConfigured": bool(self.config.telegram_token),
            "pollSeconds": self.config.poll_seconds,
            "stats": dict(self.stats),
            "standard": "NGS-0029-gateway",
        }

    def handle_inbound(
        self,
        *,
        channel: str,
        text: str,
        external_id: str | None = None,
    ) -> dict[str, Any]:
        out = self.ask_fn(text, channel, external_id)
        self.stats["handled"] += 1
        return out

    def _telegram_get_updates(self) -> list[dict[str, Any]]:
        token = self.config.telegram_token
        if not token:
            return []
        url = (
            f"https://api.telegram.org/bot{token}/getUpdates"
            f"?timeout=0&offset={self._tg_offset}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "narna-gateway/0.1"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data.get("ok"):
            return []
        return list(data.get("result") or [])

    def _telegram_send(self, chat_id: str | int, text: str) -> None:
        token = self.config.telegram_token
        if not token:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        body = json.dumps(
            {"chat_id": chat_id, "text": (text or "")[:4000]}
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "narna-gateway/0.1"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()

    def poll_once(self) -> int:
        """Poll configured channels once. Returns number of messages handled."""
        n = 0
        self.stats["polled"] += 1
        if self.config.telegram_token:
            try:
                for upd in self._telegram_get_updates():
                    uid = int(upd.get("update_id") or 0)
                    self._tg_offset = max(self._tg_offset, uid + 1)
                    msg = upd.get("message") or upd.get("edited_message") or {}
                    text = str(msg.get("text") or "").strip()
                    chat = (msg.get("chat") or {}).get("id")
                    if not text or chat is None:
                        continue
                    out = self.handle_inbound(
                        channel="telegram",
                        text=text,
                        external_id=str(chat),
                    )
                    reply = str(out.get("answer") or "")
                    dqs = out.get("dqs")
                    if dqs is not None:
                        reply = f"{reply}\n\n— ADQA DQS {dqs}"
                    self._telegram_send(chat, reply)
                    n += 1
            except urllib.error.HTTPError as e:
                self.stats["errors"] += 1
                raise RuntimeError(f"telegram poll HTTP {e.code}") from e
            except Exception:
                self.stats["errors"] += 1
                raise
        return n

    def run_forever(self, *, max_iterations: int | None = None) -> None:
        self._running = True
        i = 0
        try:
            while self._running:
                try:
                    self.poll_once()
                except Exception:
                    # keep looping; stats already bumped
                    pass
                i += 1
                if max_iterations is not None and i >= max_iterations:
                    break
                time.sleep(self.config.poll_seconds)
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False
