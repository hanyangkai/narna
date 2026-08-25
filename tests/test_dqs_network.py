"""DQS Network + Redis rate limiter unit tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class DqsNetworkTest(unittest.TestCase):
    def test_export_import_merge(self) -> None:
        from uap.dqs_network import DqsNetwork
        from uap.outcome_learning import OutcomeLearningEngine

        with tempfile.TemporaryDirectory() as td:
            # seed priors via evaluate path mock
            eng = OutcomeLearningEngine(td)
            data = eng._read()
            data["actions"]["contract.sign"] = {
                "avgSuccess": 0.9,
                "count": 5,
                "hint": "require dual approval",
            }
            eng._write(data)

            a = DqsNetwork(td)
            self.assertFalse(a.export_digest(org_id=1).get("ok"))
            a.set_opt_in(True)
            dig = a.export_digest(org_id=1, min_count=3)
            self.assertTrue(dig["ok"])
            self.assertGreaterEqual(dig["actionCount"], 1)

            with tempfile.TemporaryDirectory() as td2:
                b = DqsNetwork(td2)
                b.set_opt_in(True)
                out = b.import_digest(dig)
                self.assertTrue(out["ok"])
                enrich = b.enrich_adqa_context("contract.sign")
                self.assertIn("networkPrior", enrich.get("decisionMemory", {}))


class RateLimiterTest(unittest.TestCase):
    def test_memory_limiter(self) -> None:
        import sys

        repo = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repo / "web" / "backend"))
        from app.rate_limit import InMemoryRateLimiter

        lim = InMemoryRateLimiter(limit_per_min=2)
        self.assertTrue(lim.allow("a")[0])
        self.assertTrue(lim.allow("a")[0])
        ok, retry = lim.allow("a")
        self.assertFalse(ok)
        self.assertGreaterEqual(retry, 0)


if __name__ == "__main__":
    unittest.main()
