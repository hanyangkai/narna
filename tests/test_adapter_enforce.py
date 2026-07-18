"""Tests for adapter enforce-before mode."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import yaml


class AdapterEnforceTest(unittest.TestCase):
    def test_enforce_blocks_before_original(self) -> None:
        from narna.adapters.base import BaseAdapter, NarnaGovernanceDenied
        from uap.agent import Agent
        from uap.governance_runtime import ConstitutionRuntime

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            os.environ["NARNA_ADAPTER_MODE"] = "enforce"

            pkg = {
                "apiVersion": "narna.ai/v1alpha1",
                "kind": "GovernancePackage",
                "metadata": {
                    "id": "pkg_test",
                    "name": "Test Deny",
                    "version": "1.0.0",
                    "provider": "test",
                    "packageKind": "Compliance",
                },
                "spec": {
                    "rules": [
                        {
                            "id": "deny-invoke",
                            "action": "langgraph.invoke",
                            "effect": "deny",
                        }
                    ]
                },
            }
            (ws / "packages").mkdir(parents=True)
            test_pkg = ws / "packages" / "test.yaml"
            test_pkg.write_text(yaml.dump(pkg), encoding="utf-8")
            ConstitutionRuntime(ws).load(path=test_pkg)

            agent = Agent(name="EnforceTest", workspace=ws)
            foreign = MagicMock()
            foreign.invoke = MagicMock(return_value={"ok": True})
            original_invoke = foreign.invoke

            adapter = BaseAdapter()
            adapter.id = "langgraph"
            adapter._wrap_method(foreign, "invoke", agent)

            with self.assertRaises(NarnaGovernanceDenied):
                foreign.invoke("hello")

            self.assertEqual(original_invoke.call_count, 0)

    def test_observe_calls_original(self) -> None:
        from narna import wrap

        class FakeGraph:
            def invoke(self, x: str) -> str:
                return f"out:{x}"

        with tempfile.TemporaryDirectory() as td:
            os.environ["NARNA_ADAPTER_MODE"] = "observe"
            agent = wrap(FakeGraph(), workspace=td, vap=False, mode="observe")
            self.assertEqual(agent._wrapped.invoke("hi"), "out:hi")

    def test_enforce_allows_without_active_package(self) -> None:
        from narna.adapters.base import BaseAdapter
        from uap.agent import Agent

        class FakeGraph:
            calls = 0

            def invoke(self, x: str) -> int:
                FakeGraph.calls += 1
                return 42

        with tempfile.TemporaryDirectory() as td:
            os.environ["NARNA_ADAPTER_MODE"] = "enforce"
            agent = Agent(name="AllowTest", workspace=Path(td))
            foreign = FakeGraph()

            adapter = BaseAdapter()
            adapter.id = "langgraph"
            adapter._wrap_method(foreign, "invoke", agent)
            self.assertEqual(foreign.invoke("x"), 42)
            self.assertEqual(FakeGraph.calls, 1)


if __name__ == "__main__":
    unittest.main()
