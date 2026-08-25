"""Guardian completeness — Reputation, Container, Kill cascade, Federation, rich threats."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class ReputationTest(unittest.TestCase):
    def test_violation_tightens_capability(self) -> None:
        from uap.capability_gov import CapabilityGovernor
        from uap.reputation import ReputationStore

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            store = ReputationStore(ws)
            store.record("bot", origin="unknown", attested=False)
            store.add_violation("bot", kind="exfil", severity=1.0)
            store.add_violation("bot", kind="spawn_storm", severity=0.8)
            rep = store.get("bot")
            self.assertLess(rep["score"], 45)
            self.assertIn(rep["band"], {"low", "critical"})

            out = CapabilityGovernor(ws).evaluate(
                capability="search", agent_id="bot", profile="guardian"
            )
            # search default allow → reputation floor raises
            self.assertIn(out["decision"], {"deny", "restricted", "ask"})
            self.assertTrue(any("reputation" in r for r in out["reasons"]))

    def test_no_self_assert_without_attestation(self) -> None:
        from uap.reputation import ReputationStore

        with tempfile.TemporaryDirectory() as td:
            store = ReputationStore(td)
            with self.assertRaises(PermissionError):
                store.add_feedback("bot", score=100, by="bot")


class ContainerTest(unittest.TestCase):
    def test_spawn_depth_quota(self) -> None:
        from uap.container import AgentContainer

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            c = AgentContainer(ws)
            c.install_default()
            ok = c.check(agent_id="a1", action="create.agent", spawn_depth=1)
            self.assertEqual(ok["decision"], "allow")
            bad = c.check(agent_id="a1", action="create.agent", spawn_depth=5)
            self.assertEqual(bad["decision"], "deny")


class KillCascadeTest(unittest.TestCase):
    def test_cascade_freezes_container(self) -> None:
        from uap.container import AgentContainer
        from uap.kill import KillStore

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            AgentContainer(ws).install_default()
            entry = KillStore(ws).issue_local(agent_id="x", reason="cascade-test")
            self.assertIn("cascade", entry)
            steps = [s["step"] for s in entry["cascade"]["steps"]]
            self.assertIn("capability_revoked", steps)
            self.assertIn("mcp_disconnected", steps)
            self.assertIn("memory_frozen", steps)
            self.assertIn("network_isolated", steps)
            frozen = AgentContainer(ws).is_frozen("x")
            self.assertTrue(frozen and frozen.get("memoryFrozen"))
            chk = AgentContainer(ws).check(agent_id="x", action="mcp.call", tool="mcp", network=True)
            self.assertEqual(chk["decision"], "deny")


class ThreatCatalogTest(unittest.TestCase):
    def test_exfil_and_scan_patterns(self) -> None:
        from uap.execution_graph import ExecutionGraph, GraphNode
        from uap.threat import ThreatEngine

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            session_dir = ws / ".uap" / "sessions" / "s1"
            session_dir.mkdir(parents=True)
            (session_dir / "session.json").write_text(
                '{"sessionId":"s1","logicalAgentId":"a0","state":"open"}',
                encoding="utf-8",
            )
            g = ExecutionGraph(session_dir)
            g.add_node(GraphNode("eu1", "network.scan", "a0"))
            g.add_node(GraphNode("eu2", "bulk.exfil.dump", "a0", parent_unit_id="eu1"))
            report = ThreatEngine(ws).analyze_graph(g, session_id="s1")
            self.assertIn("network_scanning", report["patterns"])
            self.assertIn("bulk_exfiltration", report["patterns"])
            self.assertGreaterEqual(report["riskScore"], 0.9)
            self.assertIn("credential_harvest", report["catalog"])  # catalog present


class FederationBundleTest(unittest.TestCase):
    def test_export_import_bundle(self) -> None:
        from uap.collective import CollectiveDefense

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            a = CollectiveDefense(ws)
            a.set_opt_in(True)
            sig = a.publish_from_threat(
                {"patterns": ["spawn_storm"], "riskBand": "high", "recommendation": "restrict"}
            )
            bundle = a.export_bundle()
            self.assertEqual(bundle["kind"], "CollectiveDefenseBundle")

            with tempfile.TemporaryDirectory() as td2:
                b = CollectiveDefense(td2)
                b.set_opt_in(True)
                out = b.import_bundle(bundle)
                self.assertEqual(out["imported"], 1)
                hits = b.match(patterns=["spawn_storm"])
                self.assertEqual(hits[0]["signatureId"], sig["signatureId"])


if __name__ == "__main__":
    unittest.main()
