"""CTI Mesh — sync local outbox ↔ remote CTI hub URLs (multi-VPS)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collective import CollectiveDefense
from .cti_hub import CTIHub


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class CTIMesh:
    """Push/pull privacy-preserving signatures across configured hub endpoints."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.path = self.workspace / ".uap" / "guardian" / "cti-mesh.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            env = os.environ.get("NARNA_CTI_HUBS", "")
            hubs = [u.strip().rstrip("/") for u in env.split(",") if u.strip()]
            return {"hubs": hubs, "updatedAt": None}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        data["updatedAt"] = _now()
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def set_hubs(self, hubs: list[str]) -> dict[str, Any]:
        data = {"hubs": [h.rstrip("/") for h in hubs if h.strip()]}
        self._write(data)
        return data

    def list_hubs(self) -> list[str]:
        return list(self._read().get("hubs") or [])

    def push(self) -> dict[str, Any]:
        """Push local outbox (+ local hub feed) to remote hubs."""
        cd = CollectiveDefense(self.workspace)
        if not cd._opt_in():  # noqa: SLF001
            raise PermissionError("collective opt-in required for mesh push")
        hubs = self.list_hubs()
        if not hubs:
            return {"ok": True, "pushed": 0, "note": "no hubs configured"}
        # Prefer local hub feed; fallback outbox
        local_hub = CTIHub(self.workspace)
        sigs = local_hub.feed_list(limit=200) or cd.list_signatures(source="outbox")
        results = []
        for hub in hubs:
            url = f"{hub}/v1/guardian/cti/submit"
            for sig in sigs:
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps({"signature": sig}).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        results.append(
                            {
                                "hub": hub,
                                "signatureId": sig.get("signatureId"),
                                "status": resp.status,
                            }
                        )
                except Exception as e:
                    results.append(
                        {
                            "hub": hub,
                            "signatureId": sig.get("signatureId"),
                            "error": str(e),
                            "status": getattr(e, "code", None),
                        }
                    )
        return {
            "ok": True,
            "pushed": len([r for r in results if not r.get("error")]),
            "results": results,
            "standard": "NGS-0020-mesh",
            "syncedAt": _now(),
        }

    def pull(self, *, limit: int = 100) -> dict[str, Any]:
        """Pull remote hub feeds into local inbox + local hub."""
        cd = CollectiveDefense(self.workspace)
        if not cd._opt_in():  # noqa: SLF001
            raise PermissionError("collective opt-in required for mesh pull")
        hubs = self.list_hubs()
        if not hubs:
            return {"ok": True, "imported": 0, "note": "no hubs configured"}
        hub_local = CTIHub(self.workspace)
        imported: list[str] = []
        errors: list[dict[str, Any]] = []
        for hub in hubs:
            url = f"{hub}/v1/guardian/cti/feed?limit={limit}"
            try:
                with urllib.request.urlopen(url, timeout=15) as resp:
                    data = json.loads(resp.read().decode())
                for sig in data.get("feed") or []:
                    hub_local.submit(sig, require_opt_in=False)
                    cd.import_signature(sig)
                    imported.append(str(sig.get("signatureId")))
            except Exception as e:
                errors.append({"hub": hub, "error": str(e)})
        return {
            "ok": True,
            "imported": len(set(imported)),
            "ids": sorted(set(imported)),
            "errors": errors,
            "standard": "NGS-0020-mesh",
            "syncedAt": _now(),
        }

    def sync(self) -> dict[str, Any]:
        """Push then pull."""
        return {"ok": True, "push": self.push(), "pull": self.pull(), "standard": "NGS-0020-mesh"}
