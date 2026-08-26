"""Tests for router modes + MEMORY.md."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.agent_memory_md import AgentMemoryMd
from uap.model_router import ModelRouter
from uap.narna_agent import NarnaAgent


class RouterModeTests(unittest.TestCase):
    def test_quality_mode_merges(self):
        r = ModelRouter(provider="mock")
        out = r.complete_mode(
            messages=[{"role": "user", "content": "Should we ship?"}],
            mode="quality",
        )
        self.assertTrue(out.content)
        self.assertIn("→", out.model)
        self.assertEqual(out.task, "quality")

    def test_critical_mode_three_plus_merge(self):
        r = ModelRouter(provider="mock")
        out = r.complete_mode(
            messages=[{"role": "user", "content": "Critical deploy?"}],
            mode="critical",
        )
        self.assertTrue(out.content)
        self.assertGreaterEqual(out.model.count("→"), 2)


class MemoryMdTests(unittest.TestCase):
    def test_roundtrip_and_ask(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            md = AgentMemoryMd(Path(td))
            md.append_lesson("Prefer recent supplier data", dqs=88)
            md.observe_user_message("I prefer concise answers")
            self.assertIn("supplier", md.read_memory())
            self.assertIn("concise", md.read_user().lower())
            agent = NarnaAgent(workspace=td, router=ModelRouter(provider="mock"))
            out = agent.ask("Ship tonight?", use_tools=False, capture_skill=False, mode="quality")
            self.assertEqual(out.get("mode"), "quality")
            self.assertTrue(out.get("traceId"))
            # High DQS may append lesson
            mem = agent.memory_md.read_memory()
            self.assertTrue(len(mem) > 20)


if __name__ == "__main__":
    unittest.main()
