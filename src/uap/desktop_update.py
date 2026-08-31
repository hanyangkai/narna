"""Check GitHub Releases for newer NARNA versions (no auto-install)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


def _parse_version(tag: str) -> tuple[int, ...]:
    s = (tag or "").strip().lstrip("vV")
    parts = re.findall(r"\d+", s)
    return tuple(int(p) for p in parts[:4]) if parts else (0,)


def check_update(
    *,
    current: str | None = None,
    repo: str = "hanyangkai/narna",
) -> dict[str, Any]:
    """Compare installed version to latest GitHub release tag."""
    if current is None:
        try:
            from narna import __version__ as current
        except Exception:
            current = "0.0.0"
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "narna-agent-update-check",
        },
        method="GET",
    )
    token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {
            "ok": False,
            "current": current,
            "error": f"GitHub HTTP {e.code}",
        }
    except Exception as e:
        return {"ok": False, "current": current, "error": str(e)[:200]}

    tag = str(data.get("tag_name") or "").strip()
    html = str(data.get("html_url") or f"https://github.com/{repo}/releases/latest")
    assets = [
        {
            "name": a.get("name"),
            "url": a.get("browser_download_url"),
            "size": a.get("size"),
        }
        for a in (data.get("assets") or [])
        if isinstance(a, dict)
    ]
    newer = _parse_version(tag) > _parse_version(str(current))
    return {
        "ok": True,
        "current": current,
        "latest": tag.lstrip("v"),
        "tag": tag,
        "updateAvailable": newer,
        "url": html,
        "assets": assets,
        "publishedAt": data.get("published_at"),
    }
