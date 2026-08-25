"""Connect module — Decision OS connectors registry (MCP · API · DB · Files · Email · ERP · CRM)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


BUILTIN = [
    {"type": "mcp", "name": "MCP tools", "status": "available"},
    {"type": "api", "name": "HTTP API", "status": "available"},
    {"type": "db", "name": "SQL database", "status": "stub"},
    {"type": "files", "name": "Filesystem / workspace", "status": "available"},
    {"type": "email", "name": "Email", "status": "adapter"},
    {"type": "erp", "name": "ERP", "status": "stub"},
    {"type": "crm", "name": "CRM", "status": "stub"},
]


class ConnectRegistry:
    """Register and probe enterprise connectors — does not replace MCP hosts."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.path = self.workspace / ".uap" / "connect" / "connectors.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"connectors": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def builtins(self) -> list[dict[str, Any]]:
        return list(BUILTIN)

    def register(
        self,
        *,
        type: str,
        name: str,
        endpoint: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cid = new_id("conn")
        entry = {
            "connectorId": cid,
            "type": type.lower(),
            "name": name,
            "endpoint": endpoint,
            "config": config or {},
            "status": "registered",
            "registeredAt": _now(),
            "lastProbe": None,
            "standard": "Decision-OS-Connect",
        }
        data = self._read()
        data.setdefault("connectors", {})[cid] = entry
        self._write(data)
        return entry

    def list(self) -> list[dict[str, Any]]:
        rows = list((self._read().get("connectors") or {}).values())
        return rows

    def catalog(self) -> dict[str, Any]:
        return {
            "ok": True,
            "builtins": self.builtins(),
            "registered": self.list(),
            "module": "Connect",
        }

    def probe(self, connector_id: str) -> dict[str, Any]:
        data = self._read()
        entry = (data.get("connectors") or {}).get(connector_id)
        if not entry:
            raise KeyError(f"unknown connector: {connector_id}")
        # v0: connectivity is config-present check (no outbound secrets leak)
        ok = bool(entry.get("endpoint") or entry.get("config"))
        result = {
            "connectorId": connector_id,
            "ok": ok,
            "status": "reachable" if ok else "misconfigured",
            "probedAt": _now(),
            "note": "v0 probe checks config presence; live TCP/auth is host concern",
        }
        entry["lastProbe"] = result
        entry["status"] = result["status"]
        data["connectors"][connector_id] = entry
        self._write(data)
        return result
