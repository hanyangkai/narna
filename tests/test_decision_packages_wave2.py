"""Wave 2 — industry Decision Packages catalog + evaluate."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


PROVIDERS = [
    ("legal-decision", "contract.sign", ["policy.decision", "human.review", "contract.hash"], "ask"),
    ("procurement-decision", "po.approve", ["policy.decision", "human.review", "vendor.diligence"], "ask"),
    ("finance-decision", "wire.transfer", ["policy.decision", "human.review", "payment.authorization"], "ask"),
    ("hr-decision", "terminate.initiate", ["policy.decision", "human.review"], "ask"),
    ("hospital-decision", "phi.disclose", ["policy.decision", "human.review", "clinical.indication"], "ask"),
    ("crypto-decision", "withdrawal.release", ["policy.decision", "human.review", "aml.screen"], "ask"),
]


class IndustryDecisionPackagesTest(unittest.TestCase):
    def test_catalog_has_six_decision_packages(self) -> None:
        from uap.decision_market import DecisionMarketplace

        pkgs = DecisionMarketplace(Path.cwd()).list_packages(decisions_only=True)
        providers = {p["provider"] for p in pkgs}
        for name, _, _, _ in PROVIDERS:
            self.assertIn(name, providers)
        self.assertGreaterEqual(len(pkgs), 6)

    def test_each_industry_pack_evaluates(self) -> None:
        from uap.decision import DecisionEngine
        from uap.decision_market import DecisionMarketplace

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            mp = DecisionMarketplace(ws)
            for provider, action, evidence, expect in PROVIDERS:
                mp.install(provider)
                out = DecisionEngine(ws).evaluate(
                    action=action,
                    provider=provider,
                    evidence_present=evidence,
                )
                self.assertEqual(
                    out["decision"],
                    expect,
                    msg=f"{provider} {action} → {out.get('decision')} reasons={out.get('reasons')}",
                )
                self.assertIn("riskScore", out)

            # missing evidence still denies guarded actions
            deny = DecisionEngine(ws).evaluate(
                action="wire.transfer",
                provider="finance-decision",
                evidence_present=[],
            )
            self.assertEqual(deny["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
