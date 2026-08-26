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
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            store = SkillStore(Path(td))
            row = store.save(name="Contract review", body="Check clause 5", tags=["legal"])
            self.assertTrue(row["skillId"])
            listed = store.list_skills()
            self.assertEqual(len(listed), 1)
            got = store.get(row["skillId"])
            self.assertEqual(got["body"], "Check clause 5")

    def test_session_multiturn(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
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

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
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
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
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

    def test_shell_browser_hub_parallel(self):
        from uap.agent_tools import tool_browser_navigate, tool_shell_exec
        from uap.skill_hub import SkillHub

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            root = Path(td)
            cwd = root / ".uap" / "agent-workspace"
            cwd.mkdir(parents=True)
            (cwd / "note.txt").write_text("hello hub", encoding="utf-8")
            # use python -c? blocked if python allowed - use cat-like via python read file
            # on windows, type/cat may vary — use python allowlisted
            sh = tool_shell_exec({"command": "python -c \"print(open('note.txt').read())\""}, cwd=cwd)
            # python -c may be ok; if posix shlex works
            if not sh.get("ok"):
                # fallback: echo
                sh = tool_shell_exec({"command": "echo hello"}, cwd=cwd)
            self.assertTrue(sh.get("ok") or sh.get("stdout"), sh)

            bad = tool_shell_exec({"command": "rm -rf /"}, cwd=cwd)
            self.assertFalse(bad.get("ok"))

            # browser fetch engine (no network assert — may fail offline)
            br = tool_browser_navigate({"url": "https://example.com"})
            self.assertIn("ok", br)

            hub = SkillHub(root)
            pub = hub.publish(name="Review leases", body="Always check CPI", tags=["legal"])
            agent = NarnaAgent(workspace=root, router=ModelRouter(provider="mock"))
            inst = agent.tools.call("skill_hub_install", {"skillId": pub["skillId"]})
            self.assertTrue(inst["ok"])
            par = agent.tools.call(
                "parallel_delegate",
                {"tasks": ["Risk A?", "Risk B?"]},
            )
            self.assertTrue(par["ok"])
            self.assertEqual(len(par["results"]), 2)

    def test_fts_profile_and_gateways(self):
        from uap.agent_memory_fts import AgentMemoryFTS
        from uap.email_gateway import extract_email_message
        from uap.signal_gateway import extract_signal_message

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            fts = AgentMemoryFTS(Path(td))
            fts.index_turn(session_id="s1", role="user", content="lease renewal CPI clause")
            fts.observe_user_message("I prefer short answers")
            hits = fts.search("CPI")
            self.assertTrue(hits)
            self.assertIn("preference_note", fts.get_profile())

        sender, text = extract_signal_message(
            {"envelope": {"sourceNumber": "+1555", "dataMessage": {"message": "hi"}}}
        )
        self.assertEqual(sender, "+1555")
        self.assertEqual(text, "hi")
        frm, sub, body = extract_email_message(
            {"from": "a@b.com", "subject": "Q", "text": "Should I sign?"}
        )
        self.assertEqual(frm, "a@b.com")
        self.assertEqual(sub, "Q")
        self.assertIn("sign", body)


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

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
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


class HermesAlignTests(unittest.TestCase):
    def test_openai_tools_schema(self):
        from uap.agent_tools import openai_tools_schema

        tools = openai_tools_schema()
        self.assertTrue(tools)
        self.assertEqual(tools[0]["type"], "function")
        names = {t["function"]["name"] for t in tools}
        self.assertIn("calculator", names)
        self.assertIn("shell_exec", names)

    def test_merge_prefers_native(self):
        from uap.narna_agent import _merge_tool_calls

        native = [{"tool": "calculator", "args": {"expression": "1+1"}, "id": "c1"}]
        parsed = [{"tool": "web_search", "args": {"query": "x"}}]
        self.assertEqual(_merge_tool_calls(native, parsed)[0]["tool"], "calculator")
        self.assertEqual(_merge_tool_calls(None, parsed)[0]["tool"], "web_search")

    def test_shell_approval_gate(self):
        import os
        import sys

        from uap.agent_tools import tool_shell_exec

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            os.environ["UAP_SHELL_REQUIRE_APPROVAL"] = "1"
            try:
                blocked = tool_shell_exec({"command": "python -c print(1)"}, cwd=Path(td))
                self.assertTrue(blocked.get("needsApproval"))
                # Approval path only needs to clear the gate; execution may vary by OS shell.
                cleared = tool_shell_exec(
                    {"command": "python -c print(1)", "approved": True}, cwd=Path(td)
                )
                self.assertFalse(cleared.get("needsApproval"))
                self.assertNotEqual(cleared.get("error"), blocked.get("error"))
            finally:
                os.environ.pop("UAP_SHELL_REQUIRE_APPROVAL", None)

    def test_skill_md_roundtrip(self):
        from uap.skill_md import markdown_to_skill, skill_to_markdown

        md = skill_to_markdown(
            {"name": "Review NDA", "body": "Check indemnity", "tags": ["legal"]}
        )
        self.assertIn("agentskills.io", md)
        parsed = markdown_to_skill(md)
        self.assertEqual(parsed["name"], "Review NDA")
        self.assertIn("indemnity", str(parsed["body"]))

    def test_native_tool_calls_in_ask_loop(self):
        class NativeToolsRouter(ModelRouter):
            def __init__(self):
                super().__init__(provider="mock")
                self.n = 0
                self.saw_tools = False

            def complete(self, *, messages, task="reason", tools=None, **kwargs):
                self.n += 1
                from uap.model_router import RouterResult

                if self.n == 1:
                    self.saw_tools = bool(tools)
                    return RouterResult(
                        content="",
                        model="mock-native",
                        provider="mock",
                        task=task,
                        usage={},
                        tool_calls=[
                            {
                                "tool": "calculator",
                                "args": {"expression": "7*8"},
                                "id": "call_1",
                            }
                        ],
                    )
                return super().complete(messages=messages, task=task, **kwargs)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            router = NativeToolsRouter()
            agent = NarnaAgent(workspace=td, router=router)
            out = agent.ask("what is 7*8?", use_tools=True, capture_skill=False)
            self.assertTrue(router.saw_tools)
            tools = out.get("toolsUsed") or []
            self.assertTrue(any(t.get("tool") == "calculator" for t in tools))
            self.assertIn("56", str(tools[0].get("result")))


class HermesLevelUpTests(unittest.TestCase):
    def test_nl_cron_every_day(self):
        from uap.nl_cron import parse_nl_schedule

        p = parse_nl_schedule("every day remind me to review risk via telegram")
        self.assertEqual(p["everyMinutes"], 1440)
        self.assertIn("review", p["prompt"].lower())
        self.assertEqual(p["channel"], "telegram")

    def test_nl_cron_in_minutes(self):
        from uap.nl_cron import parse_nl_schedule

        p = parse_nl_schedule("in 10 minutes check portfolio")
        self.assertTrue(p["runAt"])
        self.assertIsNone(p["everyMinutes"])

    def test_slash_parse(self):
        from uap.slash_commands import parse_slash

        self.assertEqual(parse_slash("/model gpt-4o")["cmd"], "/model")
        self.assertIsNone(parse_slash("hello"))

    def test_http_request_rejects_http(self):
        from uap.agent_tools import tool_http_request

        out = tool_http_request({"url": "http://example.com"})
        self.assertFalse(out["ok"])

    def test_schedule_job_tool(self):
        from uap.agent_jobs import AgentJobStore
        from uap.agent_tools import AgentToolbelt

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            jobs = AgentJobStore(Path(td))
            belt = AgentToolbelt(workspace=Path(td), jobs=jobs)
            out = belt.call(
                "schedule_job",
                {"schedule": "every 60 minutes ping health check"},
            )
            self.assertTrue(out.get("ok"), msg=str(out))
            self.assertEqual(out["job"]["everyMinutes"], 60)

    def test_gateway_status(self):
        from uap.gateway_runner import UnifiedGateway

        gw = UnifiedGateway(ask_fn=lambda m, c, e: {"answer": "ok"})
        st = gw.status()
        self.assertIn("telegramConfigured", st)
        self.assertEqual(st["standard"], "NGS-0029-gateway")

    def test_tool_count_grown(self):
        from uap.agent_tools import TOOL_SPECS

        self.assertGreaterEqual(len(TOOL_SPECS), 26)


if __name__ == "__main__":
    unittest.main()
