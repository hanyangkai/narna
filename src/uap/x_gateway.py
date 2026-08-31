"""X (Twitter) gateway — Account Activity API webhooks + v2 DM/reply."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from typing import Any


def x_enabled() -> bool:
    return bool(_bearer())


def _bearer() -> str:
    return os.environ.get("UAP_X_BEARER_TOKEN", "").strip() or os.environ.get(
        "X_BEARER_TOKEN", ""
    ).strip()


def _api_base() -> str:
    return os.environ.get("UAP_X_API_BASE", "https://api.twitter.com").rstrip("/")


def verify_crc(crc_token: str) -> str:
    """Respond to X Account Activity CRC check."""
    secret = os.environ.get("UAP_X_API_SECRET", "").strip() or os.environ.get(
        "X_API_SECRET", ""
    ).strip()
    if not secret:
        raise RuntimeError("UAP_X_API_SECRET required for CRC")
    digest = hmac.new(secret.encode("utf-8"), crc_token.encode("utf-8"), hashlib.sha256)
    return "sha256=" + base64.b64encode(digest.digest()).decode("utf-8")


def send_x_dm(recipient_id: str, text: str) -> dict[str, Any]:
    token = _bearer()
    if not token:
        raise RuntimeError("UAP_X_BEARER_TOKEN not set")
    url = f"{_api_base()}/2/dm_conversations/with/{recipient_id}/messages"
    body = json.dumps({"text": text[:10000]}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def reply_to_tweet(tweet_id: str, text: str) -> dict[str, Any]:
    token = _bearer()
    if not token:
        raise RuntimeError("UAP_X_BEARER_TOKEN not set")
    url = f"{_api_base()}/2/tweets"
    body = json.dumps({"text": text[:280], "reply": {"in_reply_to_tweet_id": tweet_id}}).encode(
        "utf-8"
    )
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_x_event(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (external_id, text, reply_target).

    Supports direct_message_events and tweet_create_events shapes.
    """
    for event in payload.get("direct_message_events") or []:
        msg = event.get("message_create") or {}
        target = (msg.get("target") or {}).get("recipient_id")
        sender = event.get("sender_id") or (msg.get("sender_id"))
        text = str((msg.get("message_data") or {}).get("text") or "").strip()
        if sender and text:
            return str(sender), text, None

    for event in payload.get("tweet_create_events") or []:
        text = str(event.get("text") or "").strip()
        author = event.get("user") or {}
        if author.get("id_str") and text and not text.startswith("RT @"):
            in_reply = (event.get("in_reply_to_status_id_str") or "").strip()
            mention_bot = os.environ.get("UAP_X_BOT_USER_ID", "").strip()
            if mention_bot and f"@{mention_bot}" not in text and not in_reply:
                continue
            return str(author.get("id_str")), text, str(event.get("id_str") or "") or None

    # Flat webhook relay: { from, text, tweetId? }
    frm = str(payload.get("from") or payload.get("sender_id") or "").strip()
    text = str(payload.get("text") or payload.get("message") or "").strip()
    tweet_id = str(payload.get("tweetId") or payload.get("tweet_id") or "").strip() or None
    if frm and text:
        return frm, text, tweet_id
    return None, None, None


def deliver_x_reply(*, to: str, text: str, tweet_id: str | None = None) -> dict[str, Any]:
    if tweet_id:
        return reply_to_tweet(tweet_id, text)
    return send_x_dm(to, text)


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    guardian = out.get("guardian")
    suffix = f"\n\n— ADQA DQS {dqs}"
    if guardian:
        suffix += f" · {guardian}"
    limit = 280 if not os.environ.get("UAP_X_DM_MODE") else 10000
    return (answer + suffix)[:limit]


def poll_mentions(*, since_id: str | None = None, max_results: int = 5) -> list[dict[str, Any]]:
    """Long-poll fallback: recent mentions of the authenticated user (X API v2).

    Env:
      UAP_X_BEARER_TOKEN — required
      UAP_X_USER_ID — optional; if missing, resolve via /2/users/me
    """
    token = _bearer()
    if not token:
        return []
    user_id = (
        os.environ.get("UAP_X_USER_ID", "").strip()
        or os.environ.get("X_USER_ID", "").strip()
        or _resolve_me_id(token)
    )
    if not user_id:
        return []
    params = f"max_results={max(5, min(max_results, 100))}&tweet.fields=author_id,text,created_at"
    if since_id:
        params += f"&since_id={since_id}"
    url = f"{_api_base()}/2/users/{user_id}/mentions?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    rows = []
    for tw in data.get("data") or []:
        tid = str(tw.get("id") or "")
        text = str(tw.get("text") or "").strip()
        author = str(tw.get("author_id") or "")
        if tid and text:
            rows.append({"id": tid, "text": text, "author_id": author})
    return rows


def _resolve_me_id(token: str) -> str:
    url = f"{_api_base()}/2/users/me"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "NARNA-Agent (https://narna.org, 0.2)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return str((data.get("data") or {}).get("id") or "")
    except Exception:
        return ""


def x_poll_ready() -> bool:
    return bool(_bearer()) and str(os.environ.get("UAP_X_POLL") or "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
