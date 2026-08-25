"""Governance Council + Guardian Constitution — Layer 4 (human-only amend)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .hashing import sha256_obj
from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


DEFAULT_CONSTITUTION = Path(__file__).resolve().parent / "_packages" / "guardian-constitution.yaml"
DEFAULT_COUNCIL = Path(__file__).resolve().parent / "_packages" / "governance-council.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"invalid yaml: {path}")
    return raw


class GuardianConstitution:
    """Non-agent-editable constitutional principles (NGS Guardian L4)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.active_path = self.workspace / ".uap" / "guardian" / "constitution.yaml"

    def resolve_path(self, path: str | Path | None = None) -> Path:
        if path:
            return Path(path)
        if self.active_path.exists():
            return self.active_path
        for cand in (
            self.workspace / "guardian-constitution.yaml",
            DEFAULT_CONSTITUTION,
        ):
            if cand.exists():
                return cand
        raise FileNotFoundError("GuardianConstitution not found")

    def load(self, path: str | Path | None = None) -> dict[str, Any]:
        doc = load_yaml(self.resolve_path(path))
        if doc.get("kind") not in {"GuardianConstitution", "Constitution"}:
            raise ValueError("kind must be GuardianConstitution")
        return doc

    def install_default(self) -> dict[str, Any]:
        self.active_path.parent.mkdir(parents=True, exist_ok=True)
        doc = load_yaml(DEFAULT_CONSTITUTION)
        self.active_path.write_text(
            DEFAULT_CONSTITUTION.read_text(encoding="utf-8"), encoding="utf-8"
        )
        return {"ok": True, "path": str(self.active_path), "hash": sha256_obj(doc)}

    def evaluate(self, *, action: str, agent_id: str | None = None) -> dict[str, Any]:
        doc = self.load()
        spec = doc.get("spec") or {}
        levels = list(spec.get("levels") or [])
        action_l = action.lower()
        matched = None
        for level in levels:
            for a in level.get("actions") or []:
                a_l = str(a).lower()
                if a_l == action_l or action_l.startswith(a_l) or a_l in action_l:
                    matched = level
                    break
            if matched:
                break
        if matched is None:
            return {
                "ok": True,
                "decision": "allow",
                "action": action,
                "reasons": ["no constitutional deny matched"],
                "constitutionHash": sha256_obj(doc),
                "standard": "NGS-L4",
            }
        effect = str(matched.get("effect") or "deny").lower()
        return {
            "ok": True,
            "decision": effect,
            "action": action,
            "level": matched.get("level"),
            "principleId": matched.get("id"),
            "principle": matched.get("principle"),
            "reasons": [
                f"L{matched.get('level')}:{matched.get('id')} — {matched.get('principle')}"
            ],
            "agentId": agent_id,
            "constitutionHash": sha256_obj(doc),
            "agentAmendForbidden": True,
            "standard": "NGS-L4",
        }

    def agent_may_amend(self) -> bool:
        return False  # hard rule


class GovernanceCouncil:
    """Human council that alone may amend constitution / authorize global kill."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "guardian" / "council"
        self.root.mkdir(parents=True, exist_ok=True)
        self.votes_path = self.root / "votes.json"
        self.council_path = self.workspace / ".uap" / "guardian" / "council.yaml"

    def load(self) -> dict[str, Any]:
        for cand in (self.council_path, self.workspace / "governance-council.yaml", DEFAULT_COUNCIL):
            if cand.exists():
                doc = load_yaml(cand)
                if doc.get("kind") != "GovernanceCouncil":
                    raise ValueError("kind must be GovernanceCouncil")
                return doc
        raise FileNotFoundError("GovernanceCouncil not found")

    def install_default(self) -> dict[str, Any]:
        self.council_path.parent.mkdir(parents=True, exist_ok=True)
        self.council_path.write_text(DEFAULT_COUNCIL.read_text(encoding="utf-8"), encoding="utf-8")
        return {"ok": True, "path": str(self.council_path)}

    def members(self) -> list[dict[str, Any]]:
        return list((self.load().get("spec") or {}).get("members") or [])

    def quorum(self) -> int:
        return int((self.load().get("spec") or {}).get("quorum") or 2)

    def propose(
        self,
        *,
        kind: str,
        payload: dict[str, Any],
        proposed_by: str,
    ) -> dict[str, Any]:
        member_ids = {m.get("id") for m in self.members()}
        if proposed_by not in member_ids:
            raise PermissionError(f"{proposed_by} is not a council member")
        proposal = {
            "proposalId": new_id("prop"),
            "kind": kind,
            "payload": payload,
            "proposedBy": proposed_by,
            "approvals": [proposed_by],
            "status": "open",
            "createdAt": _now(),
        }
        data = self._votes()
        data.setdefault("proposals", []).append(proposal)
        self._write_votes(data)
        return proposal

    def approve(self, proposal_id: str, *, member_id: str) -> dict[str, Any]:
        member_ids = {m.get("id") for m in self.members()}
        if member_id not in member_ids:
            raise PermissionError(f"{member_id} is not a council member")
        data = self._votes()
        prop = None
        for p in data.get("proposals") or []:
            if p.get("proposalId") == proposal_id:
                prop = p
                break
        if prop is None:
            raise KeyError(f"unknown proposal: {proposal_id}")
        if prop.get("status") != "open":
            return prop
        approvals = list(prop.get("approvals") or [])
        if member_id not in approvals:
            approvals.append(member_id)
        prop["approvals"] = approvals
        if len(approvals) >= self.quorum():
            prop["status"] = "passed"
            prop["passedAt"] = _now()
            self._execute(prop)
            try:
                from .council_binding import CouncilBinding

                prop["binding"] = CouncilBinding(self.workspace).seal(prop)
            except Exception as e:
                prop["bindingError"] = str(e)
        self._write_votes(data)
        return prop

    def _execute(self, prop: dict[str, Any]) -> None:
        kind = prop.get("kind")
        payload = prop.get("payload") or {}
        if kind == "amend_constitution":
            # write new constitution only via council
            text = payload.get("yaml")
            if not text:
                raise ValueError("amend_constitution requires payload.yaml")
            # validate parse
            doc = yaml.safe_load(text)
            if not isinstance(doc, dict) or doc.get("kind") != "GuardianConstitution":
                raise ValueError("payload.yaml must be GuardianConstitution")
            # agents cannot call this path — only council._execute
            path = self.workspace / ".uap" / "guardian" / "constitution.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
            prop["executed"] = {"path": str(path), "hash": sha256_obj(doc)}
        elif kind == "global_kill":
            from .kill import KillStore

            entry = KillStore(self.workspace).issue_global(
                reason=str(payload.get("reason") or "council-global-kill"),
                issued_by=f"council:{','.join(prop.get('approvals') or [])}",
                council_proposal_id=prop.get("proposalId"),
            )
            prop["executed"] = entry
        elif kind == "domain_kill":
            from .kill import KillStore

            entry = KillStore(self.workspace).issue_domain(
                domain_id=str(payload.get("domainId") or os_org()),
                reason=str(payload.get("reason") or "council-domain-kill"),
                issued_by=f"council:{','.join(prop.get('approvals') or [])}",
            )
            prop["executed"] = entry

    def _votes(self) -> dict[str, Any]:
        if not self.votes_path.exists():
            return {"proposals": []}
        return json.loads(self.votes_path.read_text(encoding="utf-8"))

    def _write_votes(self, data: dict[str, Any]) -> None:
        self.votes_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def os_org() -> str:
    import os

    return os.environ.get("NARNA_ORG_ID") or "local"
