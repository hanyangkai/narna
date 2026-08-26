"""Tests for Model Router (NGS-0028) and NARNA Agent (NGS-0029)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.model_router import ModelRouter, normalize_task
from uap.narna_agent import NarnaAgent


class ModelRouterTests(unittest.TestCase):
    def test_normalize_aliases(self):
        self.assertEqual(normalize_task("analyze"), "reason")
        self.assertEqual(normalize_task("CHALLENGE"), "challenge")

    def test_mock_complete(self):
        r = ModelRouter(provider="mock")
        out = r.complete(
            messages=[{"role": "user", "content": "Should I buy this car?"}],
            task="reason",
        )
        self.assertEqual(out.provider, "mock")
        self.assertIn("mock-reason", out.model)
        self.assertTrue(out.content)
        self.assertEqual(out.to_dict()["standard"], "NGS-0028")

    def test_mock_challenge(self):
        r = ModelRouter(provider="mock")
        out = r.challenge(draft="Buy it.", question="Car purchase?")
        self.assertEqual(out.task, "challenge")
        self.assertIn("mock-challenge", out.content.lower() + out.model)


class NarnaAgentTests(unittest.TestCase):
    def test_ask_pipeline(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            agent = NarnaAgent(
                workspace=Path(td),
                tenant_id="t_test",
                router=ModelRouter(provider="mock"),
            )
            out = agent.ask("Should I sign this contract?", challenge=True)
            self.assertEqual(out["standard"], "NGS-0029")
            self.assertTrue(out["answer"])
            self.assertIsNotNone(out["dqs"])
            self.assertTrue(out["decisionId"])
            self.assertTrue(out["sessionId"])
            self.assertIn("toolsUsed", out)
            self.assertGreaterEqual(len(out["modelsUsed"]), 2)
            outcome = agent.record_outcome(
                out["decisionId"],
                status="success",
                detail="held",
                lesson="Always read clause 5",
            )
            self.assertEqual(outcome["outcome"]["status"], "success")


if __name__ == "__main__":
    unittest.main()
