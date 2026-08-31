"""TikTok gateway — webhook ingest + optional Business Messaging outbound."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def tiktok_enabled() -> bool:
    return bool(
        os.environ.get("UAP_TIKTOK_CLIENT_KEY", "").strip()
        and os.environ.get("UAP_TIKTOK_CLIENT_SECRET", "").strip()
        and os.environ.get("UAP_TIKTOK_MESSAGING_ENABLED", "").strip().lower()
        in {"1", "true", "yes", "on"}
    )


def extract_tiktok_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    user = str(
        payload.get("open_id")
        or payload.get("user_id")
        or payload.get("from")
        or ""
    ).strip()
    text = str(payload.get("text") or payload.get("content") or payload.get("message") or "").strip()
    # Nested event shapes
    if not user or not text:
        data = payload.get("data") or payload.get("event") or {}
        if isinstance(data, dict):
            user = user or str(data.get("open_id") or data.get("user_id") or "").strip()
            text = text or str(data.get("text") or data.get("content") or "").strip()
    if user and text:
        return user, text
    return None, None


def send_tiktok_message(user_id: str, text: str) -> dict[str, Any]:
    if not tiktok_enabled():
        raise RuntimeError("TikTok messaging not enabled — set UAP_TIKTOK_MESSAGING_ENABLED=1")
    access = (
        os.environ.get("UAP_TIKTOK_ACCESS_TOKEN")
        or os.environ.get("TIKTOK_ACCESS_TOKEN")
        or ""
    ).strip()
    base = (
        os.environ.get("UAP_TIKTOK_API_BASE") or "https://business-api.tiktok.com"
    ).rstrip("/")
    # Prefer explicit relay URL for partner integrations
    relay = (os.environ.get("UAP_TIKTOK_SEND_URL") or "").strip()
    url = relay or f"{base}/open_api/v1.3/message/send/"
    if not access and not relay:
        return {
            "ok": False,
            "error": "Set UAP_TIKTOK_ACCESS_TOKEN or UAP_TIKTOK_SEND_URL for outbound",
            "to": user_id,
            "backend": "tiktok",
        }
    body = json.dumps(
        {
            "open_id": user_id,
            "text": text[:500],
            "message_type": "text",
        }
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
    }
    if access:
        headers["Access-Token"] = access
        headers["Authorization"] = f"Bearer {access}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        return {"ok": False, "error": f"TikTok HTTP {e.code}: {detail}", "to": user_id}
    except Exception as e:
        return {"ok": False, "error": str(e), "to": user_id}
    return {"ok": True, "to": user_id, "response": data, "backend": "tiktok"}


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    return (f"{answer}\n\n— ADQA DQS {dqs} · {guardian}")[:500]
