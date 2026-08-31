"""Instagram Messaging gateway — Meta Graph API (Messenger platform)."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def instagram_enabled() -> bool:
    return bool(_page_token())


def _page_token() -> str:
    return os.environ.get("UAP_IG_PAGE_ACCESS_TOKEN", "").strip() or os.environ.get(
        "IG_PAGE_ACCESS_TOKEN", ""
    ).strip()


def _graph_version() -> str:
    return os.environ.get("UAP_IG_GRAPH_VERSION", "v21.0").strip() or "v21.0"


def send_instagram_message(igid: str, text: str) -> dict[str, Any]:
    token = _page_token()
    if not token:
        raise RuntimeError("UAP_IG_PAGE_ACCESS_TOKEN not set")
    url = (
        f"https://graph.facebook.com/{_graph_version()}/me/messages"
        f"?access_token={urllib.parse.quote(token)}"
    )
    body = json.dumps(
        {
            "recipient": {"id": igid},
            "message": {"text": text[:1000]},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_instagram_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    for entry in payload.get("entry") or []:
        for event in entry.get("messaging") or []:
            sender = (event.get("sender") or {}).get("id")
            message = event.get("message") or {}
            if message.get("is_echo"):
                continue
            text = str(message.get("text") or "").strip()
            if sender and text:
                return str(sender), text
    igid = str(payload.get("igid") or payload.get("sender") or "").strip()
    text = str(payload.get("text") or "").strip()
    if igid and text:
        return igid, text
    return None, None


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    return (f"{answer}\n\n— ADQA DQS {out.get('dqs')}")[:1000]
