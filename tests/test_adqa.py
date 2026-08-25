"""ADQA — Decision Quality Score tests."""

from __future__ import annotations

import tempfile
import unittest


class ADQATest(unittest.TestCase):
    def test_high_dqs_with_evidence(self) -> None:
        from uap.adqa import ADQAEngine

        with tempfile.TemporaryDirectory() as td:
            out = ADQAEngine(td).check_proposed(
                action="contract.sign",
                provider="legal-decision",
                evidence_present=[
                    "policy.decision",
                    "human.review",
                    "contract.hash",
                ],
            )
            adqa = out["adqa"]
            self.assertTrue(adqa["ok"])
            self.assertIn("dqs", adqa)
            self.assertEqual(len(adqa["attributes"]), 10)
            self.assertIn(adqa["guardian"], ("approve", "revise", "escalate", "reject"))
            self.assertEqual(adqa["standard"], "NGS-0024")

    def test_missing_evidence_lowers_score(self) -> None:
        from uap.adqa import ADQAEngine

        with tempfile.TemporaryDirectory() as td:
            rich = ADQAEngine(td).check_proposed(
                action="contract.sign",
                provider="legal-decision",
                evidence_present=[
                    "policy.decision",
                    "human.review",
                    "contract.hash",
                ],
            )
            poor = ADQAEngine(td).check_proposed(
                action="contract.sign",
                provider="legal-decision",
                evidence_present=[],
            )
            self.assertGreaterEqual(rich["adqa"]["dqs"], poor["adqa"]["dqs"])
            self.assertLess(poor["adqa"]["attributes"]["evidence"], 80)

    def test_decision_engine_attaches_adqa(self) -> None:
        from uap.decision import DecisionEngine

        with tempfile.TemporaryDirectory() as td:
            result = DecisionEngine(td).evaluate(
                action="contract.sign",
                provider="legal-decision",
                evidence_present=["policy.decision", "human.review", "contract.hash"],
            )
            self.assertIn("adqa", result)
            self.assertIsInstance(result["adqa"].get("dqs"), int)


if __name__ == "__main__":
    unittest.main()
