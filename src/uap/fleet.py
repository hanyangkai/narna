"""Fleet Governance loader (C4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_fleet(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("kind") != "Fleet":
        raise ValueError("fleet document must have kind: Fleet")
    return doc


def member_role(fleet: dict[str, Any], entity_id: str) -> str | None:
    for m in fleet.get("spec", {}).get("members") or []:
        if isinstance(m, dict) and m.get("entityId") == entity_id:
            return str(m.get("role") or "")
    return None


def role_denies(fleet: dict[str, Any], role: str) -> list[str]:
    roles = fleet.get("spec", {}).get("roles") or {}
    r = roles.get(role) or {}
    return list(r.get("deny") or [])


def role_can(fleet: dict[str, Any], role: str, action: str) -> bool:
    roles = fleet.get("spec", {}).get("roles") or {}
    r = roles.get(role) or {}
    deny = set(r.get("deny") or [])
    if action in deny:
        return False
    can = set(r.get("can") or [])
    if not can:
        return True
    return action in can


def meets_min_certification(fleet: dict[str, Any], level: str | None) -> bool:
    required = str(fleet.get("spec", {}).get("defaults", {}).get("minCertification") or "L1")
    rank = {"none": 0, "L1": 1, "L2": 2, "L3": 3}
    return rank.get(level or "none", 0) >= rank.get(required, 1)
