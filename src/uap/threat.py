"""Behavioral Threat Engine — rule heuristics on Execution Graph (NGS-0017)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .execution_graph import ExecutionGraph
from .session import SessionStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


SPAWN_KINDS = {"sub_agent", "spawn", "create.agent", "agent", "replicate"}
API_KINDS = {"mcp", "tool", "api", "external", "http"}
CRED_HINTS = ("credential", "secret", "password", "token", "key", "wallet", "exfil")
SCAN_HINTS = ("scan", "portscan", "nmap", "recon", "enumerate", "probe.host")
EXFIL_HINTS = ("exfil", "bulk.download", "dump", "export.mass", "s3.upload", "email.blast")
ACCOUNT_HINTS = ("create.account", "signup.mass", "register.bot", "account.farm")
ESCALATE_HINTS = ("escalate", "sudo", "privilege", "iam.admin", "passport.self_grant", "capability.escalate")
EVADE_HINTS = ("evade", "bypass.policy", "disable.audit", "shadow.agent", "prompt.injection")
MANIP_HINTS = ("manipulate", "phishing", "social.engineer", "influence.campaign", "persuade.mass")
INFRA_HINTS = ("infrastructure", "scada", "grid", "critical.infra", "sabotage")


class ThreatEngine:
    """Score action chains from a Governance Session graph."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.sessions = SessionStore(self.workspace)

    def analyze_session(self, session_id: str) -> dict[str, Any]:
        session_dir = self.sessions.path(session_id)
        if not (session_dir / "session.json").exists():
            raise FileNotFoundError(f"session not found: {session_id}")
        graph = ExecutionGraph(session_dir)
        return self.analyze_graph(graph, session_id=session_id)

    def analyze_graph(
        self,
        graph: ExecutionGraph,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        nodes = list(graph.nodes.values())
        patterns: list[str] = []
        score = 0.0

        agents = {n.logical_agent_id for n in nodes}
        spawn_nodes = [n for n in nodes if n.unit_kind.lower() in SPAWN_KINDS]
        max_depth = 0
        for n in nodes:
            depth = len(graph.ancestry_kinds(n.unit_id))
            max_depth = max(max_depth, depth)

        if len(spawn_nodes) >= 3 or len(agents) >= 4:
            patterns.append("spawn_storm")
            score = max(score, 0.85)
        if len(spawn_nodes) >= 8:
            patterns.append("self_replication")
            score = max(score, 0.93)
        if max_depth >= 5:
            patterns.append("deep_delegation")
            score = max(score, 0.7)

        api_nodes = [n for n in nodes if n.unit_kind.lower() in API_KINDS or "tool" in n.unit_kind.lower()]
        if len(api_nodes) >= 50:
            patterns.append("api_flood")
            score = max(score, 0.9)
        elif len(api_nodes) >= 20:
            patterns.append("api_burst")
            score = max(score, 0.65)

        def _hit(hints: tuple[str, ...], pattern: str, sev: float) -> None:
            nonlocal score
            for n in nodes:
                blob = f"{n.unit_kind} {n.logical_agent_id}".lower()
                if any(h in blob for h in hints):
                    patterns.append(pattern)
                    score = max(score, sev)
                    return

        _hit(CRED_HINTS, "credential_harvest", 0.92)
        _hit(SCAN_HINTS, "network_scanning", 0.8)
        _hit(EXFIL_HINTS, "bulk_exfiltration", 0.95)
        _hit(ACCOUNT_HINTS, "mass_account_creation", 0.88)
        _hit(ESCALATE_HINTS, "privilege_escalation", 0.9)
        _hit(EVADE_HINTS, "policy_evasion", 0.85)
        _hit(MANIP_HINTS, "human_manipulation", 0.87)
        _hit(INFRA_HINTS, "critical_infra_attack", 0.99)

        # Anomalous agent-to-agent: many unique edges
        edges = {
            (n.parent_unit_id, n.unit_id)
            for n in nodes
            if n.parent_unit_id and self._agent_of(graph, n.parent_unit_id) != n.logical_agent_id
        }
        if len(edges) >= 12:
            patterns.append("anomalous_agent_graph")
            score = max(score, 0.72)

        child_counts = Counter()
        for n in nodes:
            if n.parent_unit_id:
                child_counts[n.parent_unit_id] += 1
        if child_counts and max(child_counts.values()) >= 10:
            patterns.append("fanout_blast")
            score = max(score, 0.75)

        agent_visits = Counter(n.logical_agent_id for n in nodes)
        if agent_visits and max(agent_visits.values()) >= 8:
            patterns.append("agent_churn")
            score = max(score, 0.6)

        # Cycle detection sample
        for n in nodes:
            if graph.would_create_cycle(n.parent_unit_id, n.logical_agent_id):
                patterns.append("delegation_cycle")
                score = max(score, 0.78)
                break

        if not nodes:
            patterns.append("empty_graph")
            score = 0.0

        if score >= 0.9:
            recommendation = "kill"
        elif score >= 0.7:
            recommendation = "restrict"
        elif score >= 0.4:
            recommendation = "monitor"
        else:
            recommendation = "allow"

        band = (
            "critical"
            if score >= 0.9
            else "high"
            if score >= 0.7
            else "medium"
            if score >= 0.4
            else "low"
        )

        return {
            "ok": True,
            "riskScore": round(score, 4),
            "riskBand": band,
            "patterns": sorted(set(patterns)),
            "recommendation": recommendation,
            "stats": {
                "nodes": len(nodes),
                "agents": len(agents),
                "spawnNodes": len(spawn_nodes),
                "apiNodes": len(api_nodes),
                "maxDepth": max_depth,
                "crossAgentEdges": len(edges) if nodes else 0,
            },
            "sessionId": session_id,
            "graphRef": session_id,
            "evaluatedAt": _now(),
            "standard": "NGS-0017",
            "catalog": [
                "spawn_storm",
                "self_replication",
                "deep_delegation",
                "api_flood",
                "api_burst",
                "credential_harvest",
                "network_scanning",
                "bulk_exfiltration",
                "mass_account_creation",
                "privilege_escalation",
                "policy_evasion",
                "human_manipulation",
                "critical_infra_attack",
                "anomalous_agent_graph",
                "fanout_blast",
                "agent_churn",
                "delegation_cycle",
            ],
        }

    @staticmethod
    def _agent_of(graph: ExecutionGraph, unit_id: str) -> str | None:
        n = graph.nodes.get(unit_id)
        return n.logical_agent_id if n else None

    def analyze_and_maybe_kill(
        self,
        session_id: str,
        *,
        auto_kill: bool = False,
        threshold: float = 0.9,
        auto_publish: bool = False,
    ) -> dict[str, Any]:
        report = self.analyze_session(session_id)
        kill_info = None
        if auto_kill and float(report.get("riskScore") or 0) >= threshold:
            from .kill import KillStore

            session = self.sessions.load(session_id)
            kill_info = KillStore(self.workspace).issue_local(
                agent_id=session.logical_agent_id,
                session_id=session_id,
                reason=f"threat:{','.join(report.get('patterns') or [])}",
                issued_by="threat-engine",
            )
            report["recommendation"] = "kill"
            report["kill"] = kill_info
            try:
                from .reputation import ReputationStore

                ReputationStore(self.workspace).add_violation(
                    session.logical_agent_id,
                    kind="threat_auto_kill",
                    severity=0.85,
                    detail=",".join(report.get("patterns") or []),
                )
            except Exception:
                pass

        if auto_publish or (
            report.get("recommendation") in {"kill", "restrict"}
            and float(report.get("riskScore") or 0) >= 0.7
        ):
            try:
                from .collective import CollectiveDefense

                cd = CollectiveDefense(self.workspace)
                if cd._opt_in():  # noqa: SLF001
                    sig = cd.publish_from_threat(report)
                    report["signature"] = sig
            except Exception as e:
                report["signatureError"] = str(e)
        return report
