"""Map adapter permissions → Guardian capabilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def guardian_enabled(agent: Any, workspace: Path) -> bool:
    if os.environ.get("NARNA_GUARDIAN", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    if getattr(agent, "_narna_guardian", False):
        return True
    for cand in (
        workspace / "capability-passport.yaml",
        workspace / ".uap" / "capability-passport.yaml",
    ):
        if cand.exists():
            return True
    return False


def capability_for_permission(permission: str) -> str | None:
    """Best-effort map of permission/action → Capability Passport capability.

    Returns None when no Guardian capability gate applies (leave to policy/gov packages).
    """
    p = (permission or "").lower()
    if not p:
        return None
    if "create.agent" in p or "spawn" in p or p.endswith(".spawn"):
        return "create.agent"
    if "email" in p or "mail.send" in p:
        return "email"
    if "wallet" in p or "transfer" in p or "payment" in p:
        return "wallet"
    if "trade" in p or "order.place" in p:
        return "trade"
    if "terminal" in p or "shell" in p or "exec" in p:
        return "terminal"
    if "filesystem" in p or p.startswith("file.") or "fs." in p:
        return "filesystem"
    if p.startswith("tool.") or "call_tool" in p or p.startswith("mcp."):
        return "mcp"
    if "code" in p or "interpreter" in p:
        return "code"
    if "search" in p or "browser" in p:
        return "search"
    return None
