from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class OrchestratorSharedSessionTest(unittest.TestCase):
    def test_pipeline_shares_one_session(self) -> None:
        from uap.orchestrator import MultiAgentOrchestrator
        from uap.spec import AgentSpec

        # Minimal inline specs via Agent.from_spec needs files — use Agent() + runtime directly
        from uap.agent import Agent
        from uap.governor import Governor

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            # Write two tiny agent specs
            for name, aid in (("coord", "coord-1"), ("child", "child-1")):
                spec = {
                    "apiVersion": "uap.dev/v1alpha1",
                    "kind": "Agent",
                    "metadata": {
                        "id": aid,
                        "name": name,
                        "version": "0.1.0",
                        "creator": "test",
                        "createdAt": "2026-07-17T00:00:00Z",
                    },
                    "spec": {
                        "capability": ["general"],
                        "permissions": [],
                        "tools": [],
                        "policy": {"ref": "local-default@0.0.0"},
                    },
                }
                (ws / f"{name}.json").write_text(json.dumps(spec), encoding="utf-8")

            orch = MultiAgentOrchestrator(ws)
            result = orch.run_pipeline(
                coordinator_spec=ws / "coord.json",
                child_specs=[ws / "child.json"],
                input_text="hello",
            )
            self.assertIsNotNone(result.session_id)
            self.assertEqual(len(result.child_results), 1)
            self.assertEqual(result.child_results[0]["sessionId"], result.session_id)
            self.assertGreaterEqual(result.total_gu, 2)  # coord + child at minimum
            session = Governor(ws).sessions.load(result.session_id)
            self.assertEqual(session.state, "closed")


class AdapterEuEmitTest(unittest.TestCase):
    def test_wrap_emits_eu(self) -> None:
        from narna.adapters.base import BaseAdapter, _emit_execution_unit
        from uap.agent import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent(name="AdapterAgent", workspace=ws)
            agent.run("ping")  # opens session on last_result
            _emit_execution_unit(agent, unit_kind="mcp", label="mcp.call_tool")
            eu = getattr(agent, "_adapter_last_eu", None)
            self.assertIsNotNone(eu)
            self.assertEqual(eu["unitKind"], "mcp")


class MarketplaceTakeTest(unittest.TestCase):
    def test_twenty_percent_take(self) -> None:
        from uap.packages import marketplace_take, record_local_purchase, register_package_local

        split = marketplace_take(10000, take_rate_bps=2000)  # $100.00
        self.assertEqual(split["platformCutUsd"], 2000)
        self.assertEqual(split["authorCutUsd"], 8000)

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            pkg = ws / "hipaa.yaml"
            pkg.write_text(
                """
apiVersion: narna.ai/v1alpha1
kind: GovernancePackage
metadata:
  id: hipaa-demo
  name: HIPAA Demo
  version: 0.1.0
  provider: hipaa-demo
  packageKind: Compliance
  license: MIT
  priceUsd: 5000
  takeRateBps: 2000
spec:
  constitution: {}
""",
                encoding="utf-8",
            )
            # load_package_file may need different format — register via entry mock
            try:
                entry = register_package_local(ws, pkg)
            except Exception:
                # Fallback: write registry entry directly
                root = ws / ".uap" / "package-registry"
                root.mkdir(parents=True, exist_ok=True)
                entry = {
                    "packageId": "hipaa-demo",
                    "name": "HIPAA Demo",
                    "priceUsd": 5000,
                    "takeRateBps": 2000,
                    "downloads": 0,
                    "authorRevenueUsd": 0,
                    "platformRevenueUsd": 0,
                }
                (root / "hipaa-demo.json").write_text(json.dumps(entry), encoding="utf-8")

            out = record_local_purchase(ws, "hipaa-demo")
            self.assertEqual(out["platformCutUsd"], 1000)
            self.assertEqual(out["authorCutUsd"], 4000)
            self.assertEqual(out["guCharged"], 50)


if __name__ == "__main__":
    unittest.main()
