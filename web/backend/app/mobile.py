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


# ── Helper functions ──


def _get_workspace_for_org(org_id: int) -> Path:
    """Get workspace path for organization."""
    base = Path(os.environ.get("UAP_HOME", os.path.expanduser("~/.narna")))
    return base / "orgs" / f"org_{org_id}"


def _get_agent_for_org(org_id: int) -> Any:
    """Get or create NarnaAgent instance for organization."""
    from uap.narna_agent import NarnaAgent
    
    workspace = _get_workspace_for_org(org_id)
    workspace.mkdir(parents=True, exist_ok=True)
    
    return NarnaAgent(workspace=workspace, tenant_id=f"org_{org_id}")


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
    
    # Store pairing request in Redis with 5-minute TTL
    pairing_data = {
        "org_id": org.id,
        "org_name": org.name,
        "device_name": body.device_name or f"{body.platform.upper()} Device",
        "platform": body.platform,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    store_pairing_code(code, pairing_data, ttl_seconds=300)
    
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
    pairing_data = get_pairing_code(code)
    
    if not pairing_data:
        raise HTTPException(status_code=404, detail="Invalid or expired pairing code")
    
    # Generate mobile token (30 days validity)
    mobile_token = f"narna_mobile_{secrets.token_urlsafe(32)}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Store in database
    device = MobileDevice(
        org_id=pairing_data["org_id"],
        mobile_token=mobile_token,
        device_name=pairing_data["device_name"],
        platform=pairing_data["platform"],
        paired_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    db.add(device)
    db.commit()
    
    return PairingVerifyResponse(
        mobile_token=mobile_token,
        agent_name=pairing_data["org_name"],
        org_id=pairing_data["org_id"],
    )


@router.delete("/v1/mobile/pairing/revoke")
def revoke_pairing(
    body: PairingRevokeRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Revoke mobile access token."""
    
    token = body.mobile_token
    device = db.query(MobileDevice).filter(MobileDevice.mobile_token == token).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Token not found")
    
    if device.org_id != org.id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this token")
    
    db.delete(device)
    db.commit()
    
    return {"ok": True, "revoked_at": datetime.now(timezone.utc).isoformat()}


# ── Mobile Auth Dependency ──


def get_mobile_auth(mobile_token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Verify mobile token from database."""
    device = db.query(MobileDevice).filter(MobileDevice.mobile_token == mobile_token).first()
    
    if not device:
        raise HTTPException(status_code=401, detail="Invalid or expired mobile token")
    
    if datetime.now(timezone.utc) > device.expires_at:
        db.delete(device)
        db.commit()
        raise HTTPException(status_code=401, detail="Mobile token expired")
    
    # Update last seen
    device.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    
    return {
        "org_id": device.org_id,
        "device_name": device.device_name,
        "platform": device.platform,
        "paired_at": device.paired_at.isoformat(),
    }


# ── Bot Management ──


@router.get("/v1/mobile/bots")
def list_bots(mobile_token: str, db: Session = Depends(get_db)) -> list[BotInfo]:
    """List active bots from agent sessions."""
    auth = get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]
    
    try:
        agent = _get_agent_for_org(org_id)
        workspace = _get_workspace_for_org(org_id)
        
        # Get agent sessions
        sessions_dir = workspace / ".uap" / "agent-sessions"
        bots: list[BotInfo] = []
        
        if sessions_dir.exists():
            for session_file in sessions_dir.glob("*.json"):
                try:
                    with open(session_file) as f:
                        session_data = json.load(f)
                    
                    session_id = session_data.get("sessionId", "")
                    messages = session_data.get("messages", [])
                    last_message = messages[-1] if messages else None
                    
                    # Determine status based on recent activity
                    status = "idle"
                    if last_message:
                        last_ts = last_message.get("ts", "")
                        if last_ts:
                            try:
                                last_time = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                                if (datetime.now(timezone.utc) - last_time).seconds < 300:
                                    status = "working"
                            except Exception:
                                pass
                    
                    bots.append(BotInfo(
                        bot_id=session_id,
                        name=f"NARNA {session_data.get('channel', 'Bot').title()}",
                        model="claude-3.5-sonnet",
                        status=status,
                        last_message_at=last_message.get("ts") if last_message else None,
                    ))
                except Exception:
                    continue
        
        # If no sessions, create a default bot
        if not bots:
            bots.append(BotInfo(
                bot_id="default",
                name="NARNA Assistant",
                model="claude-3.5-sonnet",
                status="idle",
                last_message_at=None,
            ))
        
        return bots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list bots: {str(e)}")


@router.get("/v1/mobile/bots/{bot_id}/thread")
def get_bot_thread(
    bot_id: str,
    mobile_token: str,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Get conversation thread for a bot from agent sessions."""
    auth = get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]
    
    try:
        agent = _get_agent_for_org(org_id)
        
        # Get session data
        session_data = agent.sessions.get(bot_id)
        
        if not session_data:
            # Return empty thread for new bot
            return {
                "bot_id": bot_id,
                "thread_id": bot_id,
                "messages": [],
            }
        
        messages = session_data.get("messages", [])[-limit:]
        
        formatted_messages = []
        for idx, msg in enumerate(messages):
            formatted_messages.append({
                "message_id": f"msg_{idx}_{msg.get('ts', '')}",
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "created_at": msg.get("ts", datetime.now(timezone.utc).isoformat()),
            })
        
        return {
            "bot_id": bot_id,
            "thread_id": bot_id,
            "messages": formatted_messages,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")


@router.post("/v1/mobile/bots/{bot_id}/message", response_model=BotMessageResponse)
async def send_bot_message(
    bot_id: str,
    body: BotMessageRequest,
    mobile_token: str,
    db: Session = Depends(get_db)
) -> BotMessageResponse:
    """Send message to bot and get agent response."""
    auth = get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]
    
    try:
        agent = _get_agent_for_org(org_id)
        thread_id = body.thread_id or bot_id
        
        # Register session with WebSocket manager
        ws_manager = get_ws_manager()
        ws_manager.register_session(thread_id, bot_id)
        
        # Send status update
        await ws_manager.send_to_bot(bot_id, {
            "type": "status",
            "status": "processing",
            "message": "Processing your request...",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Call agent.ask() to process the message
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def run_agent():
            return agent.ask(
                body.message,
                session_id=thread_id,
                use_tools=True,
                channel="mobile",
            )
        
        # Run agent in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, run_agent)
        
        # Send response via WebSocket
        await ws_manager.send_to_bot(bot_id, {
            "type": "message",
            "role": "assistant",
            "content": result.get("reply", ""),
            "message_id": f"msg_{int(time.time())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        return BotMessageResponse(
            thread_id=thread_id,
            message_id=f"msg_{int(time.time())}",
            status="completed",
        )
    except Exception as e:
        # Send error via WebSocket
        await ws_manager.send_to_bot(bot_id, {
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# ── Approval Gates ──


@router.get("/v1/mobile/approvals")
def list_approvals(mobile_token: str, db: Session = Depends(get_db)) -> list[ApprovalInfo]:
    """List pending approvals from database."""
    auth = get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]
    
    approvals = db.query(ApprovalRequest).filter(
        ApprovalRequest.org_id == org_id,
        ApprovalRequest.status == "pending"
    ).order_by(ApprovalRequest.created_at.desc()).limit(50).all()
    
    return [
        ApprovalInfo(
            approval_id=a.approval_id,
            bot_id=a.bot_id,
            action_type=a.action_type,
            description=a.description,
            details=json.loads(a.details_json),
            created_at=a.created_at.isoformat(),
        )
        for a in approvals
    ]


@router.post("/v1/mobile/approvals/{approval_id}/allow", response_model=ApprovalResponse)
async def allow_approval(
    approval_id: str,
    mobile_token: str,
    db: Session = Depends(get_db)
) -> ApprovalResponse:
    """Allow a pending action."""
    auth = get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]
    
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.approval_id == approval_id,
        ApprovalRequest.org_id == org_id
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already decided")
    
    approval.status = "approved"
    approval.decision = "allowed"
    approval.decided_at = datetime.now(timezone.utc)
    db.commit()
    
    # Notify agent via WebSocket
    ws_manager = get_ws_manager()
    await ws_manager.send_to_bot(approval.bot_id, {
        "type": "approval_decision",
        "approval_id": approval_id,
        "decision": "allowed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    return ApprovalResponse(approval_id=approval_id, decision="allowed")


@router.post("/v1/mobile/approvals/{approval_id}/deny", response_model=ApprovalResponse)
async def deny_approval(
    approval_id: str,
    mobile_token: str,
    db: Session = Depends(get_db)
) -> ApprovalResponse:
    """Deny a pending action."""
    auth = get_mobile_auth(mobile_token, db)
    org_id = auth["org_id"]
    
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.approval_id == approval_id,
        ApprovalRequest.org_id == org_id
    ).first()
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already decided")
    
    approval.status = "denied"
    approval.decision = "denied"
    approval.decided_at = datetime.now(timezone.utc)
    db.commit()
    
    # Notify agent via WebSocket
    ws_manager = get_ws_manager()
    await ws_manager.send_to_bot(approval.bot_id, {
        "type": "approval_decision",
        "approval_id": approval_id,
        "decision": "denied",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    return ApprovalResponse(approval_id=approval_id, decision="denied")


# ── WebSocket for Real-time Updates ──


@router.websocket("/v1/mobile/bots/{bot_id}/stream")
async def bot_stream(websocket: WebSocket, bot_id: str, mobile_token: str) -> None:
    """Real-time bot updates via WebSocket."""
    
    # Get database session for token verification
    db = next(get_db())
    
    # Verify mobile token
    try:
        device = db.query(MobileDevice).filter(MobileDevice.mobile_token == mobile_token).first()
        if not device:
            await websocket.close(code=4001, reason="Invalid mobile token")
            return
        
        if datetime.now(timezone.utc) > device.expires_at:
            await websocket.close(code=4001, reason="Token expired")
            return
        
        auth = {
            "org_id": device.org_id,
            "device_name": device.device_name,
            "platform": device.platform,
        }
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Register connection with WebSocket manager
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket, bot_id, mobile_token, auth)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "bot_id": bot_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                
                # Handle ping
                if data == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                else:
                    # Parse as JSON command
                    try:
                        command = json.loads(data)
                        command_type = command.get("type")
                        
                        if command_type == "ping":
                            await websocket.send_json({
                                "type": "pong",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
                    except json.JSONDecodeError:
                        pass
            except WebSocketDisconnect:
                break
            except Exception:
                break
    
    finally:
        # Clean up connection
        ws_manager.disconnect(websocket, bot_id)


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
