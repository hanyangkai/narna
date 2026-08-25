"""Guardian kill + threat + capability-in-adapter tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import yaml


class KillStoreTest(unittest.TestCase):
    def test_issue_and_block(self) -> None:
        from uap.kill import KillStore

        with tempfile.TemporaryDirectory() as td:
            store = KillStore(td)
            entry = store.issue_local(agent_id="agent_x", reason="test")
            self.assertTrue(entry["token"].startswith("kill_"))
            self.assertIsNotNone(store.is_agent_killed("agent_x"))
            store.revoke(entry["token"])
            self.assertIsNone(store.is_agent_killed("agent_x"))


class ThreatEngineTest(unittest.TestCase):
    def test_spawn_storm(self) -> None:
        from uap.execution_graph import ExecutionGraph, GraphNode
        from uap.threat import ThreatEngine

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            session_dir = ws / ".uap" / "sessions" / "session_test"
            session_dir.mkdir(parents=True)
            (session_dir / "session.json").write_text(
                '{"sessionId":"session_test","logicalAgentId":"a0","state":"open"}',
                encoding="utf-8",
            )
            g = ExecutionGraph(session_dir)
            parent = None
            for i in range(5):
                uid = f"eu_{i}"
                node = GraphNode(
                    unit_id=uid,
                    unit_kind="spawn",
                    logical_agent_id=f"agent_{i}",
                    parent_unit_id=parent,
                )
                g.add_node(node)
                parent = uid
            report = ThreatEngine(ws).analyze_graph(g, session_id="session_test")
            self.assertIn("spawn_storm", report["patterns"])
            self.assertGreaterEqual(report["riskScore"], 0.7)


class AdapterGuardianTest(unittest.TestCase):
    def test_guardian_blocks_email_ask(self) -> None:
        from narna.adapters.base import BaseAdapter, NarnaGovernanceDenied
        from uap.agent import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            os.environ["NARNA_ADAPTER_MODE"] = "enforce"
            os.environ["NARNA_GUARDIAN"] = "1"
            # default guardian passport: email=ask
            agent = Agent(name="GuardTest", workspace=ws)
            foreign = type("F", (), {})()
            foreign.send_email = lambda *a, **k: "sent"  # type: ignore

            adapter = BaseAdapter()
            adapter.id = "email"
            adapter._wrap_method(foreign, "send_email", agent)
            with self.assertRaises(NarnaGovernanceDenied):
                foreign.send_email("hi")
            os.environ.pop("NARNA_GUARDIAN", None)

    def test_killed_agent_blocked(self) -> None:
        from narna.adapters.base import BaseAdapter, NarnaGovernanceDenied
        from uap.agent import Agent
        from uap.kill import KillStore

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            os.environ["NARNA_ADAPTER_MODE"] = "enforce"
            os.environ.pop("NARNA_GUARDIAN", None)
            agent = Agent(name="DeadAgent", workspace=ws)
            KillStore(ws).issue_local(agent_id=agent.spec.agent_id, reason="test-kill")
            foreign = type("F", (), {})()
            foreign.invoke = lambda *a, **k: 1  # type: ignore
            adapter = BaseAdapter()
            adapter.id = "langgraph"
            adapter._wrap_method(foreign, "invoke", agent)
            with self.assertRaises(NarnaGovernanceDenied):
                foreign.invoke("x")


if __name__ == "__main__":
    unittest.main()
