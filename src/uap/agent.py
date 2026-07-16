from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import audit_run
from .identity import IdentityStore
from .ids import new_id
from .marketplace import Marketplace
from .passport import refresh_passport
from .proof import write_proof_bundle
from .registry import AgentRegistry
from .runtime import LocalRuntime, RunResult
from .spec import AgentSpec, load_agent_spec
from .vap.pipeline import run_vap_pipeline
from .verify import verify_proof_bundle


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_spec(*, name: str, agent_id: str, creator: str = "local") -> AgentSpec:
    return AgentSpec(
        raw={
            "apiVersion": "uap.dev/v1alpha1",
            "kind": "Agent",
            "metadata": {
                "id": agent_id,
                "name": name,
                "version": "0.1.0",
                "creator": creator,
                "createdAt": _now_rfc3339(),
            },
            "spec": {
                "capability": ["general"],
                "permissions": [],
                "tools": [],
                "policy": {"ref": "local-default@0.0.0"},
            },
        }
    )


class Agent:
    """NARNA / UAP agent — works offline with zero config.

    Phase 1::

        from narna import Agent
        agent = Agent()
        agent.run()

    Phase 2::

        agent.enable_vap()
        result = agent.run("btc price")
        print(result.trust_score)
    """

    def __init__(
        self,
        name: str | None = None,
        *,
        spec_path: str | Path | None = None,
        workspace: str | Path | None = None,
        auto_init: bool = True,
        vap: bool = False,
    ) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.runtime = LocalRuntime(self.workspace)
        self._spec_path = Path(spec_path) if spec_path else None
        self._vap_enabled = False
        self._wrapped: Any = None
        self.last_vap: dict[str, Any] | None = None
        self.last_result: RunResult | None = None

        if auto_init:
            self.runtime.init()

        if vap:
            self.enable_vap(True)

        if spec_path is not None:
            self.spec = load_agent_spec(spec_path)
        else:
            agent_name = name or "Agent"
            # Reuse persisted local identity if present
            store = IdentityStore(self.workspace)
            existing = None
            try:
                existing = store.load()
            except Exception:
                existing = None

            if existing and existing.get("agentId"):
                agent_id = str(existing["agentId"])
            else:
                agent_id = new_id("agent")

            self.spec = _default_spec(name=agent_name, agent_id=agent_id)
            # Persist a minimal agent.yaml so CLI / registry can find it
            if self._spec_path is None:
                yaml_path = self.workspace / "agent.yaml"
                if not yaml_path.exists():
                    self._write_minimal_yaml(yaml_path)
                self._spec_path = yaml_path if yaml_path.exists() else None

            try:
                store.issue(self.spec)
            except Exception:
                pass

    def _write_minimal_yaml(self, path: Path) -> None:
        import yaml

        path.write_text(
            yaml.safe_dump(self.spec.raw, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    @classmethod
    def from_spec(cls, spec_path: str | Path, *, workspace: str | Path | None = None) -> "Agent":
        return cls(spec_path=spec_path, workspace=workspace)

    def enable_vap(self, enabled: bool = True) -> "Agent":
        """Phase 2: Verify → Audit → Prove on every action and at run end.

        When enabled:
        - Each tool action with evidence is verified immediately (hash, freshness, …)
        - Run completion runs the full VAP pipeline
        - ``result.trust_score`` / ``agent.last_vap`` are populated
        """
        self._vap_enabled = enabled
        self.runtime.enable_vap(enabled)
        return self

    def run(self, input: str | None = None, *, auto_approve_ask: bool = False) -> RunResult:
        result = self.runtime.run(
            self.spec,
            user_input=input,
            auto_approve_ask=auto_approve_ask,
            spec_path=self._spec_path,
        )
        self.last_result = result
        if result.vap is not None:
            self.last_vap = result.vap
        return result

    def resolve_ask(self, run_id: str, *, approved: bool) -> RunResult:
        if not self._spec_path:
            raise ValueError("resolve_ask requires Agent with a spec file")
        result = self.runtime.resolve_ask(run_id, approved=approved, spec_path=self._spec_path)
        self.last_result = result
        if result.vap is not None:
            self.last_vap = result.vap
        return result

    def vap_report(self, run_id: str | None = None) -> dict[str, Any]:
        """Return the latest VAP report (or load proof-bundle for a run)."""
        if run_id is None:
            if self.last_vap is not None:
                return {
                    "trustScore": self.last_vap.get("trustScore"),
                    "audit": self.last_vap.get("audit"),
                    "verifications": self.last_vap.get("verifications"),
                    "proofBundle": self.last_vap.get("proofBundle"),
                }
            if self.last_result is not None:
                run_id = self.last_result.run_id
            else:
                raise ValueError("no VAP report — call enable_vap() then run()")
        bundle_path = self.runtime.runs_dir / run_id / "proof-bundle.json"
        if not bundle_path.exists():
            bundle = self.prove(run_id)
            return {"proofBundle": bundle, "trustScore": bundle.get("trustScore")}
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        return {
            "proofBundle": bundle,
            "trustScore": bundle.get("trustScore"),
            "audit": bundle.get("audit"),
            "verifications": bundle.get("verifications"),
        }

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

    def publish(
        self,
        *,
        remote: bool = True,
        category: str | None = None,
        registry_url: str | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        """Phase 3: publish agent to Registry (local + optional remote).

        Example::

            agent.enable_vap()
            agent.run("btc price")
            agent.publish()
        """
        import os

        IdentityStore(self.workspace).issue(self.spec)
        passport = self.passport(refresh=True)

        if self._spec_path and Path(self._spec_path).exists():
            spec_path = Path(self._spec_path)
        else:
            spec_path = self.workspace / "agent.yaml"
            self._write_minimal_yaml(spec_path)
            self._spec_path = spec_path

        entry = AgentRegistry(self.workspace).register(
            spec_path,
            workspace=self.workspace,
            passport=passport,
            category=category,
        )
        Marketplace(self.workspace).index()
        Marketplace(self.workspace).trending()

        result: dict[str, Any] = {
            **entry,
            "status": "local",
            "passportUrl": f"local://passport/{entry['agentId']}",
            "message": "Published to local NARNA Registry.",
        }

        if remote:
            base = (
                registry_url
                or os.environ.get("NARNA_REGISTRY_URL")
                or os.environ.get("UAP_CLOUD_URL")
                or ""
            ).rstrip("/")
            key = api_key or os.environ.get("NARNA_REGISTRY_KEY") or os.environ.get("UAP_CLOUD_KEY") or ""
            if base:
                try:
                    from uap_cloud.exporter import publish_agent

                    remote_resp = publish_agent(
                        listing=entry,
                        passport=passport,
                        api_key=key or "uap_live_dev_local_key_change_in_prod",
                        base_url=base,
                    )
                    result["status"] = "published"
                    result["remote"] = remote_resp
                    result["passportUrl"] = remote_resp.get(
                        "passportUrl", f"{base}/v1/passport/{entry['agentId']}"
                    )
                    result["message"] = "Published to local + remote NARNA Registry."
                except Exception as e:
                    result["remoteError"] = str(e)
                    result["message"] = (
                        "Published locally. Remote registry unavailable "
                        f"({e}). Set NARNA_REGISTRY_URL / UAP_CLOUD_URL to sync."
                    )

        return result

    def register(self) -> dict[str, Any]:
        return self.publish(remote=False)

    def marketplace_index(self) -> dict[str, list[dict]]:
        return Marketplace(self.workspace).index()

    def registry_search(self, *, capability: str | None = None, q: str | None = None) -> list[dict]:
        return AgentRegistry(self.workspace).search(capability=capability, q=q)

    def registry_trending(self, *, category: str | None = None, limit: int = 20) -> list[dict]:
        return Marketplace(self.workspace).trending(category=category, limit=limit)

    def verify_bundle(self, bundle: dict[str, Any]) -> tuple[bool, list[str]]:
        return verify_proof_bundle(bundle)
