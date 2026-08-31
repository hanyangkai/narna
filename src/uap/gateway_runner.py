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
from pathlib import Path
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
        workspace: str | Path | None = None,
    ) -> None:
        self.ask_fn = ask_fn
        self.config = config or config_from_env()
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self._tg_offset = 0
        self._discord_last: dict[str, str] = {}
        self._slack_last: dict[str, str] = {}
        self._discord_seen: set[str] = set()
        self._slack_seen: set[str] = set()
        self._youtube_seen: set[str] = set()
        self._running = False
        self.stats: dict[str, int] = {
            "polled": 0,
            "handled": 0,
            "errors": 0,
            "voice": 0,
            "deduped": 0,
        }

    def status(self) -> dict[str, Any]:
        from .channels.registry import channels_status
        from .gateway_pairing import pairing_enabled

        reg = channels_status()
        return {
            "running": self._running,
            "telegramConfigured": bool(self.config.telegram_token),
            "discordConfigured": bool(
                self.config.discord_token and self.config.discord_channels
            ),
            "slackConfigured": bool(
                self.config.slack_token and self.config.slack_channels
            ),
            "pollSeconds": self.config.poll_seconds,
            "pairingEnabled": pairing_enabled(),
            "workspace": str(self.workspace),
            "stats": dict(self.stats),
            **reg,
        }

    def handle_inbound(
        self,
        *,
        channel: str,
        text: str,
        external_id: str | None = None,
    ) -> dict[str, Any]:
        from .gateway_pairing import gate_inbound

        blocked = gate_inbound(
            channel=channel,
            external_id=external_id,
            text=text,
            workspace=self.workspace,
        )
        if blocked:
            self.stats["handled"] += 1
            return {
                "ok": True,
                "answer": blocked.get("answer"),
                "pairing": True,
                "paired": blocked.get("paired"),
                "dqs": None,
            }
        out = self.ask_fn(text, channel, external_id)
        self.stats["handled"] += 1
        return out if isinstance(out, dict) else {"ok": True, "answer": str(out)}

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
            inbound_voice = bool(voice)
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
            voice_reply = str(os.environ.get("UAP_GATEWAY_VOICE_REPLY") or "").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            if inbound_voice and voice_reply:
                try:
                    from pathlib import Path

                    from .agent_tools import tool_text_to_speech
                    from .telegram_gateway import send_telegram_voice

                    tts = tool_text_to_speech(
                        {"text": reply[:500], "name": f"tg_{chat}.mp3"},
                        workspace=self.workspace,
                    )
                    if tts.get("ok") and tts.get("path"):
                        audio = Path(str(self.workspace) / str(tts["path"]))
                        if not audio.is_file():
                            audio = Path(str(tts["path"]))
                        send_telegram_voice(chat, str(audio), caption=reply[:200])
                        n += 1
                        continue
                except Exception:
                    self.stats["errors"] += 1
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
                if not mid:
                    continue
                if mid in self._discord_seen:
                    self.stats["deduped"] += 1
                    continue
                self._discord_seen.add(mid)
                if len(self._discord_seen) > 500:
                    self._discord_seen = set(list(self._discord_seen)[-250:])
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
            # Slack oldest is inclusive — bump slightly past last ts to reduce re-delivery
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
                if not ts:
                    continue
                if ts in self._slack_seen or (oldest != "0" and ts == oldest):
                    self.stats["deduped"] += 1
                    # still advance watermark past seen
                    try:
                        self._slack_last[channel] = str(float(ts) + 0.000001)
                    except Exception:
                        self._slack_last[channel] = ts
                    continue
                self._slack_seen.add(ts)
                if len(self._slack_seen) > 500:
                    self._slack_seen = set(list(self._slack_seen)[-250:])
                try:
                    self._slack_last[channel] = str(float(ts) + 0.000001)
                except Exception:
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

    def _poll_youtube(self) -> int:
        from .youtube_gateway import (
            format_agent_reply,
            list_recent_comments,
            list_uploads,
            poll_channel_ids,
            reply_youtube_comment,
            youtube_enabled,
        )

        if not youtube_enabled():
            return 0
        channel_ids = poll_channel_ids()
        if not channel_ids:
            return 0
        n = 0
        bot_channel = os.environ.get("UAP_YOUTUBE_BOT_CHANNEL_ID", "").strip()
        for channel_id in channel_ids:
            video_ids = list_uploads(channel_id, max_results=2)
            for video_id in video_ids:
                threads, _ = list_recent_comments(video_id)
                for thread in threads:
                    tid = str(thread.get("id") or "")
                    if not tid or tid in self._youtube_seen:
                        continue
                    snippet = ((thread.get("snippet") or {}).get("topLevelComment") or {}).get(
                        "snippet"
                    ) or {}
                    author = str((snippet.get("authorChannelId") or {}).get("value") or "")
                    text = str(snippet.get("textDisplay") or snippet.get("textOriginal") or "").strip()
                    if not text:
                        continue
                    if bot_channel and author == bot_channel:
                        continue
                    self._youtube_seen.add(tid)
                    if len(self._youtube_seen) > 500:
                        self._youtube_seen = set(list(self._youtube_seen)[-250:])
                    out = self.handle_inbound(
                        channel="youtube",
                        text=text,
                        external_id=author or tid,
                    )
                    reply_text = format_agent_reply(out)
                    try:
                        reply_youtube_comment(tid, reply_text)
                    except Exception:
                        self.stats["errors"] += 1
                        continue
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
            n += self._poll_youtube()
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
