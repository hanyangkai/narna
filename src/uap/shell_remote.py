"""Remote shell backends — Modal / Daytona / Singularity / Vercel (BYOK HTTP exec)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _post_exec(
    *,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any],
    backend: str,
    timeout: int,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "narna-agent/0.2",
            **headers,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        out = {
            "ok": False,
            "error": f"{backend} HTTP {e.code}: {detail}",
            "backend": backend,
        }
        if extra:
            out.update(extra)
        return out
    except Exception as e:
        out = {"ok": False, "error": str(e), "backend": backend}
        if extra:
            out.update(extra)
        return out

    stdout = str(data.get("stdout") or data.get("output") or data.get("logs") or "")[:8000]
    stderr = str(data.get("stderr") or "")[:2000]
    code = int(
        data.get("exitCode")
        if data.get("exitCode") is not None
        else data.get("exit_code")
        if data.get("exit_code") is not None
        else data.get("code")
        or 0
    )
    result = {
        "ok": code == 0 and data.get("ok", True) is not False,
        "exitCode": code,
        "stdout": stdout,
        "stderr": stderr,
        "backend": backend,
    }
    if extra:
        result.update(extra)
    return result


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
        base = f"https://api.modal.com/v1/apps/{app}/sandboxes/exec"
    return _post_exec(
        url=base,
        headers={"Authorization": f"Bearer {token}"},
        body={"command": command, "timeout": timeout, "cwd": cwd or "/work", "app": app},
        backend="modal",
        timeout=timeout,
        extra={"app": app, "cwd": cwd},
    )


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
    return _post_exec(
        url=url,
        headers={"Authorization": f"Bearer {key}"},
        body={"command": command, "timeout": timeout, "cwd": cwd or "/work"},
        backend="daytona",
        timeout=timeout,
        extra={"workspaceId": ws_id, "cwd": cwd},
    )


def exec_singularity(*, command: str, timeout: int = 15, cwd: str | None = None) -> dict[str, Any]:
    """POST to BYOK Singularity / Apptainer exec bridge.

    Env:
      UAP_SINGULARITY_EXEC_URL — required HTTP bridge endpoint
      UAP_SINGULARITY_TOKEN    — optional Bearer
      UAP_SINGULARITY_IMAGE    — optional image/SIF path hint
    """
    url = (os.environ.get("UAP_SINGULARITY_EXEC_URL") or "").strip()
    if not url:
        return {
            "ok": False,
            "error": "UAP_SINGULARITY_EXEC_URL not set — point at your Singularity exec bridge",
            "backend": "singularity",
        }
    token = (os.environ.get("UAP_SINGULARITY_TOKEN") or "").strip()
    image = (os.environ.get("UAP_SINGULARITY_IMAGE") or "").strip() or None
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body: dict[str, Any] = {"command": command, "timeout": timeout, "cwd": cwd or "/work"}
    if image:
        body["image"] = image
    return _post_exec(
        url=url,
        headers=headers,
        body=body,
        backend="singularity",
        timeout=timeout,
        extra={"image": image, "cwd": cwd},
    )


def exec_vercel(*, command: str, timeout: int = 15, cwd: str | None = None) -> dict[str, Any]:
    """POST to BYOK Vercel Sandbox / custom exec URL.

    Env:
      UAP_VERCEL_EXEC_URL — required
      UAP_VERCEL_TOKEN    — optional Bearer (or VERCEL_TOKEN)
    """
    url = (os.environ.get("UAP_VERCEL_EXEC_URL") or "").strip()
    if not url:
        return {
            "ok": False,
            "error": "UAP_VERCEL_EXEC_URL not set — point at your Vercel sandbox exec bridge",
            "backend": "vercel",
        }
    token = (
        os.environ.get("UAP_VERCEL_TOKEN") or os.environ.get("VERCEL_TOKEN") or ""
    ).strip()
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _post_exec(
        url=url,
        headers=headers,
        body={"command": command, "timeout": timeout, "cwd": cwd or "/work"},
        backend="vercel",
        timeout=timeout,
        extra={"cwd": cwd},
    )
