"""Tier D — CTI hub, council bindings, reputation network."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class CTIHubTest(unittest.TestCase):
    def test_submit_feed_pull(self) -> None:
        from uap.collective import CollectiveDefense
        from uap.cti_hub import CTIHub

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            CollectiveDefense(ws).set_opt_in(True)
            hub = CTIHub(ws)
            out = hub.submit(
                {
                    "signatureId": "sig_test1",
                    "patterns": ["spawn_storm"],
                    "riskBand": "critical",
                },
                require_opt_in=False,
            )
            self.assertTrue(out["ok"])
            feed = hub.feed_list()
            self.assertEqual(len(feed), 1)
            pulled = hub.pull_into_workspace()
            self.assertEqual(pulled["imported"], 1)


class CouncilBindingTest(unittest.TestCase):
    def test_seal_on_quorum(self) -> None:
        from uap.council import GovernanceCouncil
        from uap.council_binding import CouncilBinding

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            c = GovernanceCouncil(ws)
            c.install_default()
            prop = c.propose(
                kind="domain_kill",
                payload={"domainId": "acme", "reason": "test"},
                proposed_by="chair",
            )
            passed = c.approve(prop["proposalId"], member_id="security")
            self.assertEqual(passed["status"], "passed")
            self.assertIn("binding", passed)
            bid = passed["binding"]["bindingId"]
            verify = CouncilBinding(ws).verify(bid)
            self.assertTrue(verify["ok"])


class ReputationNetworkTest(unittest.TestCase):
    def test_export_import_peer(self) -> None:
        from uap.reputation import ReputationStore

        with tempfile.TemporaryDirectory() as ta, tempfile.TemporaryDirectory() as tb:
            a = ReputationStore(ta)
            a.add_violation("bad_bot", kind="exfil", severity=1.0)
            a.add_violation("bad_bot", kind="spawn", severity=0.9)
            digest = a.export_digest("bad_bot")
            self.assertEqual(digest["kind"], "ReputationDigestBundle")
            self.assertTrue(digest["digests"])
            self.assertLess(digest["digests"][0]["scoreBucket"], 50)

            b = ReputationStore(tb)
            before = b.get("local_agent")["score"]
            out = b.import_digest(digest, map_to_agent="local_agent")
            self.assertGreaterEqual(out["applied"], 1)
            after = b.get("local_agent")
            self.assertLess(after["score"], before)


if __name__ == "__main__":
    unittest.main()
