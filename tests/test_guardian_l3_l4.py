"""Guardian L3 Collective Defense + L4 Constitution/Council tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class CollectiveDefenseTest(unittest.TestCase):
    def test_opt_in_publish_match_apply(self) -> None:
        from uap.capability_gov import CapabilityGovernor
        from uap.collective import CollectiveDefense

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            cd = CollectiveDefense(ws)
            with self.assertRaises(PermissionError):
                cd.publish_from_threat({"patterns": ["spawn_storm"], "riskBand": "critical"})

            cd.set_opt_in(True)
            sig = cd.publish_from_threat(
                {
                    "patterns": ["spawn_storm", "deep_delegation"],
                    "riskScore": 0.9,
                    "riskBand": "critical",
                    "recommendation": "restrict",
                }
            )
            self.assertTrue(sig["signatureId"].startswith("sig_"))
            self.assertIn("patternHash", sig)
            self.assertNotIn("sessionId", sig)

            hits = cd.match(patterns=["spawn_storm"])
            self.assertEqual(len(hits), 1)

            out = cd.apply(sig["signatureId"], agent_id="agent_bad")
            self.assertTrue(out["ok"])

            gov = CapabilityGovernor(ws).evaluate(
                capability="create.agent", agent_id="agent_bad", profile="guardian"
            )
            self.assertEqual(gov["decision"], "deny")
            self.assertTrue(any("collective" in r for r in gov["reasons"]))


class DomainGlobalKillTest(unittest.TestCase):
    def test_domain_kill_blocks_agents(self) -> None:
        from uap.kill import KillStore

        with tempfile.TemporaryDirectory() as td:
            store = KillStore(td)
            entry = store.issue_domain(domain_id="acme", reason="breach")
            self.assertEqual(entry["tier"], "domain")
            # without NARNA_ORG_ID matching, domain check uses env default "local"
            # set domain via env for is_agent_killed path
            import os

            os.environ["NARNA_ORG_ID"] = "acme"
            try:
                killed = store.is_agent_killed("any_agent")
                self.assertIsNotNone(killed)
                self.assertEqual(killed["tier"], "domain")
            finally:
                os.environ.pop("NARNA_ORG_ID", None)

    def test_global_via_council_quorum(self) -> None:
        from uap.council import GovernanceCouncil
        from uap.kill import KillStore

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            council = GovernanceCouncil(ws)
            council.install_default()
            prop = council.propose(
                kind="global_kill",
                payload={"reason": "emergency"},
                proposed_by="chair",
            )
            self.assertEqual(prop["status"], "open")
            # quorum=2 — second approval executes
            passed = council.approve(prop["proposalId"], member_id="security")
            self.assertEqual(passed["status"], "passed")
            g = KillStore(ws).is_global_killed()
            self.assertIsNotNone(g)
            self.assertEqual(g["tier"], "global")
            self.assertIsNotNone(KillStore(ws).is_agent_killed("anyone"))


class ConstitutionCouncilTest(unittest.TestCase):
    def test_constitution_deny_and_agent_cannot_amend(self) -> None:
        from uap.council import GovernanceCouncil, GuardianConstitution

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            gc = GuardianConstitution(ws)
            gc.install_default()
            out = gc.evaluate(action="harm.human", agent_id="bot")
            self.assertEqual(out["decision"], "deny")
            self.assertEqual(out["principleId"], "protect-life")
            self.assertFalse(gc.agent_may_amend())

            allow = gc.evaluate(action="search.web")
            self.assertEqual(allow["decision"], "allow")

            council = GovernanceCouncil(ws)
            council.install_default()
            with self.assertRaises(PermissionError):
                council.propose(
                    kind="amend_constitution",
                    payload={"yaml": "kind: GuardianConstitution\nspec: {}\n"},
                    proposed_by="agent_bot",
                )

    def test_council_amend_constitution(self) -> None:
        from uap.council import GovernanceCouncil, GuardianConstitution

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            GuardianConstitution(ws).install_default()
            council = GovernanceCouncil(ws)
            council.install_default()
            new_yaml = """kind: GuardianConstitution
apiVersion: narna.org/v1
metadata:
  name: amended
  version: "0.2.0"
spec:
  agentAmend: false
  amendableBy: council
  levels:
    - level: 0
      id: protect-life
      principle: Protect human life
      effect: deny
      actions: [harm.human]
    - level: 9
      id: no-coffee
      principle: No unauthorized coffee orders
      effect: deny
      actions: [order.coffee]
"""
            prop = council.propose(
                kind="amend_constitution",
                payload={"yaml": new_yaml},
                proposed_by="chair",
            )
            council.approve(prop["proposalId"], member_id="ethics")
            out = GuardianConstitution(ws).evaluate(action="order.coffee")
            self.assertEqual(out["decision"], "deny")
            self.assertEqual(out["principleId"], "no-coffee")


if __name__ == "__main__":
    unittest.main()
