"""Hermes gap P4/P6/P7 — shell backends, TTS, tool batch."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from uap.agent_tools import (
    TOOL_SPECS,
    AgentToolbelt,
    openai_tools_schema,
    tool_env_get,
    tool_hash,
    tool_json_query,
    tool_shell_exec,
    tool_text_to_speech,
    tool_uuid,
)
from uap.shell_remote import exec_daytona, exec_modal
from uap.telegram_gateway import build_telegram_voice_payload


class ShellBackendTests(unittest.TestCase):
    def test_modal_missing_env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("UAP_MODAL")}
        with mock.patch.dict(os.environ, env, clear=True):
            out = exec_modal(command="echo hi")
        self.assertFalse(out["ok"])
        self.assertIn("UAP_MODAL_TOKEN", out["error"])

    def test_daytona_missing_env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("UAP_DAYTONA")}
        with mock.patch.dict(os.environ, env, clear=True):
            out = exec_daytona(command="echo hi")
        self.assertFalse(out["ok"])
        self.assertIn("UAP_DAYTONA_API_KEY", out["error"])

    def test_modal_http_mock(self):
        class _Resp:
            def read(self):
                return json.dumps({"ok": True, "stdout": "hello\n", "exitCode": 0}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with mock.patch.dict(
            os.environ,
            {
                "UAP_MODAL_TOKEN": "tok",
                "UAP_MODAL_APP": "app1",
                "UAP_MODAL_EXEC_URL": "https://example.test/exec",
            },
            clear=False,
        ):
            with mock.patch("urllib.request.urlopen", return_value=_Resp()):
                out = exec_modal(command="echo hello")
        self.assertTrue(out["ok"])
        self.assertEqual(out["backend"], "modal")
        self.assertIn("hello", out["stdout"])

    def test_shell_exec_modal_backend_missing(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            with mock.patch.dict(
                os.environ,
                {"UAP_SHELL_BACKEND": "modal"},
                clear=False,
            ):
                # Clear modal keys for this call
                os.environ.pop("UAP_MODAL_TOKEN", None)
                os.environ.pop("UAP_MODAL_APP", None)
                out = tool_shell_exec({"command": "echo hi", "approved": True}, cwd=Path(td))
        self.assertFalse(out["ok"])
        self.assertIn("UAP_MODAL", out.get("error", ""))


class ToolBatchTests(unittest.TestCase):
    def test_tool_count_at_least_40(self):
        self.assertGreaterEqual(len(TOOL_SPECS), 40)
        schema = openai_tools_schema()
        self.assertGreaterEqual(len(schema), 40)
        self.assertEqual(schema[0]["type"], "function")

    def test_uuid_hash_json_env(self):
        u = tool_uuid({"n": 2})
        self.assertTrue(u["ok"])
        self.assertEqual(len(u["uuids"]), 2)
        h = tool_hash({"text": "narna", "algo": "sha256"})
        self.assertTrue(h["ok"])
        self.assertEqual(len(h["hex"]), 64)
        j = tool_json_query({"json": '{"a":{"b":[1,2]}}', "path": "a.b[1]"})
        self.assertTrue(j["ok"])
        self.assertEqual(j["value"], 2)
        bad = tool_env_get({"key": "OPENAI_API_KEY"})
        self.assertFalse(bad["ok"])
        with mock.patch.dict(os.environ, {"LANG": "C.UTF-8"}):
            good = tool_env_get({"key": "LANG"})
        self.assertTrue(good["ok"])
        self.assertEqual(good["value"], "C.UTF-8")

    def test_grep_and_skill_md(self):
        from uap.agent_skills import SkillStore

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            ws = Path(td)
            belt = AgentToolbelt(workspace=ws, skills=SkillStore(ws))
            aw = ws / ".uap" / "agent-workspace"
            aw.mkdir(parents=True)
            (aw / "note.txt").write_text("find-me-narna-token\n", encoding="utf-8")
            g = belt.call("grep_workspace", {"pattern": "narna-token"})
            self.assertTrue(g["ok"])
            self.assertGreaterEqual(g["n"], 1)
            saved = belt.call("skill_save", {"name": "Demo", "body": "Do X", "tags": ["t"]})
            self.assertTrue(saved["ok"])
            sid = saved["skill"]["skillId"]
            md = belt.call("skill_export_md", {"skillId": sid})
            self.assertTrue(md["ok"])
            self.assertIn("Demo", md["markdown"])
            imp = belt.call(
                "skill_import_md",
                {"markdown": "---\nname: Imported\ntags: [a]\n---\n\n# Imported\n\nBody here\n"},
            )
            self.assertTrue(imp["ok"])
            self.assertEqual(imp["skill"]["name"], "Imported")

    def test_tts_needs_key(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            env = {
                k: v
                for k, v in os.environ.items()
                if k not in {"UAP_OPENAI_API_KEY", "OPENAI_API_KEY"}
            }
            with mock.patch.dict(os.environ, env, clear=True):
                out = tool_text_to_speech({"text": "hello"}, workspace=Path(td))
        self.assertFalse(out["ok"])
        self.assertTrue(out.get("needsKey"))

    def test_telegram_voice_payload_shape(self):
        p = build_telegram_voice_payload(123, "out.mp3", caption="hi")
        self.assertEqual(p["method"], "sendVoice")
        self.assertEqual(p["chat_id"], "123")
        self.assertEqual(p["filename"], "out.mp3")


if __name__ == "__main__":
    unittest.main()
