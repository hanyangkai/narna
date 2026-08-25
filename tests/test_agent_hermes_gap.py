"""Tests for agent tools, skills, sessions (Hermes-gap v1)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.agent_session import AgentSessionStore
from uap.agent_skills import SkillStore
from uap.agent_tools import tool_calculator
from uap.model_router import ModelRouter
from uap.narna_agent import NarnaAgent, _parse_tool_calls
from uap.telegram_gateway import extract_telegram_text, format_agent_reply


class ToolTests(unittest.TestCase):
    def test_calculator(self):
        out = tool_calculator({"expression": "2 + 3 * 4"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["value"], 14)

    def test_calculator_rejects_import(self):
        out = tool_calculator({"expression": "__import__('os').system('x')"})
        self.assertFalse(out["ok"])

    def test_parse_tool_calls(self):
        text = 'Before\n```json\n{"tool":"calculator","args":{"expression":"1+1"}}\n```\nafter'
        calls = _parse_tool_calls(text)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["tool"], "calculator")


class SkillsSessionsTests(unittest.TestCase):
    def test_skill_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            store = SkillStore(Path(td))
            row = store.save(name="Contract review", body="Check clause 5", tags=["legal"])
            self.assertTrue(row["skillId"])
            listed = store.list_skills()
            self.assertEqual(len(listed), 1)
            got = store.get(row["skillId"])
            self.assertEqual(got["body"], "Check clause 5")

    def test_session_multiturn(self):
        with tempfile.TemporaryDirectory() as td:
            store = AgentSessionStore(Path(td))
            s = store.get_or_create(channel="web")
            sid = s["sessionId"]
            store.append(sid, role="user", content="hi")
            store.append(sid, role="assistant", content="hello")
            hist = store.history_for_prompt(sid)
            self.assertEqual(len(hist), 2)
            again = store.get_or_create(external_id="42", channel="telegram")
            same = store.get_or_create(external_id="42", channel="telegram")
            self.assertEqual(again["sessionId"], same["sessionId"])


class AgentToolsLoopTests(unittest.TestCase):
    def test_ask_with_forced_tool_round(self):
        class ToolThenAnswer(ModelRouter):
            def __init__(self):
                super().__init__(provider="mock")
                self.n = 0

            def complete(self, *, messages, task="reason", **kwargs):
                self.n += 1
                if self.n == 1:
                    from uap.model_router import RouterResult

                    return RouterResult(
                        content='```json\n{"tool":"calculator","args":{"expression":"10+5"}}\n```',
                        model="mock-tool",
                        provider="mock",
                        task=task,
                        usage={},
                    )
                return super().complete(messages=messages, task=task, **kwargs)

        with tempfile.TemporaryDirectory() as td:
            agent = NarnaAgent(
                workspace=Path(td),
                router=ToolThenAnswer(),
                max_tool_rounds=2,
            )
            out = agent.ask("What is 10+5?", use_tools=True, capture_skill=False)
            self.assertTrue(out["toolsUsed"])
            self.assertEqual(out["toolsUsed"][0]["tool"], "calculator")
            self.assertEqual(out["toolsUsed"][0]["result"]["value"], 15)
            self.assertTrue(out["sessionId"])
            # second turn same session
            out2 = agent.ask("And double it?", session_id=out["sessionId"], use_tools=False)
            self.assertEqual(out2["sessionId"], out["sessionId"])


class TelegramTests(unittest.TestCase):
    def test_extract(self):
        chat_id, text, user = extract_telegram_text(
            {"message": {"chat": {"id": 99}, "text": "hello", "from": {"username": "a"}}}
        )
        self.assertEqual(chat_id, "99")
        self.assertEqual(text, "hello")
        self.assertEqual(user, "a")

    def test_format(self):
        msg = format_agent_reply(
            {"answer": "Buy after review", "dqs": 72, "guardian": "caution", "toolsUsed": [{"tool": "web_search"}]}
        )
        self.assertIn("DQS 72", msg)
        self.assertIn("web_search", msg)


class DiscordDelegateTests(unittest.TestCase):
    def test_discord_extract(self):
        from uap.discord_gateway import extract_discord_message

        ch, text, author = extract_discord_message(
            {
                "t": "MESSAGE_CREATE",
                "d": {
                    "channel_id": "111",
                    "content": "Should I ship?",
                    "author": {"id": "222", "bot": False},
                },
            }
        )
        self.assertEqual(ch, "111")
        self.assertEqual(text, "Should I ship?")
        self.assertEqual(author, "222")

    def test_memory_search_and_delegate(self):
        with tempfile.TemporaryDirectory() as td:
            agent = NarnaAgent(
                workspace=Path(td),
                router=ModelRouter(provider="mock"),
                max_tool_rounds=0,
            )
            first = agent.ask("Should I renew the lease?", use_tools=False, capture_skill=False)
            agent.record_outcome(first["decisionId"], status="success", lesson="Check CPI clause")
            hits = agent.tools.call("memory_search", {"query": "lease"})
            self.assertTrue(hits["ok"])
            self.assertTrue(hits["hits"])
            sub = agent.tools.call("delegate_task", {"task": "Summarize lease risks"})
            self.assertTrue(sub["ok"])
            self.assertTrue(sub.get("answer"))


class SandboxJobsTests(unittest.TestCase):
    def test_code_exec(self):
        from uap.agent_tools import tool_code_exec

        out = tool_code_exec({"code": "result = sum(range(10))"})
        self.assertTrue(out["ok"])
        self.assertEqual(out["result"], 45)
        bad = tool_code_exec({"code": "import os"})
        self.assertFalse(bad["ok"])

    def test_workspace_and_jobs(self):
        from uap.agent_jobs import AgentJobStore
        from uap.agent_tools import AgentToolbelt

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            belt = AgentToolbelt(workspace=root)
            w = belt.call("workspace_write", {"path": "notes.txt", "text": "hello"})
            self.assertTrue(w["ok"])
            r = belt.call("workspace_read", {"path": "notes.txt"})
            self.assertEqual(r["text"], "hello")
            jobs = AgentJobStore(root)
            job = jobs.create(prompt="Daily risk check", every_minutes=None)
            self.assertTrue(job["jobId"])
            due = jobs.due_jobs()
            self.assertTrue(any(j["jobId"] == job["jobId"] for j in due))
            recurring = jobs.create(prompt="Hourly", every_minutes=60)
            self.assertFalse(any(j["jobId"] == recurring["jobId"] for j in jobs.due_jobs()))


if __name__ == "__main__":
    unittest.main()
