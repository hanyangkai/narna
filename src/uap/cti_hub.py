"""CTI Hub — multi-org Collective Threat Intelligence relay (Tier D / NGS-0020).

Cloud (or any NARNA node) can act as a hub: orgs submit privacy-preserving
signatures; peers pull a feed. No raw prompts/secrets — pattern hashes only.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collective import CollectiveDefense, _org_hash, _sha256_text
from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class CTIHub:
    """Shared signature feed under .uap/guardian/cti-hub/."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "guardian" / "cti-hub"
        self.feed = self.root / "feed"
        self.subs = self.root / "subscribers.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.feed.mkdir(parents=True, exist_ok=True)

    def submit(
        self,
        signature: dict[str, Any],
        *,
        org_id: str | None = None,
        require_opt_in: bool = True,
    ) -> dict[str, Any]:
        """Accept a privacy-preserving signature into the hub feed."""
        local = CollectiveDefense(self.workspace)
        if require_opt_in and not local._opt_in():  # noqa: SLF001
            # Hub itself may always accept if NARNA_CTI_HUB=1
            if os.environ.get("NARNA_CTI_HUB", "").lower() not in {"1", "true", "yes"}:
                raise PermissionError("collective opt-in or NARNA_CTI_HUB=1 required")

        sig = dict(signature)
        for bad in ("sessionId", "agentId", "prompts", "events", "graph", "secrets"):
            sig.pop(bad, None)
        sid = sig.get("signatureId") or new_id("sig")
        sig["signatureId"] = sid
        if "patternHash" not in sig and sig.get("patterns"):
            sig["patternHash"] = _sha256_text("|".join(sorted(sig["patterns"])))
        if "orgHash" not in sig:
            sig["orgHash"] = _org_hash(org_id)
        sig["hubReceivedAt"] = _now()
        sig["hubId"] = os.environ.get("NARNA_CTI_HUB_ID") or "local-hub"
        path = self.feed / f"{sid}.json"
        path.write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")
        # also mirror into local collective inbox for same-node consumers
        local.import_signature(sig)
        return {"ok": True, "signatureId": sid, "hub": sig["hubId"], "standard": "NGS-0020-hub"}

    def feed_list(self, *, limit: int = 100, since: str | None = None) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for p in sorted(self.feed.glob("sig_*.json"), reverse=True):
            try:
                row = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if since and str(row.get("hubReceivedAt") or "") < since:
                continue
            rows.append(row)
            if len(rows) >= limit:
                break
        return rows

    def subscribe(self, *, org_hash: str, callback_url: str | None = None) -> dict[str, Any]:
        data = {"subscribers": []}
        if self.subs.exists():
            data = json.loads(self.subs.read_text(encoding="utf-8"))
        entry = {
            "orgHash": org_hash,
            "callbackUrl": callback_url,
            "subscribedAt": _now(),
        }
        subs = [s for s in (data.get("subscribers") or []) if s.get("orgHash") != org_hash]
        subs.append(entry)
        data["subscribers"] = subs
        self.subs.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, **entry}

    def pull_into_workspace(self, *, limit: int = 50) -> dict[str, Any]:
        """Import hub feed into local collective inbox."""
        cd = CollectiveDefense(self.workspace)
        if not cd._opt_in():  # noqa: SLF001
            raise PermissionError("collective opt-in required to pull CTI hub feed")
        n = 0
        for sig in self.feed_list(limit=limit):
            cd.import_signature(sig)
            n += 1
        return {"ok": True, "imported": n, "standard": "NGS-0020-hub"}

    def relay_from_local_outbox(self) -> dict[str, Any]:
        """Push local outbox signatures into this hub (same node bootstrap)."""
        cd = CollectiveDefense(self.workspace)
        submitted = []
        for sig in cd.list_signatures(source="outbox"):
            submitted.append(self.submit(sig, require_opt_in=False)["signatureId"])
        return {"ok": True, "submitted": len(submitted), "ids": submitted}
