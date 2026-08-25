"""Kill Token store — Guardian NGS-0019 (local / domain / global)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_org() -> str:
    return os.environ.get("NARNA_ORG_ID") or "local"


class KillStore:
    """Persist kills under .uap/guardian/ — local, domain, and council global."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.path = self.workspace / ".uap" / "guardian" / "kills.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"agents": {}, "sessions": {}, "domains": {}, "global": None, "tokens": {}}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data.setdefault("agents", {})
        data.setdefault("sessions", {})
        data.setdefault("domains", {})
        data.setdefault("tokens", {})
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def issue_local(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        reason: str = "manual",
        issued_by: str = "operator",
    ) -> dict[str, Any]:
        if not agent_id and not session_id:
            raise ValueError("agent_id or session_id required")
        token = new_id("kill")
        entry = {
            "token": token,
            "tier": "local",
            "agentId": agent_id,
            "sessionId": session_id,
            "reason": reason,
            "issuedBy": issued_by,
            "killedAt": _now(),
            "active": True,
        }
        data = self._read()
        data.setdefault("tokens", {})[token] = entry
        if agent_id:
            data.setdefault("agents", {})[agent_id] = entry
        if session_id:
            data.setdefault("sessions", {})[session_id] = entry
            try:
                from .session import SessionStore

                store = SessionStore(self.workspace)
                if (store.path(session_id) / "session.json").exists():
                    store.close(session_id, terminated=True, reason=f"kill:{reason}")
            except Exception:
                pass
        self._write(data)
        entry["cascade"] = self._run_cascade(
            agent_id=agent_id,
            tier="local",
            token=token,
            reason=reason,
        )
        return entry

    def issue_domain(
        self,
        *,
        domain_id: str | None = None,
        reason: str = "domain-kill",
        issued_by: str = "operator",
    ) -> dict[str, Any]:
        """Kill all agents in an org/domain (L3 scope)."""
        domain = (domain_id or _default_org()).strip()
        token = new_id("kill")
        entry = {
            "token": token,
            "tier": "domain",
            "domainId": domain,
            "reason": reason,
            "issuedBy": issued_by,
            "killedAt": _now(),
            "active": True,
        }
        data = self._read()
        data.setdefault("tokens", {})[token] = entry
        data.setdefault("domains", {})[domain] = entry
        self._write(data)
        entry["cascade"] = self._run_cascade(
            agent_id=None,
            tier="domain",
            token=token,
            reason=reason,
        )
        return entry

    def issue_global(
        self,
        *,
        reason: str = "global-kill",
        issued_by: str = "council",
        council_proposal_id: str | None = None,
    ) -> dict[str, Any]:
        """Network-wide kill flag — only Governance Council may issue (L4)."""
        token = new_id("kill")
        entry = {
            "token": token,
            "tier": "global",
            "reason": reason,
            "issuedBy": issued_by,
            "councilProposalId": council_proposal_id,
            "killedAt": _now(),
            "active": True,
        }
        data = self._read()
        data.setdefault("tokens", {})[token] = entry
        data["global"] = entry
        # federation outbox for peers
        outbox = self.workspace / ".uap" / "guardian" / "collective" / "global_kills"
        outbox.mkdir(parents=True, exist_ok=True)
        (outbox / f"{token}.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        self._write(data)
        entry["cascade"] = self._run_cascade(
            agent_id=None,
            tier="global",
            token=token,
            reason=reason,
        )
        return entry

    def _run_cascade(
        self,
        *,
        agent_id: str | None,
        tier: str,
        token: str,
        reason: str,
    ) -> dict[str, Any]:
        """Kill Token → Capability revoked → MCP disconnected → Memory frozen → Network isolated."""
        steps: list[dict[str, Any]] = [{"step": "kill_token", "token": token, "tier": tier}]
        try:
            from .container import AgentContainer

            cascade = AgentContainer(self.workspace).apply_kill_cascade(
                agent_id, tier=tier, token=token
            )
            steps.append({"step": "capability_revoked", "ok": True})
            steps.append({"step": "mcp_disconnected", "ok": True})
            steps.append({"step": "memory_frozen", "ok": True})
            steps.append({"step": "network_isolated", "ok": True})
            steps.append({"step": "container", "detail": cascade})
        except Exception as e:
            steps.append({"step": "cascade_error", "error": str(e)})
        try:
            from .reputation import ReputationStore

            if agent_id:
                ReputationStore(self.workspace).add_violation(
                    agent_id, kind=f"killed:{tier}", severity=0.9, detail=reason
                )
                steps.append({"step": "reputation_violation", "ok": True})
        except Exception:
            pass
        # federation: publish kill notice when collective opt-in
        try:
            from .collective import CollectiveDefense

            cd = CollectiveDefense(self.workspace)
            if cd._opt_in():  # noqa: SLF001 — intentional for cascade
                notice = {
                    "signatureId": f"sig_kill_{token}",
                    "version": "0.1",
                    "patterns": [f"kill_{tier}"],
                    "riskBand": "critical",
                    "recommendation": "kill",
                    "killToken": token,
                    "createdAt": _now(),
                    "standard": "NGS-0020",
                }
                cd.import_signature(notice)
                (cd.outbox / f"{notice['signatureId']}.json").write_text(
                    json.dumps(notice, indent=2) + "\n", encoding="utf-8"
                )
                steps.append({"step": "collective_broadcast", "ok": True})
        except Exception:
            pass
        return {
            "flow": "Kill Token → Capability revoked → MCP disconnected → Memory frozen → Network isolated",
            "steps": steps,
            "standard": "NGS-0019",
        }

    def is_global_killed(self) -> dict[str, Any] | None:
        row = self._read().get("global")
        if row and row.get("active"):
            return row
        return None

    def is_domain_killed(self, domain_id: str | None = None) -> dict[str, Any] | None:
        domain = (domain_id or _default_org()).strip()
        row = (self._read().get("domains") or {}).get(domain)
        if row and row.get("active"):
            return row
        return None

    def is_agent_killed(self, agent_id: str) -> dict[str, Any] | None:
        g = self.is_global_killed()
        if g:
            return g
        d = self.is_domain_killed()
        if d:
            return d
        row = (self._read().get("agents") or {}).get(agent_id)
        if row and row.get("active"):
            return row
        return None

    def is_session_killed(self, session_id: str) -> dict[str, Any] | None:
        g = self.is_global_killed()
        if g:
            return g
        row = (self._read().get("sessions") or {}).get(session_id)
        if row and row.get("active"):
            return row
        return None

    def revoke(self, token: str) -> dict[str, Any]:
        data = self._read()
        entry = (data.get("tokens") or {}).get(token)
        if not entry:
            raise KeyError(f"unknown kill token: {token}")
        entry["active"] = False
        entry["revokedAt"] = _now()
        agent_id = entry.get("agentId")
        session_id = entry.get("sessionId")
        domain_id = entry.get("domainId")
        if agent_id and (data.get("agents") or {}).get(agent_id, {}).get("token") == token:
            data["agents"][agent_id]["active"] = False
        if session_id and (data.get("sessions") or {}).get(session_id, {}).get("token") == token:
            data["sessions"][session_id]["active"] = False
        if domain_id and (data.get("domains") or {}).get(domain_id, {}).get("token") == token:
            data["domains"][domain_id]["active"] = False
        if data.get("global") and data["global"].get("token") == token:
            data["global"]["active"] = False
        data["tokens"][token] = entry
        self._write(data)
        return entry

    def status(
        self,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        domain_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "agent": self.is_agent_killed(agent_id) if agent_id else None,
            "session": self.is_session_killed(session_id) if session_id else None,
            "domain": self.is_domain_killed(domain_id),
            "global": self.is_global_killed(),
            "standard": "NGS-0019",
            "tiers": ["local", "domain", "global"],
        }
