"""Self-serve signup — email → org + API key (no Stripe)."""

from __future__ import annotations

import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import ApiKey, Organization, generate_api_key

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def signup_account(
    *,
    db: Session,
    email: str,
    name: str | None = None,
) -> dict:
    """Create free org + first API key. Email must be unique."""
    norm = normalize_email(email)
    if not norm or not _EMAIL_RE.match(norm):
        raise HTTPException(status_code=400, detail="valid email required")

    existing = db.query(Organization).filter(Organization.email == norm).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="email already registered — sign in with your API key at /account",
        )

    display = (name or "").strip() or norm.split("@")[0]
    org = Organization(name=display[:255], plan="free", email=norm)
    db.add(org)
    db.flush()

    full, prefix, key_hash = generate_api_key()
    db.add(
        ApiKey(
            org_id=org.id,
            key_prefix=prefix,
            key_hash=key_hash,
            label="signup",
        )
    )
    db.commit()
    db.refresh(org)

    return {
        "ok": True,
        "orgId": org.id,
        "email": norm,
        "name": org.name,
        "plan": org.plan,
        "apiKey": full,
        "keyPrefix": prefix,
        "message": "Store this API key securely — it is shown only once.",
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
    }
