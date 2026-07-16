from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.benchmark import BenchmarkStore
from uap.conformance import run_conformance_checks
from uap.identity import IdentityStore


REPO = Path(__file__).resolve().parents[1]


class MvpTest(unittest.TestCase):
    def test_benchmark_record(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            store = BenchmarkStore(ws)
            store.record(
                agent_id="agent1",
                run_id="run1",
                trust_score={"score": 0.9, "algorithm": "vap-trust-v0", "breakdown": {}},
            )
            self.assertEqual(len(store.list()), 1)
            self.assertAlmostEqual(store.average_score(agent_id="agent1"), 0.9)

    def test_conformance_after_init(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            import shutil

            shutil.copytree(REPO / "policies", ws / "policies")
            spec = REPO / "specs" / "examples" / "trading-agent.yaml"
            from uap.spec import load_agent_spec

            s = load_agent_spec(spec)
            IdentityStore(ws).issue(s)
            problems = run_conformance_checks(ws, spec)
            self.assertEqual(problems, [], msg="\n".join(problems))


if __name__ == "__main__":
    unittest.main()
