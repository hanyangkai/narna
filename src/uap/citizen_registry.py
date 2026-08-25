"""Citizen device registry + audit — free tier Guardian Network."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class CitizenRegistry:
    """Anonymous device registration + approval tokens + audit log."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "citizen"
        self.root.mkdir(parents=True, exist_ok=True)
        self.devices = self.root / "devices.json"
        self.audit_path = self.root / "audit.jsonl"
        self.approvals = self.root / "approvals.json"

    def _read_devices(self) -> dict[str, Any]:
        if not self.devices.exists():
            return {"devices": {}}
        return json.loads(self.devices.read_text(encoding="utf-8"))

    def _write_devices(self, data: dict[str, Any]) -> None:
        self.devices.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def register(self, *, label: str | None = None, profile: str = "citizen") -> dict[str, Any]:
        device_id = new_id("dev")
        api_key = f"narna_citizen_{secrets.token_hex(16)}"
        row = {
            "deviceId": device_id,
            "apiKey": api_key,
            "label": label or "Guardian Extension",
            "profile": profile if profile in {"citizen", "family"} else "citizen",
            "tier": "free",
            "createdAt": _now(),
            "standard": "NGS-0022",
        }
        data = self._read_devices()
        data.setdefault("devices", {})[device_id] = row
        # Also index by key prefix for lookup
        data.setdefault("byKey", {})[api_key] = device_id
        self._write_devices(data)
        return {
            "ok": True,
            "deviceId": device_id,
            "apiKey": api_key,
            "profile": row["profile"],
            "tier": "free",
        }

    def resolve_key(self, api_key: str | None) -> dict[str, Any] | None:
        if not api_key:
            return None
        data = self._read_devices()
        did = (data.get("byKey") or {}).get(api_key)
        if not did:
            return None
        return (data.get("devices") or {}).get(did)

    def issue_approval(
        self,
        *,
        device_id: str,
        capability: str,
        ttl_seconds: int = 300,
    ) -> dict[str, Any]:
        token = f"apr_{secrets.token_hex(12)}"
        exp = datetime.now(timezone.utc).timestamp() + ttl_seconds
        store = {}
        if self.approvals.exists():
            store = json.loads(self.approvals.read_text(encoding="utf-8"))
        store[token] = {
            "deviceId": device_id,
            "capability": capability,
            "expiresAt": exp,
            "issuedAt": _now(),
        }
        self.approvals.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")
        return {"approvalToken": token, "capability": capability, "ttlSeconds": ttl_seconds}

    def consume_approval(self, token: str | None, *, capability: str) -> bool:
        if not token or not self.approvals.exists():
            return False
        store = json.loads(self.approvals.read_text(encoding="utf-8"))
        row = store.get(token)
        if not row:
            return False
        if float(row.get("expiresAt") or 0) < datetime.now(timezone.utc).timestamp():
            store.pop(token, None)
            self.approvals.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")
            return False
        if str(row.get("capability")) != capability:
            return False
        store.pop(token, None)
        self.approvals.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")
        return True

    def audit(self, entry: dict[str, Any]) -> None:
        line = json.dumps({**entry, "at": _now()}, ensure_ascii=False)
        with self.audit_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def list_audit(self, *, limit: int = 50, device_id: str | None = None) -> list[dict[str, Any]]:
        if not self.audit_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.audit_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if device_id and row.get("deviceId") != device_id:
                continue
            rows.append(row)
        return rows[-limit:]
