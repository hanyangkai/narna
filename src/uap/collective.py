"""Collective AI Defense Network — Guardian L3 (NGS-0020).

Privacy-preserving threat signatures: publish → import → match → apply.
No raw secrets/prompts — pattern hashes + optional org HMAC only.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _org_hash(org_id: str | None) -> str:
    org = (org_id or os.environ.get("NARNA_ORG_ID") or "local").strip()
    secret = (os.environ.get("NARNA_COLLECTIVE_HMAC_SECRET") or "narna-dev-collective").encode()
    digest = hmac.new(secret, org.encode("utf-8"), hashlib.sha256).hexdigest()
    return "hmac-sha256:" + digest


class CollectiveDefense:
    """Local inbox/outbox for threat signatures (federation-ready file store)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "guardian" / "collective"
        self.inbox = self.root / "inbox"
        self.outbox = self.root / "outbox"
        self.applied = self.root / "applied.json"
        self.root.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.outbox.mkdir(parents=True, exist_ok=True)

    def _opt_in(self) -> bool:
        flag = self.workspace / ".uap" / "guardian" / "collective_opt_in.json"
        if flag.exists():
            try:
                data = json.loads(flag.read_text(encoding="utf-8"))
                return bool(data.get("optIn"))
            except Exception:
                return False
        return os.environ.get("NARNA_COLLECTIVE_OPT_IN", "").lower() in {"1", "true", "yes"}

    def set_opt_in(self, opt_in: bool) -> dict[str, Any]:
        path = self.workspace / ".uap" / "guardian" / "collective_opt_in.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"optIn": bool(opt_in), "updatedAt": _now()}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload

    def publish_from_threat(
        self,
        report: dict[str, Any],
        *,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        if not self._opt_in():
            raise PermissionError("collective defense opt-in required (narna collective opt-in)")
        patterns = sorted(set(report.get("patterns") or []))
        if not patterns:
            raise ValueError("threat report has no patterns to publish")
        sig = {
            "signatureId": new_id("sig"),
            "version": "0.1",
            "patterns": patterns,
            "patternHash": _sha256_text("|".join(patterns)),
            "riskScore": report.get("riskScore"),
            "riskBand": report.get("riskBand"),
            "recommendation": report.get("recommendation"),
            "orgHash": _org_hash(org_id),
            "createdAt": _now(),
            "standard": "NGS-0020",
            # Never include session graphs, prompts, agent names, or secrets
        }
        path = self.outbox / f"{sig['signatureId']}.json"
        path.write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")
        # also drop into local inbox so same org can match immediately
        (self.inbox / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return sig

    def import_signature(self, signature: dict[str, Any] | str | Path) -> dict[str, Any]:
        if isinstance(signature, (str, Path)):
            p = Path(signature)
            signature = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(signature, dict):
            raise ValueError("signature must be an object")
        sid = signature.get("signatureId") or new_id("sig")
        signature = dict(signature)
        signature["signatureId"] = sid
        # strip forbidden fields if present
        for bad in ("sessionId", "agentId", "prompts", "events", "graph", "secrets"):
            signature.pop(bad, None)
        path = self.inbox / f"{sid}.json"
        path.write_text(json.dumps(signature, indent=2) + "\n", encoding="utf-8")
        return signature

    def list_signatures(self, *, source: str = "inbox") -> list[dict[str, Any]]:
        root = self.inbox if source == "inbox" else self.outbox
        rows: list[dict[str, Any]] = []
        for p in sorted(root.glob("sig_*.json")):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return rows

    def match(
        self,
        *,
        patterns: list[str] | None = None,
        risk_band: str | None = None,
    ) -> list[dict[str, Any]]:
        want = set(patterns or [])
        hits: list[dict[str, Any]] = []
        for sig in self.list_signatures(source="inbox"):
            sig_patterns = set(sig.get("patterns") or [])
            overlap = sorted(want & sig_patterns) if want else sorted(sig_patterns)
            if want and not overlap:
                continue
            if risk_band and str(sig.get("riskBand") or "") != risk_band:
                # still allow if patterns overlap strongly
                if not (want and overlap):
                    continue
            hits.append({**sig, "matchedPatterns": overlap or sorted(sig_patterns)})
        return hits

    def apply(
        self,
        signature_id: str,
        *,
        agent_id: str | None = None,
        auto_kill: bool = False,
        restrict_capabilities: list[str] | None = None,
    ) -> dict[str, Any]:
        """Apply an inbox signature: restrict capabilities and/or local-kill agent."""
        path = self.inbox / f"{signature_id}.json"
        if not path.exists():
            # allow bare id without prefix file naming edge cases
            matches = [s for s in self.list_signatures() if s.get("signatureId") == signature_id]
            if not matches:
                raise FileNotFoundError(f"signature not in inbox: {signature_id}")
            sig = matches[0]
        else:
            sig = json.loads(path.read_text(encoding="utf-8"))

        actions: list[dict[str, Any]] = []
        caps = restrict_capabilities or ["create.agent", "mcp", "terminal", "email", "wallet", "trade"]
        # write restriction overlay
        restrict_path = self.workspace / ".uap" / "guardian" / "capability_restrictions.json"
        restrict_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if restrict_path.exists():
            data = json.loads(restrict_path.read_text(encoding="utf-8"))
        agents = data.setdefault("agents", {})
        target = agent_id or "*"
        agents[target] = {
            "mode": "deny",
            "capabilities": caps,
            "signatureId": signature_id,
            "patterns": sig.get("patterns"),
            "appliedAt": _now(),
        }
        restrict_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        actions.append({"type": "capability_restrict", "agentId": target, "capabilities": caps})

        kill_entry = None
        if auto_kill or str(sig.get("recommendation") or "") == "kill":
            if agent_id:
                from .kill import KillStore

                kill_entry = KillStore(self.workspace).issue_local(
                    agent_id=agent_id,
                    reason=f"collective:{signature_id}",
                    issued_by="collective-defense",
                )
                actions.append({"type": "local_kill", "kill": kill_entry})

        applied = {"applied": []}
        if self.applied.exists():
            applied = json.loads(self.applied.read_text(encoding="utf-8"))
        record = {
            "signatureId": signature_id,
            "agentId": agent_id,
            "actions": actions,
            "appliedAt": _now(),
        }
        applied.setdefault("applied", []).append(record)
        self.applied.write_text(json.dumps(applied, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "signature": sig, "record": record, "standard": "NGS-0020"}

    def peers_path(self) -> Path:
        return self.root / "peers.json"

    def set_peers(self, urls: list[str]) -> dict[str, Any]:
        payload = {"peers": [u.rstrip("/") for u in urls if u.strip()], "updatedAt": _now()}
        self.peers_path().write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload

    def list_peers(self) -> list[str]:
        if not self.peers_path().exists():
            env = os.environ.get("NARNA_COLLECTIVE_PEERS", "")
            return [u.strip().rstrip("/") for u in env.split(",") if u.strip()]
        data = json.loads(self.peers_path().read_text(encoding="utf-8"))
        return list(data.get("peers") or [])

    def push_to_peers(self) -> dict[str, Any]:
        """Push outbox signatures to peer /v1/guardian/collective/import endpoints."""
        if not self._opt_in():
            raise PermissionError("collective defense opt-in required")
        peers = self.list_peers()
        if not peers:
            return {"ok": True, "pushed": 0, "peers": [], "note": "no peers configured"}
        import urllib.error
        import urllib.request

        results = []
        for sig in self.list_signatures(source="outbox"):
            for peer in peers:
                url = f"{peer}/v1/guardian/collective/import"
                try:
                    req = urllib.request.Request(
                        url,
                        data=json.dumps({"signature": sig}).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        results.append(
                            {"peer": peer, "signatureId": sig.get("signatureId"), "status": resp.status}
                        )
                except Exception as e:
                    code = getattr(e, "code", None)
                    results.append(
                        {
                            "peer": peer,
                            "signatureId": sig.get("signatureId"),
                            "error": str(e),
                            "status": code,
                        }
                    )
        return {"ok": True, "pushed": len(results), "results": results, "standard": "NGS-0020"}

    def pull_from_peers(self) -> dict[str, Any]:
        """Pull peer /v1/guardian/collective/signatures into local inbox."""
        if not self._opt_in():
            raise PermissionError("collective defense opt-in required")
        peers = self.list_peers()
        if not peers:
            return {"ok": True, "imported": 0, "peers": [], "note": "no peers configured"}
        import urllib.request

        imported = []
        for peer in peers:
            url = f"{peer}/v1/guardian/collective/signatures?source=outbox"
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                for sig in data.get("signatures") or []:
                    self.import_signature(sig)
                    imported.append(sig.get("signatureId"))
            except Exception as e:
                imported.append({"peer": peer, "error": str(e)})
        # also ingest peer global kills if exposed as signatures
        return {
            "ok": True,
            "imported": len([x for x in imported if isinstance(x, str)]),
            "details": imported,
            "standard": "NGS-0020",
        }

    def export_bundle(self) -> dict[str, Any]:
        """Federation hub payload for offline/peer exchange."""
        return {
            "kind": "CollectiveDefenseBundle",
            "exportedAt": _now(),
            "signatures": self.list_signatures(source="outbox"),
            "standard": "NGS-0020",
        }

    def import_bundle(self, bundle: dict[str, Any]) -> dict[str, Any]:
        count = 0
        for sig in bundle.get("signatures") or []:
            self.import_signature(sig)
            count += 1
        return {"ok": True, "imported": count, "standard": "NGS-0020"}

    @staticmethod
    def active_restrictions(workspace: Path, agent_id: str | None) -> dict[str, Any] | None:
        path = workspace / ".uap" / "guardian" / "capability_restrictions.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        agents = data.get("agents") or {}
        if agent_id and agent_id in agents:
            return agents[agent_id]
        return agents.get("*")
