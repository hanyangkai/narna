from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.agent import Agent
from uap.audit import audit_run
from uap.trust import compute_trust_score_v0
from uap.vap.pipeline import run_vap_pipeline
from uap.verify import verify_proof_bundle


REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "specs" / "examples" / "trading-agent.yaml"


def _setup_workspace(workspace: Path) -> None:
    import shutil

    if not (workspace / "policies").exists() and (REPO / "policies").exists():
        shutil.copytree(REPO / "policies", workspace / "policies")


class VapTest(unittest.TestCase):
    def test_vap_pipeline_and_trust_caps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            _setup_workspace(ws)
            agent = Agent.from_spec(SPEC, workspace=ws)
            result = agent.run(input="btc price")
            events = agent.load_events(result.run_id)
            policy = [e["payload"]["decision"] for e in events if e["eventType"] == "PolicyEvaluated"]
            vap = run_vap_pipeline(
                agent_id=agent.spec.agent_id,
                run_id=result.run_id,
                events=events,
                evidence=[],
                evidence_blobs={},
                policy_decisions=policy,
            )
            trust = vap["trustScore"]
            self.assertGreater(trust["score"], 0.5)
            ok, _ = verify_proof_bundle(vap["proofBundle"])
            self.assertTrue(ok)

    def test_audit_detects_sequence_gap(self) -> None:
        events = [
            {"sequence": 0, "eventType": "AgentStarted", "hashPrev": "sha256:" + "0" * 64},
            {"sequence": 2, "eventType": "Completed", "hashPrev": "sha256:" + "0" * 64},
        ]
        audit = audit_run(agent_id="a", run_id="r", events=events)
        self.assertTrue(any("sequence gap" in v for v in audit["violations"]))


if __name__ == "__main__":
    unittest.main()
