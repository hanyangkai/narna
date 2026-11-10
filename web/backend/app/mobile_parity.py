"""MausBot/GrokBot parity APIs for NARNA mobile companion.

Adds: cross-bot inbox, routines, voice session stubs, remote access config,
connected apps, and push device registration.
"""

from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .models import ApprovalRequest, MobileDevice

router = APIRouter()

# In-memory stores (persist later via Redis/DB if needed)
_ROUTINES: dict[str, dict[str, Any]] = {}
_VOICE_SESSIONS: dict[str, dict[str, Any]] = {}
_REMOTE_CONFIG: dict[int, dict[str, Any]] = {}
_CONNECTED_APPS: dict[int, dict[str, dict[str, Any]]] = {}
_PUSH_DEVICES: dict[str, dict[str, Any]] = {}

SUPPORTED_APPS = ("gmail", "slack", "github", "notion", "linear")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_mobile_auth(mobile_token: str, db: Session) -> dict[str, Any]:
    if not mobile_token:
        raise HTTPException(status_code=401, detail="missing mobile token")
    device = db.query(MobileDevice).filter(MobileDevice.mobile_token == mobile_token).first()
    if device is None:
        raise HTTPException(status_code=401, detail="Invalid or expired mobile token")
    if getattr(device, "expires_at", None) and _now() > device.expires_at:
        raise HTTPException(status_code=401, detail="Mobile token expired")
    return {
        "org_id": device.org_id,
        "device_name": device.device_name,
        "platform": device.platform,
        "mobile_token": mobile_token,
    }


# ── Models ──


class InboxItem(BaseModel):
    item_id: str
    kind: str  # approval | message | bot_status
    bot_id: str
    title: str
    body: str
    action_type: str | None = None
    created_at: str
    status: str = "pending"


class RoutineCreate(BaseModel):
    name: str
    cron: str = "0 9 * * *"
    bot_id: str = "bot_1"
    prompt: str = "Run morning digest"
    enabled: bool = True


class RoutineInfo(BaseModel):
    routine_id: str
    name: str
    cron: str
    bot_id: str
    prompt: str
    enabled: bool
    last_run_at: str | None = None
    created_at: str


class VoiceStartRequest(BaseModel):
    bot_id: str = "bot_1"
    openai_api_key: str | None = None


class VoiceSession(BaseModel):
    session_id: str
    bot_id: str
    status: str
    started_at: str
    note: str


class RemoteConfigUpdate(BaseModel):
    mode: str = "local"  # local | tailscale | custom
    host: str | None = None
    base_url: str | None = None


class PushRegisterRequest(BaseModel):
    platform: str  # ios | android
    device_token: str
    device_name: str | None = None


class ConnectedAppAction(BaseModel):
    account_label: str | None = None


# ── Inbox ──


@router.get("/v1/mobile/inbox")
def get_inbox(mobile_token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Cross-bot inbox: pending approvals + waiting bots (MausBot-style)."""
    auth = _get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]

    items: list[InboxItem] = []

    approvals = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.org_id == org_id, ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.created_at.desc())
        .limit(50)
        .all()
    )
    for a in approvals:
        items.append(
            InboxItem(
                item_id=a.approval_id,
                kind="approval",
                bot_id=a.bot_id,
                title=f"Approval · {a.action_type}",
                body=a.description or "Action needs your decision",
                action_type=a.action_type,
                created_at=(a.created_at or _now()).isoformat(),
                status="pending",
            )
        )

    # Demo waiting items if empty (so UI is not blank in fresh installs)
    if not items:
        items.append(
            InboxItem(
                item_id="inbox_demo_empty",
                kind="message",
                bot_id="system",
                title="Inbox clear",
                body="Approvals and bot questions appear here across all bots.",
                created_at=_now().isoformat(),
                status="info",
            )
        )

    pending = sum(1 for i in items if i.status == "pending" and i.kind == "approval")
    return {
        "ok": True,
        "pending_count": pending,
        "items": [i.dict() for i in items],
    }


# ── Routines ──


@router.get("/v1/mobile/routines")
def list_routines(mobile_token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]
    rows = [r for r in _ROUTINES.values() if r["org_id"] == org_id]
    return {"ok": True, "routines": rows}


@router.post("/v1/mobile/routines")
def create_routine(
    body: RoutineCreate,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> RoutineInfo:
    auth = _get_mobile_auth(mobile_token, db)
    rid = f"rtn_{secrets.token_hex(6)}"
    row = {
        "routine_id": rid,
        "org_id": auth["org_id"],
        "name": body.name,
        "cron": body.cron,
        "bot_id": body.bot_id,
        "prompt": body.prompt,
        "enabled": body.enabled,
        "last_run_at": None,
        "created_at": _now().isoformat(),
    }
    _ROUTINES[rid] = row
    return RoutineInfo(**{k: v for k, v in row.items() if k != "org_id"})


@router.post("/v1/mobile/routines/{routine_id}/toggle")
def toggle_routine(
    routine_id: str,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> RoutineInfo:
    auth = _get_mobile_auth(mobile_token, db)
    row = _ROUTINES.get(routine_id)
    if not row or row["org_id"] != auth["org_id"]:
        raise HTTPException(status_code=404, detail="Routine not found")
    row["enabled"] = not bool(row.get("enabled"))
    return RoutineInfo(**{k: v for k, v in row.items() if k != "org_id"})


@router.delete("/v1/mobile/routines/{routine_id}")
def delete_routine(
    routine_id: str,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    row = _ROUTINES.get(routine_id)
    if not row or row["org_id"] != auth["org_id"]:
        raise HTTPException(status_code=404, detail="Routine not found")
    del _ROUTINES[routine_id]
    return {"ok": True, "deleted": routine_id}


# ── Voice (Live call stub — OpenAI Realtime later) ──


@router.post("/v1/mobile/voice/start", response_model=VoiceSession)
def voice_start(
    body: VoiceStartRequest,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> VoiceSession:
    auth = _get_mobile_auth(mobile_token, db)
    sid = f"voice_{secrets.token_hex(8)}"
    row = {
        "session_id": sid,
        "org_id": auth["org_id"],
        "bot_id": body.bot_id,
        "status": "live",
        "started_at": _now().isoformat(),
        "has_key": bool(body.openai_api_key),
    }
    _VOICE_SESSIONS[sid] = row
    note = (
        "Voice session started. Wire OpenAI Realtime on the client with your own key "
        "(~provider billed). Server tracks session lifecycle only."
        if body.openai_api_key
        else "Voice UI session started without key — add OpenAI key in Settings for live audio."
    )
    return VoiceSession(
        session_id=sid,
        bot_id=body.bot_id,
        status="live",
        started_at=row["started_at"],
        note=note,
    )


@router.post("/v1/mobile/voice/stop")
def voice_stop(
    session_id: str,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    row = _VOICE_SESSIONS.get(session_id)
    if not row or row["org_id"] != auth["org_id"]:
        raise HTTPException(status_code=404, detail="Voice session not found")
    row["status"] = "ended"
    row["ended_at"] = _now().isoformat()
    return {"ok": True, "session_id": session_id, "status": "ended"}


# ── Remote access ──


@router.get("/v1/mobile/remote/status")
def remote_status(mobile_token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    cfg = _REMOTE_CONFIG.get(
        auth["org_id"],
        {
            "mode": "local",
            "host": "127.0.0.1",
            "base_url": "http://127.0.0.1:8765",
            "tailscale_hint": "Install Tailscale on phone + desktop, use MagicDNS name as host",
        },
    )
    return {"ok": True, "remote": cfg}


@router.put("/v1/mobile/remote/config")
def remote_config(
    body: RemoteConfigUpdate,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    mode = (body.mode or "local").lower()
    if mode not in ("local", "tailscale", "custom"):
        raise HTTPException(status_code=422, detail="mode must be local|tailscale|custom")

    if mode == "local":
        base = "http://127.0.0.1:8765"
        host = "127.0.0.1"
    elif mode == "tailscale":
        host = (body.host or "").strip()
        if not host:
            raise HTTPException(status_code=422, detail="Tailscale host required")
        base = body.base_url or f"https://{host}:8765"
    else:
        base = (body.base_url or "").strip()
        if not base.startswith("http"):
            raise HTTPException(status_code=422, detail="custom base_url must be http(s)")
        host = body.host or base

    cfg = {
        "mode": mode,
        "host": host,
        "base_url": base,
        "updated_at": _now().isoformat(),
        "tailscale_hint": "Use MagicDNS hostname when mode=tailscale",
    }
    _REMOTE_CONFIG[auth["org_id"]] = cfg
    return {"ok": True, "remote": cfg}


# ── Connected apps (OAuth placeholders) ──


@router.get("/v1/mobile/connected-apps")
def list_connected_apps(mobile_token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    org_apps = _CONNECTED_APPS.setdefault(auth["org_id"], {})
    apps = []
    for name in SUPPORTED_APPS:
        state = org_apps.get(name, {"connected": False, "account_label": None})
        apps.append(
            {
                "app": name,
                "display_name": name.title(),
                "connected": bool(state.get("connected")),
                "account_label": state.get("account_label"),
            }
        )
    return {"ok": True, "apps": apps}


@router.post("/v1/mobile/connected-apps/{app}/connect")
def connect_app(
    app: str,
    mobile_token: str,
    body: ConnectedAppAction | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    app = app.lower()
    if app not in SUPPORTED_APPS:
        raise HTTPException(status_code=404, detail="Unsupported app")
    org_apps = _CONNECTED_APPS.setdefault(auth["org_id"], {})
    label = (body.account_label if body else None) or f"{app}@narna.local"
    org_apps[app] = {
        "connected": True,
        "account_label": label,
        "connected_at": _now().isoformat(),
        "note": "OAuth placeholder — wire real provider OAuth in production",
    }
    return {"ok": True, "app": app, **org_apps[app]}


@router.post("/v1/mobile/connected-apps/{app}/disconnect")
def disconnect_app(
    app: str,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    app = app.lower()
    org_apps = _CONNECTED_APPS.setdefault(auth["org_id"], {})
    org_apps[app] = {"connected": False, "account_label": None}
    return {"ok": True, "app": app, "connected": False}


# ── Push registration ──


@router.post("/v1/mobile/push/register")
def push_register(
    body: PushRegisterRequest,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    auth = _get_mobile_auth(mobile_token, db)
    _PUSH_DEVICES[body.device_token] = {
        "org_id": auth["org_id"],
        "platform": body.platform,
        "device_name": body.device_name or auth.get("device_name"),
        "registered_at": _now().isoformat(),
    }
    return {
        "ok": True,
        "registered": True,
        "note": "Device registered for approval push (APNs/FCM delivery to be wired).",
    }


@router.get("/v1/mobile/parity")
def parity_status(mobile_token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Feature flags for mobile clients."""
    _get_mobile_auth(mobile_token, db)
    return {
        "ok": True,
        "version": "0.2.0-mausbot-parity",
        "features": {
            "inbox": True,
            "routines": True,
            "voice": True,
            "remote": True,
            "connected_apps": True,
            "push": True,
            "multi_bot": True,
            "approval_gates": True,
        },
    }
