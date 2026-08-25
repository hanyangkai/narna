"""Agent Container — Guardian NGS-0016 policy contract (sandbox for AI).

Full OS isolation is host-provided. NARNA enforces the policy contract:
deny-by-default network, tool allow-list, quotas, spawn depth.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .hashing import sha256_obj


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


DEFAULT_CONTAINER = Path(__file__).resolve().parent / "_packages" / "agent-container-default.yaml"


def load_container(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("AgentContainer must be a mapping")
    if raw.get("kind") not in {"AgentContainer", "Container"}:
        raise ValueError("kind must be AgentContainer")
    return raw


class AgentContainer:
    """Policy-contract sandbox bound to an agent workspace."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.active = self.workspace / ".uap" / "guardian" / "container.yaml"
        self.state_path = self.workspace / ".uap" / "guardian" / "container_state.json"

    def install_default(self) -> dict[str, Any]:
        self.active.parent.mkdir(parents=True, exist_ok=True)
        self.active.write_text(DEFAULT_CONTAINER.read_text(encoding="utf-8"), encoding="utf-8")
        doc = load_container(self.active)
        return {"ok": True, "path": str(self.active), "hash": sha256_obj(doc)}

    def load(self, path: str | Path | None = None) -> dict[str, Any]:
        for cand in (
            Path(path) if path else None,
            self.active,
            self.workspace / "agent-container.yaml",
            DEFAULT_CONTAINER,
        ):
            if cand and cand.exists():
                return load_container(cand)
        raise FileNotFoundError("AgentContainer not found — run: narna container install")

    def _state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"agents": {}}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _write_state(self, data: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def profile(self, agent_id: str | None = None) -> dict[str, Any]:
        doc = self.load()
        spec = doc.get("spec") or {}
        return {
            "ok": True,
            "agentId": agent_id,
            "network": spec.get("network") or "deny-by-default",
            "filesystem": spec.get("filesystem") or "workspace-only",
            "memory": spec.get("memory") or "isolated",
            "toolsAllowlist": list(spec.get("toolsAllowlist") or []),
            "quotas": dict(spec.get("quotas") or {}),
            "packageHash": sha256_obj(doc),
            "standard": "NGS-0016",
            "hostIsolationRequired": True,
            "note": "Full OS isolation is host/orchestrator responsibility",
        }

    def check(
        self,
        *,
        agent_id: str,
        action: str,
        tool: str | None = None,
        network: bool = False,
        spawn_depth: int | None = None,
    ) -> dict[str, Any]:
        """Evaluate whether an action is allowed under the container contract."""
        doc = self.load()
        spec = doc.get("spec") or {}
        reasons: list[str] = []
        decision = "allow"
        quotas = dict(spec.get("quotas") or {})
        net_mode = str(spec.get("network") or "deny-by-default")

        # Kill / freeze overlay
        freeze = self._state().get("agents", {}).get(agent_id) or {}
        if freeze.get("memoryFrozen"):
            decision = "deny"
            reasons.append("memory frozen (kill cascade)")
        if freeze.get("networkIsolated") and network:
            decision = "deny"
            reasons.append("network isolated (kill cascade)")
        if freeze.get("mcpDisconnected") and (
            (tool or "").startswith("mcp") or action.startswith("mcp")
        ):
            decision = "deny"
            reasons.append("MCP disconnected (kill cascade)")

        # Network deny-by-default — hard deny only when host given & not allowlisted,
        # or when kill-cascade isolated. Empty allowlist + no host → defer to Passport.
        if network and net_mode in {"deny-by-default", "deny", "isolated"}:
            allowed_hosts = [str(h) for h in (spec.get("networkAllowlist") or [])]
            # host can be passed via action suffix or future param; keep contract soft for adapters
            if freeze.get("networkIsolated"):
                decision = "deny"
                reasons.append("network isolated (kill cascade)")
            elif allowed_hosts and action:
                # if allowlist set, require match markers in action
                if not any(h in action for h in allowed_hosts):
                    # non-matching external still denied when allowlist configured
                    if any(x in action.lower() for x in ("http://", "https://", "://")):
                        decision = "deny"
                        reasons.append(f"host not in networkAllowlist ({net_mode})")
            elif net_mode == "isolated":
                decision = "deny"
                reasons.append("network mode=isolated")
            # deny-by-default with empty allowlist: policy contract noted, Passport decides
            elif not allowed_hosts:
                reasons.append(f"network mode={net_mode} (defer to Capability Passport)")

        # Tool allow-list (empty = defer to Capability Passport)
        allow = [str(t).lower() for t in (spec.get("toolsAllowlist") or [])]
        if tool and allow:
            t = tool.lower()
            if not any(t == a or t.startswith(a) or a in t for a in allow):
                decision = "deny"
                reasons.append(f"tool {tool!r} not in container allowlist")

        # Spawn depth quota
        max_depth = int(quotas.get("maxSpawnDepth") or 1)
        if spawn_depth is not None and spawn_depth > max_depth:
            decision = "deny"
            reasons.append(f"spawn depth {spawn_depth} > maxSpawnDepth {max_depth}")

        # API call quota (best-effort counter)
        max_api = quotas.get("maxApiCallsPerHour")
        if max_api is not None and (
            network or (tool or "").lower() in {"mcp", "api", "http", "external"}
        ):
            st = self._state()
            ag = st.setdefault("agents", {}).setdefault(agent_id, {})
            hour = _now()[:13]
            bucket = ag.setdefault("apiHour", {})
            if bucket.get("hour") != hour:
                bucket["hour"] = hour
                bucket["count"] = 0
            bucket["count"] = int(bucket.get("count") or 0) + 1
            ag["apiHour"] = bucket
            st["agents"][agent_id] = ag
            self._write_state(st)
            if bucket["count"] > int(max_api):
                decision = "deny"
                reasons.append(f"api quota exceeded ({bucket['count']}/{max_api})")

        if not reasons:
            reasons.append("container contract ok")

        return {
            "ok": True,
            "decision": decision,
            "action": action,
            "agentId": agent_id,
            "tool": tool,
            "reasons": reasons,
            "profile": self.profile(agent_id),
            "evaluatedAt": _now(),
            "standard": "NGS-0016",
        }

    def apply_kill_cascade(
        self,
        agent_id: str | None,
        *,
        tier: str = "local",
        token: str | None = None,
    ) -> dict[str, Any]:
        """Freeze memory, disconnect MCP, isolate network for agent (or all if domain/global)."""
        st = self._state()
        effects = {
            "capabilityRevoked": True,
            "mcpDisconnected": True,
            "memoryFrozen": True,
            "networkIsolated": True,
            "tier": tier,
            "killToken": token,
            "at": _now(),
        }
        if agent_id:
            targets = [agent_id]
        else:
            # domain/global — mark wildcard
            targets = ["*"]
        for aid in targets:
            row = st.setdefault("agents", {}).setdefault(aid, {})
            row.update(effects)
            st["agents"][aid] = row
        self._write_state(st)
        # also write capability revoke overlay
        restrict = self.workspace / ".uap" / "guardian" / "capability_restrictions.json"
        data: dict[str, Any] = {"agents": {}}
        if restrict.exists():
            data = json.loads(restrict.read_text(encoding="utf-8"))
        for aid in targets:
            data.setdefault("agents", {})[aid] = {
                "mode": "deny",
                "capabilities": ["*"],
                "reason": f"kill-cascade:{tier}",
                "killToken": token,
                "appliedAt": _now(),
            }
        restrict.parent.mkdir(parents=True, exist_ok=True)
        restrict.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "targets": targets, "effects": effects, "standard": "NGS-0019"}

    def is_frozen(self, agent_id: str) -> dict[str, Any] | None:
        st = self._state().get("agents") or {}
        row = st.get(agent_id) or st.get("*")
        if row and (row.get("memoryFrozen") or row.get("networkIsolated")):
            return row
        return None
