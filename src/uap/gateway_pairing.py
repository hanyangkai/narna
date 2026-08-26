"""Gateway DM pairing stub — unknown chat_id must pair before Ask (Hermes gap P8)."""

from __future__ import annotations

import json
import os
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def pairing_enabled() -> bool:
    return str(os.environ.get("UAP_GATEWAY_PAIRING") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class GatewayPairingStore:
    """Persist paired channel identities under workspace/.uap/gateway_pairs.json."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.path = self.workspace / ".uap" / "gateway_pairs.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"paired": {}, "pending": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"paired": {}, "pending": {}}
        if not isinstance(data, dict):
            return {"paired": {}, "pending": {}}
        data.setdefault("paired", {})
        data.setdefault("pending", {})
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @staticmethod
    def key(channel: str, external_id: str) -> str:
        return f"{channel}:{external_id}"

    def is_paired(self, channel: str, external_id: str) -> bool:
        if not pairing_enabled():
            return True
        data = self._load()
        return self.key(channel, external_id) in (data.get("paired") or {})

    def issue_code(self, channel: str, external_id: str) -> str:
        data = self._load()
        for code, row in (data.get("pending") or {}).items():
            if str(row.get("channel")) == channel and str(row.get("externalId")) == str(external_id):
                return str(code)
        alphabet = string.ascii_uppercase + string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        data["pending"][code] = {
            "channel": channel,
            "externalId": str(external_id),
            "issuedAt": _now(),
        }
        self._save(data)
        return code

    def confirm(self, code: str) -> dict[str, Any]:
        data = self._load()
        pending = (data.get("pending") or {}).pop(str(code).strip().upper(), None)
        if not pending:
            # also try as-is
            pending = (data.get("pending") or {}).pop(str(code).strip(), None)
        if not pending:
            return {"ok": False, "error": "unknown or expired pairing code"}
        k = self.key(str(pending["channel"]), str(pending["externalId"]))
        data["paired"][k] = {
            "channel": pending["channel"],
            "externalId": pending["externalId"],
            "pairedAt": _now(),
            "code": str(code).strip().upper(),
        }
        self._save(data)
        return {"ok": True, "paired": data["paired"][k]}

    def pair_direct(self, channel: str, external_id: str) -> dict[str, Any]:
        data = self._load()
        k = self.key(channel, external_id)
        data["paired"][k] = {
            "channel": channel,
            "externalId": str(external_id),
            "pairedAt": _now(),
            "code": "manual",
        }
        self._save(data)
        return {"ok": True, "paired": data["paired"][k]}

    def status(self) -> dict[str, Any]:
        data = self._load()
        return {
            "enabled": pairing_enabled(),
            "pairedCount": len(data.get("paired") or {}),
            "pendingCount": len(data.get("pending") or {}),
            "path": str(self.path),
        }


def gate_inbound(
    *,
    channel: str,
    external_id: str | None,
    text: str,
    workspace: str | Path | None = None,
) -> dict[str, Any] | None:
    """If pairing blocks the message, return a reply dict; else None (allow Ask)."""
    if not pairing_enabled() or not external_id:
        return None
    store = GatewayPairingStore(workspace)
    raw = (text or "").strip()
    slash = raw.split(None, 1)
    if slash and slash[0].lower() in {"/pair", "/pairing"}:
        code = slash[1].strip() if len(slash) > 1 else ""
        if not code:
            return {
                "blocked": True,
                "answer": "Usage: /pair CODE — use the code from the pairing message.",
            }
        out = store.confirm(code)
        if out.get("ok"):
            return {
                "blocked": True,
                "answer": f"Paired ✓ ({channel}:{external_id}). You can chat with NARNA now.",
                "paired": True,
            }
        return {"blocked": True, "answer": f"Pairing failed: {out.get('error')}"}

    if store.is_paired(channel, external_id):
        return None

    code = store.issue_code(channel, external_id)
    return {
        "blocked": True,
        "answer": (
            f"NARNA pairing required.\n"
            f"Code: {code}\n"
            f"Send `/pair {code}` in this chat, or have an admin confirm the code.\n"
            f"(Disable with UAP_GATEWAY_PAIRING=0)"
        ),
        "pairingCode": code,
    }
