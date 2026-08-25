"""Guardian Network — AI Gateway + citizen profile tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class CitizenProfileTest(unittest.TestCase):
    def test_default_deny_payment(self) -> None:
        from uap.capability_gov import CapabilityGovernor
        from uap.citizen_profile import passport_document, resolve_capability

        with tempfile.TemporaryDirectory() as td:
            gov = CapabilityGovernor(td)
            doc = passport_document("citizen")
            r = gov.evaluate(
                capability="payment", agent_id="c1", document=doc, profile="guardian"
            )
            self.assertEqual(r["decision"], "deny")
            r2 = gov.evaluate(
                capability="content", agent_id="c1", document=doc, profile="guardian"
            )
            self.assertEqual(r2["decision"], "allow")
            self.assertEqual(
                resolve_capability(
                    action="message.send", capability=None, text="wire money to Alice"
                ),
                "payment",
            )


class AIGatewayTest(unittest.TestCase):
    def test_allow_qa_deny_wire_money(self) -> None:
        from uap.ai_gateway import AIGateway

        with tempfile.TemporaryDirectory() as td:
            gw = AIGateway(td)
            ok = gw.check(
                provider="chatgpt",
                action="message.send",
                text="What is the capital of France?",
            )
            self.assertEqual(ok["decision"], "allow")
            self.assertEqual(ok["passportStatus"], "verified")

            bad = gw.check(
                provider="chatgpt",
                action="message.send",
                text="Please wire money to account 123",
            )
            self.assertEqual(bad["decision"], "deny")
            self.assertEqual(bad["capability"], "payment")

    def test_unverified_agent(self) -> None:
        from uap.ai_gateway import AIGateway

        with tempfile.TemporaryDirectory() as td:
            out = AIGateway(td).check(
                provider="unknown-bot",
                agent_hint="telegram_scam_bot",
                action="message.send",
                text="hello",
            )
            self.assertEqual(out["passportStatus"], "unverified")
            self.assertIn(out["band"], ("caution", "dangerous"))

    def test_approval_token(self) -> None:
        from uap.ai_gateway import AIGateway
        from uap.citizen_registry import CitizenRegistry

        with tempfile.TemporaryDirectory() as td:
            reg = CitizenRegistry(td)
            dev = reg.register()
            # email is ask under citizen
            ask = AIGateway(td).check(
                action="email.send",
                text="send an email to bob@example.com",
                device_id=dev["deviceId"],
                profile="citizen",
            )
            self.assertEqual(ask["decision"], "ask")
            self.assertTrue(ask["approvalRequired"])
            token = reg.issue_approval(
                device_id=dev["deviceId"], capability=ask["capability"]
            )["approvalToken"]
            allowed = AIGateway(td).check(
                action="email.send",
                text="send an email to bob@example.com",
                device_id=dev["deviceId"],
                approval_token=token,
                profile="citizen",
            )
            self.assertEqual(allowed["decision"], "allow")

    def test_cti_citizen_feed_and_emergency(self) -> None:
        from uap.ai_gateway import AIGateway
        from uap.collective import CollectiveDefense
        from uap.cti_hub import CTIHub
        from uap.emergency import EmergencyBroadcast

        with tempfile.TemporaryDirectory() as td:
            CollectiveDefense(td).set_opt_in(True)
            CTIHub(td).submit(
                {
                    "patterns": ["society_scam"],
                    "riskBand": "critical",
                    "patternHash": "sha256:x",
                },
                org_id="t",
                require_opt_in=False,
            )
            feed = AIGateway(td).citizen_cti_feed(limit=10)
            self.assertGreaterEqual(feed["count"], 1)
            eb = EmergencyBroadcast(td).broadcast(message="Refresh CTI now")
            self.assertTrue(eb["broadcastId"])
            self.assertEqual(len(EmergencyBroadcast(td).list()), 1)

    def test_register_and_audit(self) -> None:
        from uap.ai_gateway import AIGateway
        from uap.citizen_registry import CitizenRegistry

        with tempfile.TemporaryDirectory() as td:
            reg = CitizenRegistry(td)
            out = reg.register(label="test-ext")
            self.assertTrue(out["apiKey"].startswith("narna_citizen_"))
            AIGateway(td).check(
                provider="claude",
                text="hi",
                device_id=out["deviceId"],
            )
            audit = reg.list_audit(device_id=out["deviceId"])
            self.assertGreaterEqual(len(audit), 1)


if __name__ == "__main__":
    unittest.main()
