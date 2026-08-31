"""Facebook Messenger gateway — Graph API webhooks."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def facebook_enabled() -> bool:
    return bool(_page_token())


def _page_token() -> str:
    return os.environ.get("UAP_FB_PAGE_ACCESS_TOKEN", "").strip() or os.environ.get(
        "FB_PAGE_ACCESS_TOKEN", ""
    ).strip()


def _graph_version() -> str:
    return os.environ.get("UAP_FB_GRAPH_VERSION", "v21.0").strip() or "v21.0"


def verify_webhook(mode: str | None, token: str | None, challenge: str | None) -> str | None:
    expected = os.environ.get("UAP_FB_VERIFY_TOKEN", "").strip()
    if mode == "subscribe" and token and expected and token == expected:
        return challenge or ""
    return None


def send_facebook_message(psid: str, text: str) -> dict[str, Any]:
    page_token = _page_token()
    if not page_token:
        raise RuntimeError("UAP_FB_PAGE_ACCESS_TOKEN not set")
    url = (
        f"https://graph.facebook.com/{_graph_version()}/me/messages"
        f"?access_token={urllib.parse.quote(page_token)}"
    )
    body = json.dumps(
        {
            "recipient": {"id": psid},
            "message": {"text": text[:2000]},
            "messaging_type": "RESPONSE",
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


def extract_facebook_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Return (psid, text) from Messenger webhook object."""
    for entry in payload.get("entry") or []:
        for event in entry.get("messaging") or []:
            sender = (event.get("sender") or {}).get("id")
            message = event.get("message") or {}
            if message.get("is_echo"):
                continue
            text = str(message.get("text") or "").strip()
            if sender and text:
                return str(sender), text
    # Flat relay
    psid = str(payload.get("psid") or payload.get("sender") or "").strip()
    text = str(payload.get("text") or payload.get("message") or "").strip()
    if psid and text:
        return psid, text
    return None, None


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    return (f"{answer}\n\n— ADQA DQS {dqs} · {out.get('guardian')}")[:2000]
