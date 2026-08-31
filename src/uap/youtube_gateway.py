"""YouTube gateway — comment poll + PubSubHubbub webhook relay."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def youtube_enabled() -> bool:
    return bool(_api_key())


def _api_key() -> str:
    return os.environ.get("UAP_YOUTUBE_API_KEY", "").strip() or os.environ.get(
        "YOUTUBE_API_KEY", ""
    ).strip()


def _oauth_token() -> str:
    return os.environ.get("UAP_YOUTUBE_OAUTH_TOKEN", "").strip()


def poll_channel_ids() -> list[str]:
    raw = os.environ.get("UAP_YOUTUBE_POLL_CHANNELS", "")
    ids = [x.strip() for x in raw.split(",") if x.strip()]
    if ids:
        return ids
    single = os.environ.get("UAP_YOUTUBE_CHANNEL_ID", "").strip() or os.environ.get(
        "YOUTUBE_CHANNEL_ID", ""
    ).strip()
    return [single] if single else []


def _auth_headers() -> dict[str, str]:
    headers = {"User-Agent": "NARNA-Agent (https://narna.org, 0.2)"}
    token = _oauth_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def list_recent_comments(
    video_id: str, *, page_token: str | None = None
) -> tuple[list[dict[str, Any]], str | None]:
    key = _api_key()
    if not key:
        return [], None
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": "5",
        "order": "time",
        "textFormat": "plainText",
        "key": key,
    }
    if page_token:
        params["pageToken"] = page_token
    url = "https://www.googleapis.com/youtube/v3/commentThreads?" + urllib.parse.urlencode(
        params
    )
    req = urllib.request.Request(url, headers=_auth_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = list(data.get("items") or [])
    return items, data.get("nextPageToken")


def list_uploads(channel_id: str, *, max_results: int = 3) -> list[str]:
    key = _api_key()
    if not key:
        return []
    params = {
        "part": "contentDetails",
        "channelId": channel_id,
        "maxResults": str(max_results),
        "order": "date",
        "type": "video",
        "key": key,
    }
    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_auth_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out: list[str] = []
    for item in data.get("items") or []:
        vid = ((item.get("id") or {}).get("videoId") or "").strip()
        if vid:
            out.append(vid)
    return out


def reply_youtube_comment(parent_id: str, text: str) -> dict[str, Any]:
    token = _oauth_token()
    key = _api_key()
    if not token:
        raise RuntimeError("UAP_YOUTUBE_OAUTH_TOKEN required to reply to comments")
    params = {"part": "snippet", "key": key} if key else {"part": "snippet"}
    url = "https://www.googleapis.com/youtube/v3/comments?" + urllib.parse.urlencode(params)
    body = json.dumps(
        {
            "snippet": {
                "parentId": parent_id,
                "textOriginal": text[:10000],
            }
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            **(_auth_headers()),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_youtube_webhook(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Return (author_channel_id, text, comment_thread_id) from relay or XML-parsed JSON."""
    author = str(payload.get("authorChannelId") or payload.get("author") or "").strip()
    text = str(payload.get("text") or payload.get("comment") or "").strip()
    thread = str(payload.get("commentThreadId") or payload.get("thread_id") or "").strip() or None
    if author and text:
        return author, text, thread
    return None, None, None


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    dqs = out.get("dqs")
    return (f"{answer}\n\n— ADQA DQS {dqs}")[:10000]
