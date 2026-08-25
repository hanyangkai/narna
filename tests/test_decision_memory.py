"""Decision Memory + Outcome Learning tests."""

from __future__ import annotations

import tempfile
import unittest


class DecisionMemoryLearningTest(unittest.TestCase):
    def test_record_outcome_lesson_enriches_adqa(self) -> None:
        from uap.adqa import ADQAEngine
        from uap.outcome_learning import OutcomeLearningEngine

        with tempfile.TemporaryDirectory() as td:
            first = ADQAEngine(td).check_proposed(
                action="contract.sign",
                provider="legal-decision",
                evidence_present=["policy.decision", "human.review", "contract.hash"],
                context={"customer": "A"},
            )
            did = first["decisionMemoryId"]
            OutcomeLearningEngine(td).evaluate(
                did,
                status="success",
                detail="fraud prevented",
                success_score=0.94,
                lesson="Check account changes within 48h",
            )
            lessons = OutcomeLearningEngine(td).enrich_adqa_context("contract.sign")
            self.assertTrue(lessons["decisionMemory"]["lessons"])
            self.assertEqual(
                lessons["decisionMemory"]["lessons"][0]["lesson"],
                "Check account changes within 48h",
            )
            prior = lessons["decisionMemory"]["prior"]
            self.assertGreaterEqual(prior["n"], 1)
            second = ADQAEngine(td).check_proposed(
                action="contract.sign",
                provider="legal-decision",
                evidence_present=["policy.decision", "human.review", "contract.hash"],
                context={"customer": "A"},
            )
            self.assertTrue(second["adqa"].get("lessonsUsed"))


if __name__ == "__main__":
    unittest.main()
