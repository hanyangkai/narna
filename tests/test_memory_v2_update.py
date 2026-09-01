"""Honcho-lite v2 + subagent isolation + update check."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from uap.agent_memory_fts import AgentMemoryFTS
from uap.agent_memory_md import AgentMemoryMd
from uap.desktop_update import _parse_version, check_update
from uap.knowledge import KnowledgeGraph
from uap.model_router import ModelRouter
from uap.narna_agent import NarnaAgent


class MemoryV2Tests(unittest.TestCase):
    def test_project_md_and_lesson_fts(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            md = AgentMemoryMd(td)
            md.observe_user_message("I am working on project NARNA-agent")
            self.assertIn("NARNA", md.read_project())
            fts = AgentMemoryFTS(td)
            fts.index_lesson("Always require dual approval for contracts", dqs=85)
            self.assertGreaterEqual(fts.lesson_count(), 1)
            hits = fts.search("dual approval")
            self.assertTrue(any(h.get("source") == "lesson" for h in hits))
            recent = fts.recent_lessons(limit=3)
            self.assertGreaterEqual(len(recent), 1)
            self.assertIn("dual approval", recent[0].get("snippet", ""))

    def test_kg_observe(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            kg = KnowledgeGraph(td)
            created = kg.observe_message("working on project AlphaVault for customer Acme")
            self.assertTrue(created)
            names = {e.get("name") for e in kg.query(limit=20)}
            self.assertTrue(any("Alpha" in str(n) for n in names))


class SubagentIsolationTests(unittest.TestCase):
    def test_delegate_creates_child_session(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            agent = NarnaAgent(workspace=td, router=ModelRouter(provider="mock"))
            parent = agent.ask("parent question", use_tools=False)
            parent_sid = parent.get("sessionId")
            self.assertTrue(parent_sid)
            # Force active parent then delegate
            agent._active_session_id = parent_sid
            out = agent._delegate_subask("sub task please")
            child_sid = out.get("sessionId")
            self.assertTrue(child_sid)
            self.assertNotEqual(child_sid, parent_sid)
            kids = agent.sessions.list_children(parent_sid)
            self.assertTrue(any(k.get("sessionId") == child_sid for k in kids))


class UpdateCheckTests(unittest.TestCase):
    def test_parse_version(self):
        self.assertGreater(_parse_version("v0.2.7"), _parse_version("0.2.6"))

    def test_check_update_mocked(self):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b'{"tag_name":"v9.9.9","html_url":"https://github.com/hanyangkai/narna/releases/tag/v9.9.9","assets":[]}'

        with mock.patch("urllib.request.urlopen", return_value=Resp()):
            out = check_update(current="0.2.6")
        self.assertTrue(out.get("ok"))
        self.assertTrue(out.get("updateAvailable"))


if __name__ == "__main__":
    unittest.main()
