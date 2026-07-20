"""Moltbook API client — agent-only social network."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://www.moltbook.com/api/v1"
CREDENTIALS_PATH = Path.home() / ".config" / "moltbook" / "credentials.json"


def _resolve_default_credentials_path() -> Path | None:
    try:
        try:
            from .credentials import resolve_credentials
        except ImportError:
            from credentials import resolve_credentials

        _, path = resolve_credentials()
        return path
    except Exception:
        return None


def load_credentials(path: Path | None = None) -> dict[str, str]:
    p = path or CREDENTIALS_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"Moltbook credentials not found at {p}. "
            "Register via POST /agents/register and save api_key + agent_name."
        )
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("credentials.json must be a JSON object")
    api_key = str(data.get("api_key") or data.get("apiKey") or "").strip()
    if not api_key:
        raise ValueError("credentials.json missing api_key")
    return {
        "api_key": api_key,
        "agent_name": str(data.get("agent_name") or data.get("agentName") or ""),
    }


def save_credentials(
    api_key: str,
    agent_name: str,
    *,
    path: Path | None = None,
) -> Path:
    p = path or CREDENTIALS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {"api_key": api_key, "agent_name": agent_name}
    p.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return p


class MoltbookClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        credentials_path: Path | None = None,
        require_auth: bool = False,
    ) -> None:
        self.base_url = (base_url or os.environ.get("MOLTBOOK_API_BASE") or DEFAULT_BASE).rstrip("/")
        self.api_key = (api_key or os.environ.get("MOLTBOOK_API_KEY") or "").strip()
        self.agent_name = ""
        if not self.api_key and (require_auth or credentials_path is not None):
            creds = load_credentials(credentials_path)
            self.api_key = creds["api_key"]
            self.agent_name = creds["agent_name"]
        elif not self.api_key:
            path = credentials_path or _resolve_default_credentials_path() or CREDENTIALS_PATH
            try:
                creds = load_credentials(path)
                self.api_key = creds["api_key"]
                self.agent_name = creds["agent_name"]
            except FileNotFoundError:
                pass

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if auth:
            if not self.api_key:
                raise ValueError("Moltbook API key required. Set MOLTBOOK_API_KEY or credentials.json.")
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Moltbook HTTP {exc.code}: {detail}") from exc

    def browse_hot(self, limit: int = 5) -> dict[str, Any]:
        return self._request("GET", f"/posts?sort=hot&limit={int(limit)}")

    def browse_new(self, limit: int = 5) -> dict[str, Any]:
        return self._request("GET", f"/posts?sort=new&limit={int(limit)}")

    def get_post(self, post_id: str) -> dict[str, Any]:
        return self._request("GET", f"/posts/{post_id}")

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/agents/me", auth=True)

    def home(self) -> dict[str, Any]:
        return self._request("GET", "/home", auth=True)

    def notifications(self) -> dict[str, Any]:
        return self._request("GET", "/notifications", auth=True)

    def create_post(
        self,
        title: str,
        content: str,
        *,
        submolt_name: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"title": title, "content": content}
        if submolt_name:
            body["submolt_name"] = submolt_name
        return self._request("POST", "/posts", body=body, auth=True)

    def reply(self, post_id: str, content: str) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/posts/{post_id}/comments",
            body={"content": content},
            auth=True,
        )

    def register_agent(self, name: str, description: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/agents/register",
            body={"name": name, "description": description},
        )

    def test_connection(self) -> dict[str, Any]:
        hot = self.browse_hot(limit=1)
        posts = hot.get("posts") or []
        out: dict[str, Any] = {
            "ok": True,
            "public_feed": bool(posts),
            "sample_title": (posts[0].get("title") if posts else None),
        }
        try:
            me = self.me()
            out["authenticated"] = True
            agent = me.get("agent") or me
            if isinstance(agent, dict):
                out["agent_name"] = agent.get("name")
                out["claimed"] = bool(agent.get("is_claimed"))
        except Exception as exc:
            out["authenticated"] = False
            out["auth_error"] = str(exc)
        return out
