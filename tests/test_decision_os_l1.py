"""Decision OS L1 modules — Connect · Knowledge · Memory · Automation · Marketplace."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class ConnectKnowledgeMemoryTest(unittest.TestCase):
    def test_context_flows_into_decision(self) -> None:
        from uap.connect import ConnectRegistry
        from uap.decision import DecisionEngine
        from uap.durable_memory import DurableMemory
        from uap.knowledge import KnowledgeGraph

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            conn = ConnectRegistry(ws).register(
                type="crm", name="HubSpot stub", endpoint="https://api.hubspot.example"
            )
            self.assertTrue(conn["connectorId"].startswith("conn_"))
            probe = ConnectRegistry(ws).probe(conn["connectorId"])
            self.assertTrue(probe["ok"])

            kg = KnowledgeGraph(ws)
            cust = kg.upsert_entity(kind="customer", name="Acme Legal")
            contract = kg.upsert_entity(kind="contract", name="Acme MSA 2026")
            kg.relate(from_id=cust["entityId"], to_id=contract["entityId"], rel_type="party_to")

            DurableMemory(ws).put(
                scope="customer",
                scope_id="Acme Legal",
                records={"riskNotes": "prior litigation", "tier": "enterprise"},
            )

            out = DecisionEngine(ws).evaluate(
                action="approve.contract",
                context={"customer": "Acme Legal", "contract": "Acme MSA"},
            )
            self.assertIn("context", out)
            self.assertGreaterEqual(out["context"]["knowledge"]["count"], 1)
            self.assertTrue(any("knowledge context" in r for r in (out.get("reasons") or [])))
            self.assertTrue(any("memory context" in r for r in (out.get("reasons") or [])))


class AutomationMarketplaceTest(unittest.TestCase):
    def test_automate_and_dmarket(self) -> None:
        from uap.automation import AutomationEngine
        from uap.decision_market import DecisionMarketplace

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            run = AutomationEngine(ws).run(
                trigger="email.inbound",
                action="approve.contract",
            )
            self.assertIn(run["status"], {"ready_to_execute", "awaiting_approval", "blocked"})
            self.assertTrue(run["runId"].startswith("auto_"))

            pkgs = DecisionMarketplace(ws).list_packages()
            self.assertTrue(any("legal" in (p.get("provider") or p.get("name") or "").lower() for p in pkgs) or len(pkgs) >= 1)
            inst = DecisionMarketplace(ws).install("legal-decision")
            self.assertTrue(inst["ok"])


if __name__ == "__main__":
    unittest.main()
