"""Emergency broadcast channel — Guardian Network Phase 5."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class EmergencyBroadcast:
    """Council/operator broadcasts for citizen devices to poll."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.path = self.workspace / ".uap" / "guardian" / "emergency-broadcasts.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"broadcasts": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def broadcast(
        self,
        *,
        message: str,
        severity: str = "high",
        action: str = "refresh_cti",
        issued_by: str = "operator",
    ) -> dict[str, Any]:
        row = {
            "broadcastId": new_id("eb"),
            "message": message,
            "severity": severity,
            "action": action,
            "issuedBy": issued_by,
            "issuedAt": _now(),
            "standard": "NGS-0021-emergency",
        }
        data = self._read()
        data.setdefault("broadcasts", []).append(row)
        # keep last 100
        data["broadcasts"] = data["broadcasts"][-100:]
        self._write(data)
        return row

    def list(self, *, limit: int = 20, since: str | None = None) -> list[dict[str, Any]]:
        rows = list(self._read().get("broadcasts") or [])
        if since:
            rows = [r for r in rows if str(r.get("issuedAt") or "") > since]
        return rows[-limit:]
