"""Resolve Moltbook credentials from OpenClaw workspace or standard config."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path.home() / ".config" / "moltbook" / "credentials.json"
OPENCLAW_WORKSPACE = Path.home() / ".openclaw" / "workspace-dev" / "moltbook_credentials.json"


def _read_cred_file(path: Path) -> dict[str, str] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    api_key = str(data.get("api_key") or data.get("apiKey") or "").strip()
    if not api_key:
        return None
    return {
        "api_key": api_key,
        "agent_name": str(data.get("agent_name") or data.get("agentName") or data.get("name") or ""),
        "path": str(path),
    }


def credential_candidates() -> list[Path]:
    paths: list[Path] = []
    env_path = os.environ.get("MOLTBOOK_CREDENTIALS_PATH", "").strip()
    if env_path:
        paths.append(Path(env_path))
    ws = os.environ.get("OPENCLAW_WORKSPACE", "").strip()
    if ws:
        paths.append(Path(ws) / "moltbook_credentials.json")
    paths.append(OPENCLAW_WORKSPACE)
    paths.append(DEFAULT_CONFIG)
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p.resolve()) if p.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def resolve_credentials(*, prefer_claimed: bool = True) -> tuple[dict[str, str], Path | None]:
    """Pick the best credentials file. Prefer claimed OpenClaw workspace key."""
    if os.environ.get("MOLTBOOK_API_KEY", "").strip():
        return (
            {
                "api_key": os.environ["MOLTBOOK_API_KEY"].strip(),
                "agent_name": os.environ.get("MOLTBOOK_AGENT_NAME", ""),
                "path": "env",
            },
            None,
        )

    loaded: list[tuple[dict[str, str], Path]] = []
    for path in credential_candidates():
        creds = _read_cred_file(path)
        if creds:
            loaded.append((creds, path))

    if not loaded:
        raise FileNotFoundError(
            "No Moltbook credentials found. Set MOLTBOOK_API_KEY or create "
            "~/.openclaw/workspace-dev/moltbook_credentials.json"
        )

    if not prefer_claimed or len(loaded) == 1:
        creds, path = loaded[0]
        return creds, path

    from client import MoltbookClient

    claimed: list[tuple[dict[str, str], Path]] = []
    for creds, path in loaded:
        try:
            me = MoltbookClient(api_key=creds["api_key"]).me()
            agent = me.get("agent") if isinstance(me.get("agent"), dict) else me
            if isinstance(agent, dict) and agent.get("is_claimed"):
                name = str(agent.get("name") or creds.get("agent_name") or "")
                picked = {**creds, "agent_name": name}
                claimed.append((picked, path))
        except Exception:
            continue
    if claimed:
        return claimed[0]
    creds, path = loaded[0]
    return creds, path


def sync_primary_credentials(target: Path | None = None) -> Path:
    """Copy best credentials into ~/.config/moltbook/credentials.json."""
    creds, _ = resolve_credentials()
    target = target or DEFAULT_CONFIG
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "api_key": creds["api_key"],
        "agent_name": creds.get("agent_name") or "",
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target
