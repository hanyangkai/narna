from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SPEC = REPO_ROOT / "specs" / "examples" / "trading-agent.yaml"


def _setup_workspace(workspace: Path) -> None:
    if not (workspace / "policies").exists() and (REPO_ROOT / "policies").exists():
        shutil.copytree(REPO_ROOT / "policies", workspace / "policies")


class Phase2VapTest(unittest.TestCase):
    def test_vap_off_by_default_no_proof(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent(workspace=ws)
            result = agent.run("hello")
            self.assertEqual(result.state, "Completed")
            self.assertFalse(result.vap_enabled)
            self.assertIsNone(result.trust_score)
            proof = ws / ".uap" / "runs" / result.run_id / "proof-bundle.json"
            self.assertFalse(proof.exists())

    def test_enable_vap_produces_trust_and_proof(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("Researcher", workspace=ws)
            agent.enable_vap()
            result = agent.run("hello")
            self.assertEqual(result.state, "Completed")
            self.assertTrue(result.vap_enabled)
            self.assertIsNotNone(result.trust_score)
            self.assertIsNotNone(result.audit_id)
            self.assertTrue(result.proof_path and result.proof_path.exists())
            self.assertIsNotNone(agent.last_vap)
            report = agent.vap_report()
            self.assertIn("trustScore", report)

    def test_vap_constructor_flag(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("Fast", workspace=ws, vap=True)
            result = agent.run()
            self.assertTrue(result.vap_enabled)
            self.assertIsNotNone(result.trust_score)

    def test_action_level_verify_on_tool(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            _setup_workspace(ws)
            agent = Agent.from_spec(EXAMPLE_SPEC, workspace=ws)
            agent.enable_vap()
            result = agent.run(input="btc price")
            self.assertEqual(result.state, "Completed")
            self.assertIsNotNone(result.trust_score)
            events = agent.load_events(result.run_id)
            action_verified = [
                e
                for e in events
                if e.get("eventType") == "Verified"
                and (e.get("payload") or {}).get("scope") == "action"
            ]
            self.assertGreaterEqual(len(action_verified), 1)
            # hash_match should be valid for attached evidence
            statuses = [
                e["payload"]["verification"]["status"]
                for e in action_verified
                if e["payload"]["verification"]["verifierId"] == "hash_match"
            ]
            self.assertTrue(statuses)
            self.assertIn("valid", statuses)


if __name__ == "__main__":
    unittest.main()
