"""Moltbook automation — queue posts, check notifications, respect rate limits."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .client import MoltbookClient
except ImportError:
    from client import MoltbookClient
try:
    from .credentials import resolve_credentials
except ImportError:
    from credentials import resolve_credentials

DEFAULT_RATE_LIMIT_SEC = 30 * 60
STATE_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def default_workspace() -> Path:
    return Path.home() / ".openclaw" / "workspace-dev"


def state_path(workspace: Path | None = None) -> Path:
    return (workspace or default_workspace()) / "moltbook_state.json"


def queue_path(workspace: Path | None = None) -> Path:
    return (workspace or default_workspace()) / "moltbook_queue.json"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": STATE_VERSION, "last_post_at": None, "last_run_at": None, "posted": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {"version": STATE_VERSION}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def load_queue(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        posts = data.get("posts")
        if isinstance(posts, list):
            return [row for row in posts if isinstance(row, dict)]
    return []


def save_queue(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"posts": items}, indent=2) + "\n", encoding="utf-8")


def seconds_since_post(state: dict[str, Any]) -> float | None:
    last = _parse_ts(str(state.get("last_post_at") or ""))
    if not last:
        return None
    return (datetime.now(timezone.utc) - last).total_seconds()


def run_automation(
    *,
    workspace: Path | None = None,
    dry_run: bool = False,
    rate_limit_sec: int = DEFAULT_RATE_LIMIT_SEC,
) -> dict[str, Any]:
    ws = workspace or default_workspace()
    creds, cred_path = resolve_credentials()
    client = MoltbookClient(api_key=creds["api_key"])
    me = client.me()
    agent = me.get("agent") if isinstance(me.get("agent"), dict) else me
    agent_name = agent.get("name") if isinstance(agent, dict) else creds.get("agent_name")
    is_claimed = bool(agent.get("is_claimed")) if isinstance(agent, dict) else False

    st_path = state_path(ws)
    q_path = queue_path(ws)
    state = load_state(st_path)
    queue = load_queue(q_path)
    state["last_run_at"] = _now()

    result: dict[str, Any] = {
        "ok": True,
        "agent": agent_name,
        "claimed": is_claimed,
        "credentials": str(cred_path or creds.get("path") or ""),
        "workspace": str(ws),
        "queue_pending": len([q for q in queue if q.get("status") != "posted"]),
        "actions": [],
    }

    try:
        home = client.home()
        result["notifications"] = {
            "unread": home.get("unread_notifications") or home.get("unreadNotifications"),
            "summary": home.get("summary"),
        }
        result["actions"].append("checked_home")
    except Exception as exc:
        result["notifications_error"] = str(exc)

    elapsed = seconds_since_post(state)
    can_post = is_claimed and (elapsed is None or elapsed >= rate_limit_sec)
    if not is_claimed:
        result["actions"].append("skip_post_unclaimed")
    elif elapsed is not None and elapsed < rate_limit_sec:
        result["actions"].append("skip_post_rate_limit")
        result["retry_post_in_sec"] = int(rate_limit_sec - elapsed)

    pending = [q for q in queue if q.get("status") != "posted"]
    if can_post and pending:
        item = pending[0]
        title = str(item.get("title") or "").strip()
        content = str(item.get("content") or "").strip()
        submolt = item.get("submolt_name") or item.get("submolt")
        if not title or not content:
            result["actions"].append("skip_post_invalid_queue_item")
        elif dry_run:
            result["actions"].append("dry_run_would_post")
            result["next_post"] = {"title": title, "submolt": submolt}
        else:
            post = client.create_post(title, content, submolt_name=submolt)
            post_id = post.get("id") or (post.get("post") or {}).get("id")
            item["status"] = "posted"
            item["posted_at"] = _now()
            item["post_id"] = post_id
            state["last_post_at"] = _now()
            state.setdefault("posted", []).append(
                {"title": title, "post_id": post_id, "posted_at": item["posted_at"]}
            )
            save_queue(q_path, queue)
            result["actions"].append("posted")
            result["posted"] = {"title": title, "post_id": post_id}

    save_state(st_path, state)
    return result
