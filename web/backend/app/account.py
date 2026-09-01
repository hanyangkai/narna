"""Self-serve signup — email → org + API key (no Stripe)."""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .mail import send_recovery_email, send_welcome_email, mail_configured
from .models import ApiKey, AuthToken, Organization, generate_api_key

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_RECOVERY_TTL_HOURS = 1


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _issue_api_key(db: Session, org: Organization, *, label: str) -> str:
    full, prefix, key_hash = generate_api_key()
    db.add(
        ApiKey(
            org_id=org.id,
            key_prefix=prefix,
            key_hash=key_hash,
            label=label,
        )
    )
    return full


def signup_account(
    *,
    db: Session,
    email: str,
    name: str | None = None,
    send_email: bool = True,
) -> dict:
    """Create free org + first API key. Email must be unique."""
    norm = normalize_email(email)
    if not norm or not _EMAIL_RE.match(norm):
        raise HTTPException(status_code=400, detail="valid email required")

    existing = db.query(Organization).filter(Organization.email == norm).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="email already registered — use recovery at /account",
        )

    display = (name or "").strip() or norm.split("@")[0]
    org = Organization(name=display[:255], plan="free", email=norm)
    db.add(org)
    db.flush()

    full = _issue_api_key(db, org, label="signup")
    db.commit()
    db.refresh(org)

    emailed = False
    if send_email and mail_configured():
        emailed = send_welcome_email(to=norm, api_key=full, name=org.name)

    return {
        "ok": True,
        "orgId": org.id,
        "email": norm,
        "name": org.name,
        "plan": org.plan,
        "apiKey": full,
        "keyPrefix": full[:16],
        "message": "Store this API key securely — it is shown only once.",
        "emailSent": emailed,
    }


def request_recovery(*, db: Session, email: str) -> dict:
    """Send magic link if account exists. Always returns ok (no email enumeration)."""
    norm = normalize_email(email)
    if not norm or not _EMAIL_RE.match(norm):
        raise HTTPException(status_code=400, detail="valid email required")

    org = db.query(Organization).filter(Organization.email == norm).first()
    sent = False
    if org is not None:
        raw = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=_RECOVERY_TTL_HOURS)
        db.add(
            AuthToken(
                org_id=org.id,
                token_hash=_hash_token(raw),
                purpose="recovery",
                expires_at=expires,
            )
        )
        db.commit()
        if mail_configured():
            sent = send_recovery_email(to=norm, token=raw)
        else:
            # Dev without SMTP — log token server-side only in mock
            sent = False

    return {
        "ok": True,
        "message": "If an account exists, we sent a sign-in link to your email.",
        "emailSent": sent,
        "smtpConfigured": mail_configured(),
    }


def claim_recovery(*, db: Session, token: str) -> dict:
    """Exchange one-time token for a fresh API key."""
    raw = (token or "").strip()
    if len(raw) < 16:
        raise HTTPException(status_code=400, detail="invalid token")

    now = datetime.now(timezone.utc)
    row = (
        db.query(AuthToken)
        .filter(
            AuthToken.token_hash == _hash_token(raw),
            AuthToken.purpose == "recovery",
            AuthToken.used_at.is_(None),
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="invalid or expired link")

    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= now:
        raise HTTPException(status_code=410, detail="link expired — request a new one")

    org = db.query(Organization).filter(Organization.id == row.org_id).first()
    if org is None:
        raise HTTPException(status_code=404, detail="account not found")

    full = _issue_api_key(db, org, label="recovery")
    row.used_at = now
    db.commit()

    return {
        "ok": True,
        "apiKey": full,
        "email": org.email,
        "plan": org.plan,
        "message": "New API key issued. Previous keys still work until you revoke them.",
    }


def account_me(org: Organization) -> dict:
    return {
        "ok": True,
        "orgId": org.id,
        "email": getattr(org, "email", None),
        "name": org.name,
        "plan": org.plan,
        "createdAt": org.created_at.isoformat() if org.created_at else None,
        "planExpiresAt": (
            org.plan_expires_at.isoformat() if getattr(org, "plan_expires_at", None) else None
        ),
        "smtpConfigured": mail_configured(),
    }
