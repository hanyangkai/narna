"""Tests for execute_code RPC (Hermes gap P2)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.agent_rpc import run_execute_code
from uap.agent_tools import AgentToolbelt, tool_browser_vision


class ExecuteCodeRpcTests(unittest.TestCase):
    def test_call_tool_calculator(self):
        belt = AgentToolbelt()

        def call_tool(name: str, args: dict) -> dict:
            return belt.call(name, args)

        code = """
r = call_tool("calculator", {"expression": "12*12"})
result = r.get("value")
"""
        out = run_execute_code(code, call_tool)
        self.assertTrue(out.get("ok"), msg=str(out))
        self.assertEqual(out.get("result"), 144)
        self.assertEqual(len(out.get("toolCalls") or []), 1)

    def test_budget_exhausted(self):
        belt = AgentToolbelt()

        def call_tool(name: str, args: dict) -> dict:
            return belt.call(name, args)

        code = """
for i in range(5):
    call_tool("calculator", {"expression": "1+1"})
result = "done"
"""
        out = run_execute_code(code, call_tool, max_calls=2)
        self.assertTrue(out.get("ok"))
        self.assertGreaterEqual(len(out.get("toolCalls") or []), 2)

    def test_toolbelt_execute_code(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            belt = AgentToolbelt(workspace=Path(td))
            out = belt.call(
                "execute_code",
                {
                    "code": (
                        'r = call_tool("calculator", {"expression": "7+5"})\n'
                        "result = r['value']"
                    )
                },
            )
            self.assertTrue(out.get("ok"), msg=str(out))
            self.assertEqual(out.get("result"), 12)

    def test_browser_vision_no_playwright(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            belt = AgentToolbelt(workspace=Path(td))
            out = tool_browser_vision({"url": "https://example.com"}, workspace=Path(td), belt=belt)
            # Without playwright or key, should fail gracefully
            self.assertIn("ok", out)


if __name__ == "__main__":
    unittest.main()
