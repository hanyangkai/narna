"""Tenant-scoped workspaces for multi-tenant Decision Memory / ADQA."""

from __future__ import annotations

import os
from pathlib import Path


def cloud_data_root() -> Path:
    raw = os.environ.get("UAP_TENANT_ROOT") or os.environ.get("NARNA_TENANT_ROOT")
    if raw:
        root = Path(raw)
    else:
        root = Path.cwd() / ".uap" / "tenants"
    root.mkdir(parents=True, exist_ok=True)
    return root


def tenant_id_for_org(org_id: int) -> str:
    return f"org_{int(org_id)}"


def tenant_workspace(org_id: int | None = None, *, tenant_id: str | None = None) -> Path:
    """Per-org workspace so Decision Memory never mixes tenants."""
    if tenant_id:
        tid = tenant_id
    elif org_id is not None:
        tid = tenant_id_for_org(org_id)
    else:
        tid = "local"
    path = cloud_data_root() / tid
    path.mkdir(parents=True, exist_ok=True)
    (path / ".uap").mkdir(parents=True, exist_ok=True)
    return path
