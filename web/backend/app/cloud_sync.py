"""Cloud sync — Pro backup of Desktop Decision Memory + traces."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .billing import normalize_plan, now_utc, plan_sync_push_cap, reset_if_new_period
from .models import Organization
from .plan_features import plan_features_payload, require_feature
from .tenants import tenant_workspace

SYNC_DIR = "cloud-sync"


def _sync_root(org: Organization) -> Path:
    root = tenant_workspace(org.id) / ".uap" / SYNC_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def _meta_path(org: Organization) -> Path:
    return _sync_root(org) / "sync_meta.json"


def _load_meta(org: Organization) -> dict[str, Any]:
    p = _meta_path(org)
    if not p.exists():
        return {"pushesInPeriod": 0, "periodStart": None, "devices": {}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"pushesInPeriod": 0, "periodStart": None, "devices": {}}


def _save_meta(org: Organization, meta: dict[str, Any]) -> None:
    _meta_path(org).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def _reset_meta_period(org: Organization, meta: dict[str, Any]) -> dict[str, Any]:
    now = now_utc()
    ps = org.period_start_at
    if ps and reset_if_new_period(period_start_at=ps, now=now):
        meta["pushesInPeriod"] = 0
    meta["periodStart"] = ps.isoformat() if ps else None
    return meta


def sync_status(*, org: Organization) -> dict[str, Any]:
    meta = _reset_meta_period(org, _load_meta(org))
    devices = meta.get("devices") or {}
    return {
        "ok": True,
        **plan_features_payload(org.plan),
        "lastPushAt": meta.get("lastPushAt"),
        "lastPullAt": meta.get("lastPullAt"),
        "pushesInPeriod": int(meta.get("pushesInPeriod") or 0),
        "pushLimit": plan_sync_push_cap(org.plan),
        "deviceCount": len(devices),
        "devices": [
            {"deviceId": k, **(v if isinstance(v, dict) else {})} for k, v in devices.items()
        ],
    }


def sync_push(
    *,
    org: Organization,
    db: Session,
    device_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    require_feature(org, "cloud_sync")
    cap = plan_sync_push_cap(org.plan)
    meta = _reset_meta_period(org, _load_meta(org))
    used = int(meta.get("pushesInPeriod") or 0)
    if cap is not None and used >= cap:
        raise HTTPException(
            status_code=402,
            detail=f"Cloud sync push limit reached ({cap}/mo) — upgrade or wait for next period",
        )

    did = (device_id or "unknown").strip()[:64]
    root = _sync_root(org)
    device_dir = root / "devices" / did
    device_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    bundle = {
        "deviceId": did,
        "orgId": org.id,
        "plan": normalize_plan(org.plan),
        "syncedAt": now,
        "memoryMd": payload.get("memoryMd"),
        "userMd": payload.get("userMd"),
        "projectMd": payload.get("projectMd"),
        "lessons": payload.get("lessons") or [],
        "traces": payload.get("traces") or [],
        "profile": payload.get("profile") or {},
    }
    (device_dir / "latest.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (root / "latest.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    devices = meta.get("devices") or {}
    devices[did] = {
        "lastPushAt": now,
        "lessonCount": len(bundle["lessons"]),
        "traceCount": len(bundle["traces"]),
    }
    meta["devices"] = devices
    meta["lastPushAt"] = now
    meta["pushesInPeriod"] = used + 1
    _save_meta(org, meta)

    return {
        "ok": True,
        "deviceId": did,
        "syncedAt": now,
        "pushesInPeriod": meta["pushesInPeriod"],
        "pushLimit": cap,
        "lessonCount": len(bundle["lessons"]),
        "traceCount": len(bundle["traces"]),
    }


def sync_pull(*, org: Organization, device_id: str | None = None) -> dict[str, Any]:
    require_feature(org, "cloud_sync")
    root = _sync_root(org)
    meta = _load_meta(org)
    path = root / "latest.json"
    if device_id:
        alt = root / "devices" / device_id.strip()[:64] / "latest.json"
        if alt.is_file():
            path = alt
    if not path.is_file():
        return {
            "ok": True,
            "empty": True,
            "memoryMd": None,
            "userMd": None,
            "projectMd": None,
            "lessons": [],
            "traces": [],
            "profile": {},
            "lastPushAt": None,
        }
    bundle = json.loads(path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    meta["lastPullAt"] = now
    _save_meta(org, meta)
    return {
        "ok": True,
        "empty": False,
        "memoryMd": bundle.get("memoryMd"),
        "userMd": bundle.get("userMd"),
        "projectMd": bundle.get("projectMd"),
        "lessons": bundle.get("lessons") or [],
        "traces": bundle.get("traces") or [],
        "profile": bundle.get("profile") or {},
        "lastPushAt": bundle.get("syncedAt"),
        "syncedAt": bundle.get("syncedAt"),
    }
