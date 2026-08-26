"""Decision Trace + Replay + evaluate SDK tests (NGS-0030 / market plan B1–B3)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.decision_replay import replay_trace
from uap.decision_trace import DecisionTraceStore
from uap.model_router import ModelRouter
from uap.narna_agent import NarnaAgent


class DecisionTraceTests(unittest.TestCase):
    def test_create_and_get(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            store = DecisionTraceStore(Path(td))
            row = store.create(
                goal="Pick a supplier",
                evidence=[{"type": "url", "ref": "https://example.com"}],
                chosen="recommend",
                rationale="Best price",
                adqa={"dqs": 85, "guardian": "allow"},
                decision_id="dmem_test",
            )
            self.assertTrue(row["traceId"].startswith("trace_"))
            got = store.get(row["traceId"])
            self.assertEqual(got["goal"], "Pick a supplier")
            by_dec = store.get_by_decision("dmem_test")
            self.assertEqual(by_dec["traceId"], row["traceId"])
            listed = store.list_traces()
            self.assertEqual(len(listed), 1)

    def test_ask_emits_trace(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            agent = NarnaAgent(workspace=td, router=ModelRouter(provider="mock"))
            out = agent.ask("Should I sign this NDA?", use_tools=False, capture_skill=False)
            self.assertTrue(out.get("traceId"))
            self.assertIn(out.get("verdict"), {"ACT", "REVIEW", "REJECT"})
            tr = agent.traces.get(str(out["traceId"]))
            self.assertIsNotNone(tr)
            self.assertEqual(tr["decisionId"], out["decisionId"])
            self.assertIn("sign", tr["goal"].lower())

    def test_outcome_mirrors_to_trace(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            agent = NarnaAgent(workspace=td, router=ModelRouter(provider="mock"))
            out = agent.ask("Buy or wait?", use_tools=False, capture_skill=False)
            agent.record_outcome(
                out["decisionId"],
                status="fail",
                lesson="Supplier data was stale",
            )
            tr = agent.traces.get(str(out["traceId"]))
            self.assertEqual((tr.get("outcome") or {}).get("status"), "fail")
            self.assertIn("stale", str(tr.get("lesson") or ""))


class DecisionReplayTests(unittest.TestCase):
    def test_replay_changed_heuristic(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            agent = NarnaAgent(workspace=td, router=ModelRouter(provider="mock"))
            out = agent.ask("Choose vendor A or B?", use_tools=False, capture_skill=False)
            agent.record_outcome(out["decisionId"], status="fail", lesson="A failed delivery")
            result = agent.replay(str(out["traceId"]))
            self.assertTrue(result.get("ok"))
            self.assertIn("replayed", result)
            self.assertEqual(result["originalTraceId"], out["traceId"])


class EvaluateSdkTests(unittest.TestCase):
    def test_evaluate_verdict(self):
        from narna.evaluate import evaluate

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            out = evaluate(
                action="contract.sign",
                evidence=["contract.reviewed"],
                workspace=td,
            )
            self.assertTrue(out["ok"])
            self.assertIn(out["verdict"], {"ACT", "REVIEW", "REJECT"})
            self.assertIsNotNone(out.get("dqs"))


if __name__ == "__main__":
    unittest.main()
