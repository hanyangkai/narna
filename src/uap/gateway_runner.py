"""Unified multi-channel gateway runner (Hermes-like process).

Webhook mode remains primary for Cloud. This runner long-polls Telegram
and optionally polls Discord/Slack channel histories when configured.
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


@dataclass
class GatewayConfig:
    telegram_token: str | None = None
    discord_token: str | None = None
    slack_token: str | None = None
    discord_channels: list[str] = field(default_factory=list)
    slack_channels: list[str] = field(default_factory=list)
    poll_seconds: float = 2.0


def config_from_env() -> GatewayConfig:
    def _split(key: str) -> list[str]:
        raw = os.environ.get(key, "")
        return [x.strip() for x in raw.split(",") if x.strip()]

    return GatewayConfig(
        telegram_token=os.environ.get("UAP_TELEGRAM_BOT_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN"),
        discord_token=os.environ.get("UAP_DISCORD_BOT_TOKEN"),
        slack_token=os.environ.get("UAP_SLACK_BOT_TOKEN"),
        discord_channels=_split("UAP_DISCORD_POLL_CHANNELS"),
        slack_channels=_split("UAP_SLACK_POLL_CHANNELS"),
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
        self._discord_last: dict[str, str] = {}
        self._slack_last: dict[str, str] = {}
        self._running = False
        self.stats: dict[str, int] = {
            "polled": 0,
            "handled": 0,
            "errors": 0,
            "voice": 0,
        }

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "telegramConfigured": bool(self.config.telegram_token),
            "discordConfigured": bool(self.config.discord_token and self.config.discord_channels),
            "slackConfigured": bool(self.config.slack_token and self.config.slack_channels),
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
        req = urllib.request.Request(url, headers={"User-Agent": "narna-gateway/0.2"})
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
        body = json.dumps({"chat_id": chat_id, "text": (text or "")[:4000]}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "narna-gateway/0.2"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()

    def _telegram_download_voice(self, file_id: str, dest: str) -> bool:
        token = self.config.telegram_token
        if not token:
            return False
        meta_url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
        with urllib.request.urlopen(meta_url, timeout=30) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
        path = ((meta.get("result") or {}).get("file_path") or "").strip()
        if not path:
            return False
        file_url = f"https://api.telegram.org/file/bot{token}/{path}"
        with urllib.request.urlopen(file_url, timeout=60) as resp:
            raw = resp.read()
        with open(dest, "wb") as f:
            f.write(raw)
        return True

    def _poll_telegram(self) -> int:
        n = 0
        for upd in self._telegram_get_updates():
            uid = int(upd.get("update_id") or 0)
            self._tg_offset = max(self._tg_offset, uid + 1)
            msg = upd.get("message") or upd.get("edited_message") or {}
            chat = (msg.get("chat") or {}).get("id")
            if chat is None:
                continue
            text = str(msg.get("text") or msg.get("caption") or "").strip()
            voice = msg.get("voice") or msg.get("audio")
            if voice and not text:
                self.stats["voice"] += 1
                from .voice_transcribe import transcribe_audio_file
                import tempfile
                from pathlib import Path

                file_id = str(voice.get("file_id") or "")
                if file_id:
                    with tempfile.TemporaryDirectory() as td:
                        dest = str(Path(td) / "voice.ogg")
                        if self._telegram_download_voice(file_id, dest):
                            tr = transcribe_audio_file(dest)
                            if tr.get("ok"):
                                text = str(tr.get("text") or "").strip()
                            else:
                                self._telegram_send(
                                    chat,
                                    f"Voice memo received but transcription failed: {tr.get('error')}",
                                )
                                continue
            if not text:
                continue
            out = self.handle_inbound(channel="telegram", text=text, external_id=str(chat))
            reply = str(out.get("answer") or "")
            dqs = out.get("dqs")
            if dqs is not None:
                reply = f"{reply}\n\n— ADQA DQS {dqs}"
            self._telegram_send(chat, reply)
            n += 1
        return n

    def _poll_discord(self) -> int:
        token = self.config.discord_token
        if not token or not self.config.discord_channels:
            return 0
        n = 0
        for channel_id in self.config.discord_channels:
            after = self._discord_last.get(channel_id, "0")
            url = (
                f"https://discord.com/api/v10/channels/{channel_id}/messages"
                f"?limit=5&after={after}"
            )
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bot {token}",
                    "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    msgs = json.loads(resp.read().decode("utf-8"))
            except Exception:
                self.stats["errors"] += 1
                continue
            if not isinstance(msgs, list):
                continue
            # Discord returns newest first
            for msg in sorted(msgs, key=lambda m: str(m.get("id") or "")):
                mid = str(msg.get("id") or "")
                self._discord_last[channel_id] = mid
                author = msg.get("author") or {}
                if author.get("bot"):
                    continue
                content = str(msg.get("content") or "").strip()
                if not content or content.startswith("/"):
                    continue
                out = self.handle_inbound(
                    channel="discord", text=content, external_id=channel_id
                )
                from .discord_gateway import send_discord_message, format_agent_reply

                send_discord_message(channel_id, format_agent_reply(out))
                n += 1
        return n

    def _poll_slack(self) -> int:
        token = self.config.slack_token
        if not token or not self.config.slack_channels:
            return 0
        n = 0
        for channel in self.config.slack_channels:
            oldest = self._slack_last.get(channel, "0")
            url = (
                f"https://slack.com/api/conversations.history"
                f"?channel={channel}&oldest={oldest}&limit=5"
            )
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "narna-gateway/0.2",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception:
                self.stats["errors"] += 1
                continue
            if not data.get("ok"):
                continue
            msgs = list(data.get("messages") or [])
            for msg in sorted(msgs, key=lambda m: float(m.get("ts") or 0)):
                ts = str(msg.get("ts") or "")
                if ts:
                    self._slack_last[channel] = ts
                if msg.get("bot_id") or msg.get("subtype"):
                    continue
                text = str(msg.get("text") or "").strip()
                if not text:
                    continue
                out = self.handle_inbound(channel="slack", text=text, external_id=channel)
                from .slack_gateway import send_slack_message, format_agent_reply

                send_slack_message(channel, format_agent_reply(out))
                n += 1
        return n

    def poll_once(self) -> int:
        self.stats["polled"] += 1
        n = 0
        try:
            if self.config.telegram_token:
                n += self._poll_telegram()
            if self.config.discord_token:
                n += self._poll_discord()
            if self.config.slack_token:
                n += self._poll_slack()
        except urllib.error.HTTPError as e:
            self.stats["errors"] += 1
            raise RuntimeError(f"gateway poll HTTP {e.code}") from e
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
                    pass
                i += 1
                if max_iterations is not None and i >= max_iterations:
                    break
                time.sleep(self.config.poll_seconds)
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False
