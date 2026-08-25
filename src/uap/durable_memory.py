"""Durable Memory — Decision OS project / customer / contract context."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .memory import LocalMemoryAdapter


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SCOPES = ("project", "customer", "contract", "agent", "session", "global")


class DurableMemory:
    """Scoped durable memory for Decision context (extends LocalMemoryAdapter)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "memory" / "durable"
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, scope: str, scope_id: str) -> Path:
        safe_scope = scope if scope in SCOPES else "global"
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in scope_id) or "default"
        return self.root / safe_scope / f"{safe_id}.json"

    def put(
        self,
        *,
        scope: str,
        scope_id: str,
        records: dict[str, Any],
    ) -> dict[str, Any]:
        path = self._path(scope, scope_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        data.update(records)
        data["_meta"] = {
            "scope": scope,
            "scopeId": scope_id,
            "updatedAt": _now(),
            "module": "Memory",
        }
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "scope": scope, "scopeId": scope_id, "keys": list(records.keys())}

    def get(
        self,
        *,
        scope: str,
        scope_id: str,
        keys: list[str] | None = None,
    ) -> dict[str, Any]:
        path = self._path(scope, scope_id)
        if not path.exists():
            return {"scope": scope, "scopeId": scope_id, "records": {}}
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.pop("_meta", None)
        if keys is not None:
            data = {k: data[k] for k in keys if k in data}
        return {"scope": scope, "scopeId": scope_id, "records": data, "meta": meta}

    def context_for(self, hints: dict[str, Any] | None = None) -> dict[str, Any]:
        hints = hints or {}
        slices = []
        for scope in ("contract", "customer", "project"):
            sid = hints.get(scope) or hints.get(f"{scope}Id")
            if sid:
                slices.append(self.get(scope=scope, scope_id=str(sid)))
        agent_id = hints.get("agentId")
        if agent_id:
            # also merge legacy agent memory
            try:
                legacy = LocalMemoryAdapter(self.workspace, str(agent_id)).read()
                slices.append({"scope": "agent", "scopeId": agent_id, "records": legacy})
            except Exception:
                pass
        return {"slices": slices, "module": "Memory"}
