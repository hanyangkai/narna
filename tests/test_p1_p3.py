from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class AdaptersP1Test(unittest.TestCase):
    def test_openai_adapter_wraps_run(self) -> None:
        from narna import wrap

        class FakeOpenAIAgent:
            def __init__(self) -> None:
                self.calls = 0

            def run(self, prompt: str) -> str:
                self.calls += 1
                return f"ok:{prompt}"

        FakeOpenAIAgent.__module__ = "agents.agent"

        with tempfile.TemporaryDirectory() as td:
            foreign = FakeOpenAIAgent()
            agent = wrap(foreign, workspace=td, vap=False)
            self.assertEqual(agent._adapter["package"], "narna-openai")
            out = foreign.run("hello")
            self.assertEqual(out, "ok:hello")
            self.assertEqual(foreign.calls, 1)
            self.assertTrue(agent.runtime.list_runs())

    def test_langgraph_adapter_detect(self) -> None:
        from narna.adapters import detect_framework

        class CompiledStateGraph:
            pass

        CompiledStateGraph.__module__ = "langgraph.graph.graph"
        self.assertEqual(detect_framework(CompiledStateGraph()), "langgraph")


class FleetAndBenchmarkTest(unittest.TestCase):
    def test_fleet_role_deny(self) -> None:
        from uap.fleet import load_fleet, member_role, role_can

        fleet = load_fleet(REPO / "specs" / "examples" / "fleet.yaml")
        role = member_role(fleet, "tool_browser_01")
        self.assertEqual(role, "restricted")
        self.assertFalse(role_can(fleet, role, "wallet.transfer"))
        self.assertTrue(role_can(fleet, role, "run"))

    def test_governance_leaderboard(self) -> None:
        from uap.governance_benchmark import leaderboard

        board = leaderboard()
        self.assertGreaterEqual(len(board["rows"]), 3)
        self.assertIn("algorithm", board)


if __name__ == "__main__":
    unittest.main()
