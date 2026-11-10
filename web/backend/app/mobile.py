"""NARNA Mobile Companion API - MausBot-style remote control for iOS/Android apps."""

from __future__ import annotations

import json
import os
import secrets
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import get_org_from_api_key
from .database import get_db
from .models import ApprovalRequest, MobileDevice, Organization
from .redis_client import get_pairing_code, store_pairing_code
from .websocket_manager import get_ws_manager

router = APIRouter()

# Add UAP/NARNA agent runtime to path
_src_path = Path(__file__).resolve().parent.parent.parent.parent / "src"
if _src_path.exists() and str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


# ── Pairing Models ──


class PairingStartRequest(BaseModel):
    device_name: str | None = None
    platform: str = "ios"  # ios | android


class PairingStartResponse(BaseModel):
    pairing_code: str
    qr_data: str
    expires_at: str


class PairingVerifyRequest(BaseModel):
    pairing_code: str


class PairingVerifyResponse(BaseModel):
    mobile_token: str
    agent_name: str
    org_id: int


class PairingRevokeRequest(BaseModel):
    mobile_token: str


# ── Bot Models ──


class BotInfo(BaseModel):
    bot_id: str
    name: str
    model: str
    status: str  # idle | working | waiting_approval
    last_message_at: str | None


class BotMessageRequest(BaseModel):
    message: str
    thread_id: str | None = None


class BotMessageResponse(BaseModel):
    thread_id: str
    message_id: str
    status: str


class ApprovalInfo(BaseModel):
    approval_id: str
    bot_id: str
    action_type: str  # shell_command | file_edit | web_action
    description: str
    details: dict[str, Any]
    created_at: str


class ApprovalResponse(BaseModel):
    approval_id: str
    decision: str  # allowed | denied


# ── In-memory pairing store (replace with Redis/DB in production) ──

_pairing_codes: dict[str, dict[str, Any]] = {}
_mobile_tokens: dict[str, dict[str, Any]] = {}


# ── Pairing Endpoints ──


@router.post("/v1/mobile/pairing/start", response_model=PairingStartResponse)
def start_pairing(
    body: PairingStartRequest,
    org: Organization = Depends(get_org_from_api_key),
) -> PairingStartResponse:
    """Generate pairing code and QR for mobile app."""
    
    # Generate 6-digit code
    code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    # Store pairing request
    _pairing_codes[code] = {
        "org_id": org.id,
        "org_name": org.name,
        "device_name": body.device_name or f"{body.platform.upper()} Device",
        "platform": body.platform,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # QR data: narna://pair?code=123456&org=dev
    qr_data = f"narna://pair?code={code}&org={org.name}"
    
    return PairingStartResponse(
        pairing_code=code,
        qr_data=qr_data,
        expires_at=expires_at.isoformat(),
    )


@router.post("/v1/mobile/pairing/verify", response_model=PairingVerifyResponse)
def verify_pairing(body: PairingVerifyRequest, db: Session = Depends(get_db)) -> PairingVerifyResponse:
    """Verify pairing code and issue mobile JWT token."""
    
    code = body.pairing_code
    pairing_data = _pairing_codes.get(code)
    
    if not pairing_data:
        raise HTTPException(status_code=404, detail="Invalid or expired pairing code")
    
    # Check expiry
    expires_at = datetime.fromisoformat(pairing_data["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        del _pairing_codes[code]
        raise HTTPException(status_code=410, detail="Pairing code expired")
    
    # Generate mobile token (JWT-style, 30 days validity)
    mobile_token = f"narna_mobile_{secrets.token_urlsafe(32)}"
    
    _mobile_tokens[mobile_token] = {
        "org_id": pairing_data["org_id"],
        "device_name": pairing_data["device_name"],
        "platform": pairing_data["platform"],
        "paired_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
    }
    
    # Clean up pairing code
    del _pairing_codes[code]
    
    return PairingVerifyResponse(
        mobile_token=mobile_token,
        agent_name=pairing_data["org_name"],
        org_id=pairing_data["org_id"],
    )


@router.delete("/v1/mobile/pairing/revoke")
def revoke_pairing(
    body: PairingRevokeRequest,
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    """Revoke mobile access token."""
    
    token = body.mobile_token
    token_data = _mobile_tokens.get(token)
    
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    
    if token_data["org_id"] != org.id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this token")
    
    del _mobile_tokens[token]
    
    return {"ok": True, "revoked_at": datetime.now(timezone.utc).isoformat()}


# ── Mobile Auth Dependency ──


def get_mobile_auth(mobile_token: str) -> dict[str, Any]:
    """Verify mobile token (replace with JWT decode in production)."""
    token_data = _mobile_tokens.get(mobile_token)
    
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired mobile token")
    
    expires_at = datetime.fromisoformat(token_data["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        del _mobile_tokens[mobile_token]
        raise HTTPException(status_code=401, detail="Mobile token expired")
    
    return token_data


# ── Bot Management ──


@router.get("/v1/mobile/bots")
def list_bots(mobile_token: str) -> list[BotInfo]:
    """List active bots (stub - implement with real agent sessions)."""
    auth = get_mobile_auth(mobile_token)
    
    # TODO: Query actual agent sessions from database
    # For now, return mock data
    return [
        BotInfo(
            bot_id="bot_1",
            name="NARNA Assistant",
            model="claude-3.5-sonnet",
            status="idle",
            last_message_at=datetime.now(timezone.utc).isoformat(),
        ),
    ]


@router.get("/v1/mobile/bots/{bot_id}/thread")
def get_bot_thread(bot_id: str, mobile_token: str, limit: int = 50) -> dict[str, Any]:
    """Get conversation thread for a bot (stub)."""
    auth = get_mobile_auth(mobile_token)
    
    # TODO: Query actual conversation history
    return {
        "bot_id": bot_id,
        "thread_id": "thread_1",
        "messages": [
            {
                "message_id": "msg_1",
                "role": "user",
                "content": "Hello, NARNA!",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "message_id": "msg_2",
                "role": "assistant",
                "content": "Hello! How can I help you today?",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ],
    }


@router.post("/v1/mobile/bots/{bot_id}/message", response_model=BotMessageResponse)
def send_bot_message(
    bot_id: str, body: BotMessageRequest, mobile_token: str
) -> BotMessageResponse:
    """Send message to bot (stub - integrate with NARNA agent runtime)."""
    auth = get_mobile_auth(mobile_token)
    
    # TODO: Send message to actual agent runtime
    # For now, return mock response
    thread_id = body.thread_id or f"thread_{int(time.time())}"
    message_id = f"msg_{int(time.time())}"
    
    return BotMessageResponse(
        thread_id=thread_id,
        message_id=message_id,
        status="processing",
    )


# ── Approval Gates ──


@router.get("/v1/mobile/approvals")
def list_approvals(mobile_token: str) -> list[ApprovalInfo]:
    """List pending approvals (stub)."""
    auth = get_mobile_auth(mobile_token)
    
    # TODO: Query actual pending approvals from agent runtime
    return []


@router.post("/v1/mobile/approvals/{approval_id}/allow", response_model=ApprovalResponse)
def allow_approval(approval_id: str, mobile_token: str) -> ApprovalResponse:
    """Allow a pending action."""
    auth = get_mobile_auth(mobile_token)
    
    # TODO: Send approval decision to agent runtime
    return ApprovalResponse(approval_id=approval_id, decision="allowed")


@router.post("/v1/mobile/approvals/{approval_id}/deny", response_model=ApprovalResponse)
def deny_approval(approval_id: str, mobile_token: str) -> ApprovalResponse:
    """Deny a pending action."""
    auth = get_mobile_auth(mobile_token)
    
    # TODO: Send denial decision to agent runtime
    return ApprovalResponse(approval_id=approval_id, decision="denied")


# ── WebSocket for Real-time Updates ──


@router.websocket("/v1/mobile/bots/{bot_id}/stream")
async def bot_stream(websocket: WebSocket, bot_id: str, mobile_token: str) -> None:
    """Real-time bot updates via WebSocket."""
    
    # Verify mobile token
    try:
        auth = get_mobile_auth(mobile_token)
    except HTTPException:
        await websocket.close(code=4001, reason="Invalid mobile token")
        return
    
    await websocket.accept()
    
    try:
        # TODO: Connect to actual agent runtime event stream
        # For now, send mock updates
        await websocket.send_json({
            "type": "connected",
            "bot_id": bot_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Keep connection alive and forward agent events
        while True:
            # Wait for client messages (ping, etc.)
            data = await websocket.receive_text()
            
            # Echo back for now
            await websocket.send_json({
                "type": "pong",
                "received": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    
    except WebSocketDisconnect:
        pass


# ── Health Check ──


@router.get("/v1/mobile/health")
def mobile_health() -> dict[str, Any]:
    """Mobile API health check."""
    return {
        "ok": True,
        "service": "narna-mobile-api",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
