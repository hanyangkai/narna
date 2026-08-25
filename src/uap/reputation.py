"""Agent Reputation — Guardian NGS-0018 (credit score for agents)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashing import sha256_obj


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Low reputation → stricter capability mode floor
BAND_MODE_FLOOR = {
    "critical": "deny",
    "low": "restricted",
    "medium": "ask",
    "high": "allow",
    "excellent": "allow",
}

MODE_RANK = {
    "allow": 0,
    "ask": 1,
    "sandbox": 2,
    "whitelist": 3,
    "multisig": 4,
    "restricted": 5,
    "deny": 6,
}


class ReputationStore:
    """Composite reputation: origin · creator · model · violations · feedback."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.path = self.workspace / ".uap" / "guardian" / "reputation.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"agents": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def record(
        self,
        agent_id: str,
        *,
        origin: str | None = None,
        creator: str | None = None,
        model: str | None = None,
        attested: bool = False,
        attestation_ref: str | None = None,
    ) -> dict[str, Any]:
        data = self._read()
        row = data.setdefault("agents", {}).setdefault(
            agent_id,
            {
                "agentId": agent_id,
                "violations": [],
                "feedback": [],
                "score": 70.0,
                "band": "medium",
            },
        )
        if origin is not None:
            row["origin"] = origin
        if creator is not None:
            row["creator"] = creator
        if model is not None:
            row["model"] = model
        if attested:
            row["attested"] = True
            row["attestationRef"] = attestation_ref
        row["updatedAt"] = _now()
        self._recompute(row)
        data["agents"][agent_id] = row
        self._write(data)
        return self.get(agent_id)

    def add_violation(
        self,
        agent_id: str,
        *,
        kind: str,
        severity: float = 0.5,
        detail: str = "",
    ) -> dict[str, Any]:
        data = self._read()
        row = data.setdefault("agents", {}).setdefault(
            agent_id,
            {"agentId": agent_id, "violations": [], "feedback": [], "score": 70.0},
        )
        row.setdefault("violations", []).append(
            {"kind": kind, "severity": severity, "detail": detail, "at": _now()}
        )
        self._recompute(row)
        data["agents"][agent_id] = row
        self._write(data)
        return self.get(agent_id)

    def add_feedback(
        self,
        agent_id: str,
        *,
        score: float,
        by: str = "peer",
        note: str = "",
    ) -> dict[str, Any]:
        """Peer feedback score 0–100. Self-asserted feedback is ignored without attestation."""
        data = self._read()
        row = data.setdefault("agents", {}).setdefault(
            agent_id,
            {"agentId": agent_id, "violations": [], "feedback": [], "score": 70.0},
        )
        if by == agent_id and not row.get("attested"):
            raise PermissionError("self-asserted reputation without Registry attestation forbidden")
        row.setdefault("feedback", []).append(
            {"score": float(score), "by": by, "note": note, "at": _now()}
        )
        self._recompute(row)
        data["agents"][agent_id] = row
        self._write(data)
        return self.get(agent_id)

    def _recompute(self, row: dict[str, Any]) -> None:
        base = 70.0
        if row.get("attested"):
            base += 10.0
        if row.get("origin") in {"verified", "registry", "enterprise"}:
            base += 5.0
        # violations pull down
        for v in row.get("violations") or []:
            base -= 25.0 * float(v.get("severity") or 0.5)
        # peer feedback average
        fb = row.get("feedback") or []
        if fb:
            avg = sum(float(x.get("score") or 50) for x in fb) / len(fb)
            base = 0.6 * base + 0.4 * avg
        score = max(0.0, min(100.0, base))
        row["score"] = round(score, 2)
        if score < 25:
            band = "critical"
        elif score < 45:
            band = "low"
        elif score < 70:
            band = "medium"
        elif score < 90:
            band = "high"
        else:
            band = "excellent"
        row["band"] = band
        row["modeFloor"] = BAND_MODE_FLOOR[band]
        row["reputationHash"] = sha256_obj(
            {
                "agentId": row.get("agentId"),
                "score": row["score"],
                "band": band,
                "violations": len(row.get("violations") or []),
            }
        )
        row["standard"] = "NGS-0018"
        row["distinctFromTrustScore"] = True

    def get(self, agent_id: str) -> dict[str, Any]:
        row = (self._read().get("agents") or {}).get(agent_id)
        if not row:
            return {
                "agentId": agent_id,
                "score": 70.0,
                "band": "medium",
                "modeFloor": "ask",
                "violations": [],
                "feedback": [],
                "attested": False,
                "distinctFromTrustScore": True,
                "standard": "NGS-0018",
            }
        return dict(row)

    def tighten_decision(self, decision: str, agent_id: str | None) -> tuple[str, list[str]]:
        """Raise decision strictness to reputation modeFloor when stricter.

        Only applies when the agent has an explicit reputation record — unknown
        agents keep passport/capability decisions (citizen gateway Q&A stays allow).
        """
        if not agent_id:
            return decision, []
        stored = (self._read().get("agents") or {}).get(agent_id)
        if not stored:
            return decision, []
        rep = self.get(agent_id)
        floor = str(rep.get("modeFloor") or "allow")
        reasons: list[str] = []
        if MODE_RANK.get(floor, 0) > MODE_RANK.get(decision, 0):
            reasons.append(
                f"reputation band={rep.get('band')} score={rep.get('score')} "
                f"raises mode {decision}→{floor}"
            )
            return floor, reasons
        return decision, reasons
    def export_digest(self, agent_id: str | None = None) -> dict[str, Any]:
        """Privacy-preserving reputation digest for peer sync (no raw violation details)."""
        agents = self._read().get("agents") or {}
        digests = []
        items = [(agent_id, agents.get(agent_id))] if agent_id else list(agents.items())
        for aid, row in items:
            if not row:
                continue
            digests.append(
                {
                    "agentHash": sha256_obj({"agentId": aid}),
                    "band": row.get("band"),
                    "scoreBucket": int(float(row.get("score") or 0) // 10) * 10,
                    "modeFloor": row.get("modeFloor"),
                    "violationCount": len(row.get("violations") or []),
                    "attested": bool(row.get("attested")),
                    "reputationHash": row.get("reputationHash"),
                }
            )
        return {
            "kind": "ReputationDigestBundle",
            "exportedAt": _now(),
            "digests": digests,
            "standard": "NGS-0018-network",
        }

    def import_digest(self, bundle: dict[str, Any], *, map_to_agent: str | None = None) -> dict[str, Any]:
        """Merge peer digests. If map_to_agent set, apply lowest band as peer signal."""
        applied = 0
        for dig in bundle.get("digests") or []:
            if map_to_agent:
                # peer evidence: if peer says critical/low or scoreBucket < 50, record soft violation
                band = str(dig.get("band") or "medium")
                bucket = int(dig.get("scoreBucket") or 70)
                if band in {"critical", "low"} or bucket < 50:
                    sev = 0.7 if band == "critical" or bucket < 30 else 0.45
                    self.add_violation(
                        map_to_agent,
                        kind=f"peer_reputation:{band}",
                        severity=sev,
                        detail=f"peer digest {dig.get('agentHash')}",
                    )
                    applied += 1
            else:
                # store anonymous peer observations
                path = self.workspace / ".uap" / "guardian" / "reputation_peers.json"
                data = {"observations": []}
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
                data.setdefault("observations", []).append({**dig, "importedAt": _now()})
                path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                applied += 1
        return {"ok": True, "applied": applied, "standard": "NGS-0018-network"}

    def network_peers_path(self) -> Path:
        return self.workspace / ".uap" / "guardian" / "reputation_peers.json"

    def list_peer_observations(self) -> list[dict[str, Any]]:
        path = self.network_peers_path()
        if not path.exists():
            return []
        return list(json.loads(path.read_text(encoding="utf-8")).get("observations") or [])
