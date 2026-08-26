"""NARNA Decision Benchmark tests (market plan B5)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.decision_benchmark import load_scenarios, run_benchmark, run_scenario, verdict_from_adqa


class DecisionBenchmarkTests(unittest.TestCase):
    def test_verdict_mapping(self):
        self.assertEqual(verdict_from_adqa({"guardian": "approve", "dqs": 90}), "ACT")
        self.assertEqual(verdict_from_adqa({"guardian": "revise", "dqs": 75}), "REVIEW")
        self.assertEqual(verdict_from_adqa({"guardian": "escalate", "dqs": 80}), "REVIEW")
        self.assertEqual(verdict_from_adqa({"guardian": "reject", "dqs": 40}), "REJECT")
        self.assertEqual(verdict_from_adqa({"decision": "deny", "guardian": "approve", "dqs": 90}), "REJECT")

    def test_load_scenarios(self):
        rows = load_scenarios(limit=5)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r.get("expectedVerdict") in {"ACT", "REVIEW", "REJECT"} for r in rows))

    def test_mock_subset_perfect(self):
        # CI subset — first 12 calibrated scenarios
        out = run_benchmark(agent="mock", limit=12)
        self.assertEqual(out["n"], 12)
        self.assertEqual(out["accuracy"], 1.0)
        self.assertGreaterEqual(out["correct"], 12)

    def test_strip_agent_differs(self):
        # strip removes evidence; at least one golden ACT/REVIEW should flip
        full = load_scenarios(ids=["res-001"])
        self.assertEqual(len(full), 1)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            mock = run_scenario(full[0], agent="mock", workspace=Path(td))
            stripped = run_scenario(full[0], agent="strip", workspace=Path(td))
        self.assertEqual(mock.got, "ACT")
        self.assertEqual(stripped.got, "REJECT")
        self.assertNotEqual(mock.got, stripped.got)

    def test_category_filter(self):
        out = run_benchmark(agent="mock", category="legal", limit=5)
        self.assertEqual(out["n"], 5)
        self.assertTrue(all(r["category"] == "legal" for r in out["results"]))


if __name__ == "__main__":
    unittest.main()
