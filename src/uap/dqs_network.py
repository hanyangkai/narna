"""DQS Network — opt-in multi-org Decision Quality priors (NGS-0027).

Orgs export anonymized action priors; peers import to enrich ADQA memory attribute.
Never ships prompts / PII — only action, avgSuccess, count, optional guardian mix.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DqsNetwork:
    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "dqs-network"
        self.root.mkdir(parents=True, exist_ok=True)
        self.inbox = self.root / "inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.peers = self.root / "peers.json"

    def _read_peers(self) -> dict[str, Any]:
        if not self.peers.exists():
            return {"peers": [], "optIn": False}
        return json.loads(self.peers.read_text(encoding="utf-8"))

    def _write_peers(self, data: dict[str, Any]) -> None:
        data["updatedAt"] = _now()
        self.peers.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def set_opt_in(self, enabled: bool) -> dict[str, Any]:
        data = self._read_peers()
        data["optIn"] = bool(enabled)
        self._write_peers(data)
        return {"ok": True, "optIn": data["optIn"]}

    def status(self) -> dict[str, Any]:
        data = self._read_peers()
        return {
            "ok": True,
            "optIn": bool(data.get("optIn")),
            "peers": len(data.get("peers") or []),
            "inbox": len(list(self.inbox.glob("*.json"))),
            "standard": "NGS-0027",
        }

    def export_digest(
        self,
        *,
        org_id: str | int | None = None,
        min_count: int = 3,
    ) -> dict[str, Any]:
        """Export anonymized priors from Outcome Learning."""
        from .outcome_learning import OutcomeLearningEngine

        data = self._read_peers()
        if not data.get("optIn"):
            return {"ok": False, "error": "opt-in required", "standard": "NGS-0027"}

        priors = OutcomeLearningEngine(self.workspace)._read()
        actions_out: list[dict[str, Any]] = []
        for action, bucket in (priors.get("actions") or {}).items():
            count = int(bucket.get("count") or 0)
            if count < min_count:
                continue
            # Hash action namespace lightly for cross-org join without leaking internal names? 
            # Keep action string — industry packs share action ids (contract.sign).
            actions_out.append(
                {
                    "action": action,
                    "avgSuccess": bucket.get("avgSuccess"),
                    "count": count,
                    "hint": bucket.get("hint"),
                }
            )
        digest = {
            "kind": "DqsNetworkDigest",
            "standard": "NGS-0027",
            "exportedAt": _now(),
            "orgFingerprint": hashlib.sha256(str(org_id or "local").encode()).hexdigest()[:16],
            "actions": actions_out,
            "actionCount": len(actions_out),
        }
        path = self.root / f"export-{digest['orgFingerprint']}.json"
        path.write_text(json.dumps(digest, indent=2) + "\n", encoding="utf-8")
        digest["path"] = str(path)
        digest["ok"] = True
        return digest

    def import_digest(self, digest: dict[str, Any]) -> dict[str, Any]:
        data = self._read_peers()
        if not data.get("optIn"):
            return {"ok": False, "error": "opt-in required"}
        if digest.get("kind") != "DqsNetworkDigest":
            return {"ok": False, "error": "invalid digest kind"}
        fp = str(digest.get("orgFingerprint") or "peer")
        path = self.inbox / f"{fp}.json"
        path.write_text(json.dumps(digest, indent=2) + "\n", encoding="utf-8")
        peers = data.setdefault("peers", [])
        if fp not in peers:
            peers.append(fp)
        self._write_peers(data)
        merged = self.merge_priors()
        return {"ok": True, "imported": fp, "mergedActions": merged.get("mergedActions", 0)}

    def merge_priors(self) -> dict[str, Any]:
        """Blend peer inbox into local network priors (does not overwrite local learning)."""
        network_path = self.root / "network-priors.json"
        merged: dict[str, Any] = {"actions": {}}
        for path in self.inbox.glob("*.json"):
            try:
                dig = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for row in dig.get("actions") or []:
                action = str(row.get("action") or "")
                if not action:
                    continue
                bucket = merged["actions"].setdefault(
                    action, {"avgSuccess": 0.0, "count": 0, "peers": 0}
                )
                c = int(row.get("count") or 0)
                s = float(row.get("avgSuccess") or 0)
                # weighted average
                total = bucket["count"] + c
                if total > 0:
                    bucket["avgSuccess"] = (
                        bucket["avgSuccess"] * bucket["count"] + s * c
                    ) / total
                bucket["count"] = total
                bucket["peers"] = int(bucket.get("peers") or 0) + 1
        network_path.write_text(json.dumps({**merged, "updatedAt": _now()}, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "mergedActions": len(merged["actions"]), "path": str(network_path)}

    def enrich_adqa_context(self, action: str) -> dict[str, Any]:
        path = self.root / "network-priors.json"
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        bucket = (data.get("actions") or {}).get(action)
        if not bucket:
            return {}
        return {
            "decisionMemory": {
                "networkPrior": bucket,
                "lessons": [
                    f"dqs-network: peers={bucket.get('peers')} avgSuccess={bucket.get('avgSuccess')}"
                ],
            }
        }
