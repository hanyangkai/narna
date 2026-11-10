"""Bridge between NARNA agent runtime and mobile API."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .models import ApprovalRequest
from .websocket_manager import notify_approval_required


async def request_mobile_approval(
    db: Session,
    org_id: int,
    bot_id: str,
    session_id: str,
    action_type: str,
    description: str,
    details: dict[str, Any]
) -> str:
    """Create approval request and notify mobile app.
    
    Returns approval_id for tracking.
    """
    approval_id = f"appr_{secrets.token_urlsafe(12)}"
    
    # Store in database
    approval = ApprovalRequest(
        approval_id=approval_id,
        org_id=org_id,
        bot_id=bot_id,
        session_id=session_id,
        action_type=action_type,
        description=description,
        details_json=json.dumps(details),
        status="pending",
        created_at=datetime.now(timezone.utc),
    )
    db.add(approval)
    db.commit()
    
    # Notify mobile via WebSocket
    await notify_approval_required(
        bot_id=bot_id,
        approval_id=approval_id,
        action_type=action_type,
        description=description,
        details=details
    )
    
    return approval_id


def check_approval_status(db: Session, approval_id: str) -> dict[str, Any] | None:
    """Check if approval has been decided.
    
    Returns None if still pending, or decision dict if decided.
    """
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.approval_id == approval_id
    ).first()
    
    if not approval:
        return {"status": "not_found"}
    
    if approval.status == "pending":
        return None
    
    return {
        "status": approval.status,
        "decision": approval.decision,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
    }


def wait_for_approval(
    db: Session,
    approval_id: str,
    timeout_seconds: int = 300
) -> bool:
    """Wait for approval decision (blocking).
    
    Returns True if approved, False if denied or timeout.
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        decision = check_approval_status(db, approval_id)
        
        if decision is None:
            # Still pending, wait and check again
            time.sleep(2)
            db.expire_all()  # Refresh session
            continue
        
        if decision["status"] == "approved":
            return True
        
        # Denied or not found
        return False
    
    # Timeout
    return False
