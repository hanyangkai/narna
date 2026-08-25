"""Tier D slice 2 — CTI mesh, jurisdictions, isolation partners."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class CTIMeshLocalTest(unittest.TestCase):
    def test_hubs_config(self) -> None:
        from uap.cti_mesh import CTIMesh

        with tempfile.TemporaryDirectory() as td:
            mesh = CTIMesh(td)
            out = mesh.set_hubs(["https://api.narna.org", "http://127.0.0.1:8100"])
            self.assertEqual(len(out["hubs"]), 2)
            self.assertEqual(mesh.list_hubs()[0], "https://api.narna.org")


class JurisdictionTest(unittest.TestCase):
    def test_list_and_apply(self) -> None:
        from uap.council import GovernanceCouncil
        from uap.jurisdiction import JurisdictionTemplates

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            jt = JurisdictionTemplates(ws)
            ids = {j["id"] for j in jt.list()}
            self.assertIn("eu-gdpr", ids)
            self.assertIn("us-enterprise", ids)
            self.assertIn("vn-pdpa", ids)

            c = GovernanceCouncil(ws)
            c.install_default()
            prop = c.propose(
                kind="domain_kill",
                payload={"domainId": "x", "reason": "t"},
                proposed_by="chair",
            )
            passed = c.approve(prop["proposalId"], member_id="ethics")
            enriched = jt.apply_to_binding(passed["binding"], jurisdiction_id="vn-pdpa")
            self.assertEqual(enriched["jurisdiction"]["id"], "vn-pdpa")
            self.assertTrue(enriched["jurisdiction"]["clauses"])


class IsolationPartnerTest(unittest.TestCase):
    def test_docker_and_k8s_plans(self) -> None:
        from uap.isolation_partner import IsolationRegistry

        with tempfile.TemporaryDirectory() as td:
            reg = IsolationRegistry(td)
            self.assertGreaterEqual(len(reg.list()), 2)
            d = reg.plan("docker", agent_id="a1")
            self.assertEqual(d["partner"], "docker")
            self.assertIn("--network", d["plan"]["argv"])
            k = reg.plan("kubernetes", agent_id="a1")
            self.assertEqual(k["networkPolicy"]["kind"], "NetworkPolicy")
            applied = reg.apply("kubernetes", agent_id="a1", dry_run=True)
            self.assertTrue(applied["dryRun"])


if __name__ == "__main__":
    unittest.main()
