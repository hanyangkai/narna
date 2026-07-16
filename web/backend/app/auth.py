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
    key = credentials.credentials
    if not key.startswith("uap_live_"):
        raise HTTPException(status_code=401, detail="invalid API key format")
    record = db.query(ApiKey).filter(ApiKey.key_hash == hash_key(key)).first()
    if record is None:
        raise HTTPException(status_code=401, detail="invalid API key")
    org = db.query(Organization).filter(Organization.id == record.org_id).first()
    if org is None:
        raise HTTPException(status_code=401, detail="organization not found")
    return org
