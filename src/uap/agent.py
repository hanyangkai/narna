from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .audit import audit_run
from .identity import IdentityStore
from .marketplace import Marketplace
from .passport import refresh_passport
from .proof import write_proof_bundle
from .registry import AgentRegistry
from .runtime import LocalRuntime, RunResult
from .spec import AgentSpec, load_agent_spec
from .vap.pipeline import run_vap_pipeline
from .verify import verify_proof_bundle


class Agent:
    def __init__(
        self,
        *,
        name: str | None = None,
        spec_path: str | Path | None = None,
        workspace: str | Path | None = None,
    ) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.runtime = LocalRuntime(self.workspace)
        self._spec_path = Path(spec_path) if spec_path else None

        if spec_path is not None:
            self.spec = load_agent_spec(spec_path)
        else:
            agent_name = name or "Unnamed Agent"
            self.spec = AgentSpec(
                raw={
                    "apiVersion": "uap.dev/v1alpha1",
                    "kind": "Agent",
                    "metadata": {
                        "id": "01JEXAMPLELOCALAGENT000001",
                        "name": agent_name,
                        "version": "0.0.0",
                        "creator": "local",
                        "createdAt": "2026-07-16T00:00:00Z",
                    },
                    "spec": {
                        "capability": ["code"],
                        "permissions": [],
                        "policy": {"ref": "policies/local-default@0.0.0"},
                    },
                }
            )

    @classmethod
    def from_spec(cls, spec_path: str | Path, *, workspace: str | Path | None = None) -> "Agent":
        return cls(spec_path=spec_path, workspace=workspace)

    def run(self, input: str | None = None, *, auto_approve_ask: bool = False) -> RunResult:
        return self.runtime.run(
            self.spec,
            user_input=input,
            auto_approve_ask=auto_approve_ask,
            spec_path=self._spec_path,
        )

    def resolve_ask(self, run_id: str, *, approved: bool) -> RunResult:
        if not self._spec_path:
            raise ValueError("resolve_ask requires Agent created from spec file")
        return self.runtime.resolve_ask(run_id, approved=approved, spec_path=self._spec_path)

    def load_events(self, run_id: str) -> list[dict[str, Any]]:
        return self.runtime.load_events(run_id)

    def prove(self, run_id: str) -> dict[str, Any]:
        events = self.load_events(run_id)
        evidence: list[dict[str, Any]] = []
        evidence_blobs: dict[str, bytes] = {}
        bundle_path = self.runtime.runs_dir / run_id / "proof-bundle.json"
        if bundle_path.exists():
            return json.loads(bundle_path.read_text(encoding="utf-8"))

        policy_decisions = [
            e["payload"]["decision"]
            for e in events
            if e.get("eventType") == "PolicyEvaluated"
        ]
        for e in events:
            if e.get("eventType") != "EvidenceAttached":
                continue
            eid = e["payload"]["evidenceId"]
            meta, blob = self.runtime.evidence_store.load(eid)
            evidence.append(meta)
            evidence_blobs[eid] = blob

        vap = run_vap_pipeline(
            agent_id=self.spec.agent_id,
            run_id=run_id,
            events=events,
            evidence=evidence,
            evidence_blobs=evidence_blobs,
            policy_decisions=policy_decisions,
        )
        write_proof_bundle(bundle_path, vap["proofBundle"])
        return vap["proofBundle"]

    def audit(self, run_id: str) -> dict[str, Any]:
        events = self.load_events(run_id)
        policy_decisions = [
            e["payload"]["decision"] for e in events if e.get("eventType") == "PolicyEvaluated"
        ]
        return audit_run(
            agent_id=self.spec.agent_id,
            run_id=run_id,
            events=events,
            policy_decisions=policy_decisions,
        )

    def passport(self, *, run_id: str | None = None, refresh: bool = False) -> dict[str, Any]:
        if refresh or run_id is None:
            return refresh_passport(
                spec=self.spec,
                workspace=self.workspace,
                runtime_runs=self.runtime.list_runs(),
                load_events_fn=self.runtime.load_events,
            )
        events = self.load_events(run_id)
        bundle_path = self.runtime.runs_dir / run_id / "proof-bundle.json"
        trust = None
        if bundle_path.exists():
            trust = json.loads(bundle_path.read_text(encoding="utf-8")).get("trustScore")
        from .passport import build_passport, observed_capabilities

        return build_passport(
            spec=self.spec,
            identity=IdentityStore(self.workspace).load(),
            trust_score=trust,
            derived_from=events[-1].get("eventHash") if events else None,
            observed=observed_capabilities(events),
            history={
                "runCount": 1,
                "successCount": 1 if any(e.get("eventType") == "Completed" for e in events) else 0,
                "failureCount": 1 if any(e.get("eventType") == "Failed" for e in events) else 0,
                "violationCount": 0,
                "lastRunAt": events[-1].get("ts") if events else None,
                "lastRunId": run_id,
            },
        )

    def register(self) -> dict[str, Any]:
        if not self._spec_path:
            raise ValueError("register requires Agent created from spec file")
        IdentityStore(self.workspace).issue(self.spec)
        return AgentRegistry(self.workspace).register(self._spec_path, workspace=self.workspace)

    def marketplace_index(self) -> dict[str, list[dict]]:
        return Marketplace(self.workspace).index()

    def verify_bundle(self, bundle: dict[str, Any]) -> tuple[bool, list[str]]:
        return verify_proof_bundle(bundle)
