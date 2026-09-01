"""Desktop → NARNA Cloud API client (Pro sync, plan status)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def default_cloud_url() -> str:
    import os

    return (os.environ.get("NARNA_CLOUD_URL") or "https://api.narna.org").rstrip("/")


def _request(
    *,
    method: str,
    path: str,
    api_key: str,
    base_url: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    url = f"{(base_url or default_cloud_url()).rstrip('/')}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "narna-desktop/1.0",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {"ok": True}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:800]
        try:
            parsed = json.loads(detail)
            msg = parsed.get("detail") or detail
        except Exception:
            msg = detail
        return {"ok": False, "status": e.code, "error": msg}


def cloud_sync_status(*, api_key: str, base_url: str | None = None) -> dict[str, Any]:
    return _request(method="GET", path="/v1/sync/status", api_key=api_key, base_url=base_url)


def cloud_billing_status(*, api_key: str, base_url: str | None = None) -> dict[str, Any]:
    return _request(method="GET", path="/v1/billing/status", api_key=api_key, base_url=base_url)


def cloud_sync_push(
    *,
    api_key: str,
    bundle: dict[str, Any],
    base_url: str | None = None,
) -> dict[str, Any]:
    return _request(
        method="POST",
        path="/v1/sync/push",
        api_key=api_key,
        base_url=base_url,
        body=bundle,
        timeout=120,
    )


def cloud_sync_pull(
    *,
    api_key: str,
    device_id: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    q = f"?deviceId={device_id}" if device_id else ""
    return _request(method="GET", path=f"/v1/sync/pull{q}", api_key=api_key, base_url=base_url)


def collect_sync_bundle(workspace: Path, *, device_id: str) -> dict[str, Any]:
    """Package local Decision Memory + traces for cloud backup."""
    from uap.agent_memory_fts import AgentMemoryFTS
    from uap.agent_memory_md import AgentMemoryMd
    from uap.decision_trace import DecisionTraceStore

    md = AgentMemoryMd(workspace)
    fts = AgentMemoryFTS(workspace)
    traces = DecisionTraceStore(workspace).list_traces(limit=50)
    lessons = fts.recent_lessons(limit=100) if hasattr(fts, "recent_lessons") else []

    return {
        "deviceId": device_id,
        "memoryMd": md.read_memory(max_chars=50_000),
        "userMd": md.read_user(max_chars=20_000),
        "projectMd": md.read_project(max_chars=20_000),
        "lessons": lessons,
        "traces": traces,
        "profile": fts.get_profile(),
    }


def apply_sync_pull(workspace: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    """Merge cloud backup into local workspace (append-only lessons, LWW markdown)."""
    from uap.agent_memory_fts import AgentMemoryFTS
    from uap.agent_memory_md import AgentMemoryMd
    from uap.decision_trace import DecisionTraceStore

    applied: dict[str, Any] = {"lessons": 0, "traces": 0, "memoryUpdated": False}
    md = AgentMemoryMd(workspace)

    if bundle.get("memoryMd"):
        existing = md.read_memory(max_chars=100_000)
        incoming = str(bundle["memoryMd"])
        if incoming.strip() and incoming.strip() != existing.strip():
            md.memory_path.write_text(incoming[:50_000], encoding="utf-8")
            applied["memoryUpdated"] = True

    fts = AgentMemoryFTS(workspace)
    for lesson in bundle.get("lessons") or []:
        if not isinstance(lesson, dict):
            continue
        text = str(lesson.get("lesson") or lesson.get("content") or lesson.get("text") or "").strip()
        if text:
            fts.index_lesson(text, dqs=int(lesson.get("dqs") or 0), meta=lesson)
            applied["lessons"] += 1

    store = DecisionTraceStore(workspace)
    for row in bundle.get("traces") or []:
        if not isinstance(row, dict):
            continue
        tid = str(row.get("traceId") or "")
        if not tid:
            continue
        path = store._path(tid)
        if not path.exists():
            path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
            applied["traces"] += 1

    for key, val in (bundle.get("profile") or {}).items():
        if key and val:
            fts.set_profile(str(key), str(val))

    return applied
