"""Tests for Decision OS / DecisionEngine (NGS-0014)."""

from __future__ import annotations

import unittest
from pathlib import Path

from uap.decision import DecisionEngine

REPO = Path(__file__).resolve().parents[1]
LEGAL = REPO / "specs" / "examples" / "packages" / "legal-decision.yaml"


class DecisionEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine(REPO)

    def test_contract_sign_without_evidence_denies_or_asks(self) -> None:
        out = self.engine.evaluate(
            action="contract.sign",
            question="Should we sign this contract?",
            path=LEGAL,
            evidence_present=[],
        )
        self.assertIn(out["decision"], {"deny", "ask"})
        self.assertGreaterEqual(out["riskScore"], 0.7)
        self.assertTrue(out["reasons"])
        self.assertTrue(out["requiredApprovals"])
        self.assertTrue(out["evidence"])
        self.assertEqual(out["auditRef"]["standard"], "NGS-0014")
        self.assertIn("pkg_legal_decision", str(out.get("packageId")))

    def test_contract_review_allows(self) -> None:
        out = self.engine.evaluate(
            action="contract.review",
            path=LEGAL,
            evidence_present=["policy.decision", "human.review", "contract.hash"],
        )
        self.assertEqual(out["decision"], "allow")
        self.assertLess(out["riskScore"], 0.9)

    def test_provider_resolve_legal_decision(self) -> None:
        out = self.engine.evaluate(
            action="contract.review",
            provider="legal-decision",
        )
        self.assertEqual(out["provider"], "legal-decision")
        self.assertTrue(out.get("ok"))


if __name__ == "__main__":
    unittest.main()
