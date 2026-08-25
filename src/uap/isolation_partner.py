"""Isolation partner adapters — host OS / orchestrator hooks (Tier D).

NARNA defines the policy contract; partners enforce kernel/network isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from .container_runner import DockerContainerRunner


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class IsolationPartner(Protocol):
    name: str

    def plan_isolation(self, *, agent_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        ...

    def apply_isolation(self, *, agent_id: str, dry_run: bool = True) -> dict[str, Any]:
        ...


class DockerIsolationPartner:
    name = "docker"

    def __init__(self, workspace: Any = None) -> None:
        self.runner = DockerContainerRunner(workspace)

    def plan_isolation(self, *, agent_id: str, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        plan = self.runner.plan(agent_id=agent_id, network="none")
        return {
            "partner": self.name,
            "agentId": agent_id,
            "plan": plan,
            "capabilities": ["network_none", "memory_limit", "read_only_root"],
            "standard": "NGS-0016-partner",
        }

    def apply_isolation(self, *, agent_id: str, dry_run: bool = True) -> dict[str, Any]:
        out = self.runner.run(agent_id=agent_id, dry_run=dry_run, network="none")
        return {"partner": self.name, "result": out, "appliedAt": _now()}


class KubernetesIsolationPartner:
    """Emits a PodSecurity / NetworkPolicy sketch — does not talk to a cluster."""

    name = "kubernetes"

    def plan_isolation(self, *, agent_id: str, profile: dict[str, Any] | None = None) -> dict[str, Any]:
        manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": f"narna-agent-{agent_id}"[:63],
                "labels": {"narna.ai/agent": agent_id, "narna.ai/guardian": "1"},
            },
            "spec": {
                "hostNetwork": False,
                "containers": [
                    {
                        "name": "agent",
                        "image": "narna/agent-container:0.1",
                        "securityContext": {
                            "readOnlyRootFilesystem": True,
                            "allowPrivilegeEscalation": False,
                            "runAsNonRoot": True,
                        },
                        "resources": {
                            "limits": {"memory": "512Mi", "cpu": "1"},
                        },
                    }
                ],
            },
        }
        netpol = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "NetworkPolicy",
            "metadata": {"name": f"narna-deny-{agent_id}"[:63]},
            "spec": {
                "podSelector": {"matchLabels": {"narna.ai/agent": agent_id}},
                "policyTypes": ["Ingress", "Egress"],
                "egress": [],
                "ingress": [],
            },
        }
        return {
            "partner": self.name,
            "agentId": agent_id,
            "pod": manifest,
            "networkPolicy": netpol,
            "note": "Apply with kubectl when cluster credentials available",
            "standard": "NGS-0016-partner",
        }

    def apply_isolation(self, *, agent_id: str, dry_run: bool = True) -> dict[str, Any]:
        plan = self.plan_isolation(agent_id=agent_id)
        return {
            "partner": self.name,
            "dryRun": dry_run,
            "executed": False,
            "plan": plan,
            "note": "v0 always dry-run — cluster apply is operator-owned",
            "appliedAt": _now(),
        }


class IsolationRegistry:
    """Resolve isolation partners by name."""

    def __init__(self, workspace: Any = None) -> None:
        self.workspace = workspace
        self._partners: dict[str, IsolationPartner] = {
            "docker": DockerIsolationPartner(workspace),
            "kubernetes": KubernetesIsolationPartner(),
            "k8s": KubernetesIsolationPartner(),
        }

    def list(self) -> list[dict[str, Any]]:
        certs: dict[str, Any] = {}
        try:
            from .partner_cert import PartnerRuntimeCertifier

            for c in PartnerRuntimeCertifier(self.workspace).list():
                certs[str(c.get("partner"))] = c.get("level")
        except Exception:
            pass
        return [
            {
                "name": "docker",
                "status": "available",
                "description": "Docker run --network none (optional execute)",
                "certLevel": certs.get("docker") or "L0",
            },
            {
                "name": "kubernetes",
                "status": "plan-only",
                "description": "Pod + deny-all NetworkPolicy manifests",
                "certLevel": certs.get("kubernetes") or "L0",
            },
        ]

    def get(self, name: str) -> IsolationPartner:
        key = name.lower().strip()
        if key not in self._partners:
            raise KeyError(f"unknown isolation partner: {name}")
        return self._partners[key]

    def plan(self, partner: str, *, agent_id: str) -> dict[str, Any]:
        return self.get(partner).plan_isolation(agent_id=agent_id)

    def apply(self, partner: str, *, agent_id: str, dry_run: bool = True) -> dict[str, Any]:
        return self.get(partner).apply_isolation(agent_id=agent_id, dry_run=dry_run)
