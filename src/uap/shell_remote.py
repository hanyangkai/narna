"""Remote shell backends — Modal + Daytona stubs (Hermes gap P4). Opt-in BYOK only."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def exec_modal(*, command: str, timeout: int = 15, cwd: str | None = None) -> dict[str, Any]:
    """POST allowlisted command to Modal sandbox exec endpoint.

    Env:
      UAP_MODAL_TOKEN   — Bearer token (required)
      UAP_MODAL_APP     — app / sandbox id (required)
      UAP_MODAL_EXEC_URL — override URL (optional)
    """
    token = (os.environ.get("UAP_MODAL_TOKEN") or "").strip()
    app = (os.environ.get("UAP_MODAL_APP") or "").strip()
    if not token:
        return {"ok": False, "error": "UAP_MODAL_TOKEN not set", "backend": "modal"}
    if not app:
        return {"ok": False, "error": "UAP_MODAL_APP not set", "backend": "modal"}
    base = (os.environ.get("UAP_MODAL_EXEC_URL") or "").strip()
    if not base:
        # Stub default — override with UAP_MODAL_EXEC_URL for real Modal endpoints
        base = f"https://api.modal.com/v1/apps/{app}/sandboxes/exec"
    body = json.dumps(
        {
            "command": command,
            "timeout": timeout,
            "cwd": cwd or "/work",
            "app": app,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        base,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "narna-agent/0.2",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        return {
            "ok": False,
            "error": f"modal HTTP {e.code}: {detail}",
            "backend": "modal",
            "app": app,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "backend": "modal", "app": app}

    stdout = str(data.get("stdout") or data.get("output") or "")[:8000]
    stderr = str(data.get("stderr") or "")[:2000]
    code = int(data.get("exitCode") if data.get("exitCode") is not None else data.get("exit_code") or 0)
    return {
        "ok": code == 0 and data.get("ok", True) is not False,
        "exitCode": code,
        "stdout": stdout,
        "stderr": stderr,
        "backend": "modal",
        "app": app,
        "cwd": cwd,
    }


def exec_daytona(*, command: str, timeout: int = 15, cwd: str | None = None) -> dict[str, Any]:
    """POST allowlisted command to Daytona workspace exec API.

    Env:
      UAP_DAYTONA_API_KEY      — required
      UAP_DAYTONA_WORKSPACE_ID — required
      UAP_DAYTONA_API_URL      — default https://api.daytona.io
    """
    key = (os.environ.get("UAP_DAYTONA_API_KEY") or "").strip()
    ws_id = (os.environ.get("UAP_DAYTONA_WORKSPACE_ID") or "").strip()
    if not key:
        return {"ok": False, "error": "UAP_DAYTONA_API_KEY not set", "backend": "daytona"}
    if not ws_id:
        return {"ok": False, "error": "UAP_DAYTONA_WORKSPACE_ID not set", "backend": "daytona"}
    api = (os.environ.get("UAP_DAYTONA_API_URL") or "https://api.daytona.io").rstrip("/")
    url = f"{api}/workspace/{ws_id}/exec"
    body = json.dumps({"command": command, "timeout": timeout, "cwd": cwd or "/work"}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "narna-agent/0.2",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        return {
            "ok": False,
            "error": f"daytona HTTP {e.code}: {detail}",
            "backend": "daytona",
            "workspaceId": ws_id,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "backend": "daytona", "workspaceId": ws_id}

    stdout = str(data.get("stdout") or data.get("output") or "")[:8000]
    stderr = str(data.get("stderr") or "")[:2000]
    code = int(data.get("exitCode") if data.get("exitCode") is not None else data.get("exit_code") or 0)
    return {
        "ok": code == 0 and data.get("ok", True) is not False,
        "exitCode": code,
        "stdout": stdout,
        "stderr": stderr,
        "backend": "daytona",
        "workspaceId": ws_id,
        "cwd": cwd,
    }
