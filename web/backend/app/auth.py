from __future__ import annotations

import hashlib
from typing import Any

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import ApiKey, Organization

security = HTTPBearer(auto_error=False)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def get_org_from_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
    db: Session = Depends(get_db),
) -> Organization:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="missing API key")
    org = resolve_api_key(credentials.credentials, db)
    if org is None:
        raise HTTPException(status_code=401, detail="invalid API key")
    return org


def resolve_api_key(key: str | None, db: Session) -> Organization | None:
    if not key:
        return None
    key = key.strip()
    if key.lower().startswith("bearer "):
        key = key.split(" ", 1)[1].strip()
    if not key.startswith("uap_live_"):
        return None
    record = db.query(ApiKey).filter(ApiKey.key_hash == hash_key(key)).first()
    if record is None:
        return None
    return db.query(Organization).filter(Organization.id == record.org_id).first()


def get_org_optional(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
    db: Session = Depends(get_db),
) -> Organization | None:
    if credentials is None or not credentials.credentials:
        return None
    return resolve_api_key(credentials.credentials, db)
