"""Prod agent parity tests (browser health, shell docker, gateway, MCP, config)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class BrowserReadyTests(unittest.TestCase):
    def test_browser_ready_without_playwright(self):
        from uap.browser_session import browser_ready

        with mock.patch.dict("sys.modules", {"playwright": None, "playwright.sync_api": None}):
            # If playwright is installed in env, ready may be True — still must return shape
            out = browser_ready()
            self.assertIn("ready", out)
            self.assertIn("enabled", out)


class ShellDockerTests(unittest.TestCase):
    def test_docker_missing_clear_error(self):
        from uap.agent_tools import tool_shell_exec

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            with mock.patch.dict(
                os.environ,
                {"UAP_SHELL_BACKEND": "docker", "UAP_SHELL_FALLBACK_LOCAL": "0"},
                clear=False,
            ):
                with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
                    out = tool_shell_exec({"command": "ls"}, cwd=Path(td))
                    self.assertFalse(out.get("ok"))
                    self.assertEqual(out.get("backend"), "docker")
                    self.assertIn("docker", str(out.get("error") or "").lower())

    def test_docker_fallback_local(self):
        from uap.agent_tools import tool_shell_exec

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            Path(td, "a.txt").write_text("x", encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"UAP_SHELL_BACKEND": "docker", "UAP_SHELL_FALLBACK_LOCAL": "1"},
                clear=False,
            ):
                with mock.patch("subprocess.run", side_effect=FileNotFoundError()) as run:
                    # first call is docker → FileNotFoundError; fallback uses real subprocess
                    # so only patch the first invocation
                    real_run = __import__("subprocess").run

                    def _side(*a, **k):
                        if a and a[0] and a[0][0] == "docker":
                            raise FileNotFoundError()
                        return real_run(*a, **k)

                    run.side_effect = _side
                    out = tool_shell_exec({"command": "ls"}, cwd=Path(td))
                    self.assertTrue(out.get("ok") or out.get("backend") == "local")
                    self.assertEqual(out.get("fellBackFrom"), "docker")


class GatewayStatusTests(unittest.TestCase):
    def test_channels_shape(self):
        from uap.gateway_runner import UnifiedGateway

        gw = UnifiedGateway(ask_fn=lambda *_: {})
        st = gw.status()
        self.assertIn("channels", st)
        for name in ("telegram", "discord", "slack", "whatsapp", "signal", "email"):
            self.assertIn(name, st["channels"])
            self.assertIn("mode", st["channels"][name])
            self.assertIn("configured", st["channels"][name])
        self.assertIn("deduped", st["stats"])


class McpRuntimeStatusTests(unittest.TestCase):
    def test_runtime_status_tool(self):
        from narna.mcp_tools import NarnaMcpTools

        tools = NarnaMcpTools()
        names = {t["name"] for t in tools.list_tools()}
        self.assertIn("narna_runtime_status", names)
        out = tools.call_tool("narna_runtime_status", {})
        self.assertTrue(out.get("ok"))
        self.assertGreaterEqual(int(out.get("toolCount") or 0), 40)
        self.assertIn("browser", out)
        self.assertEqual(out.get("mcpSurface"), "adqa+ask+status")

    def test_agent_ask_empty_message(self):
        from narna.mcp_tools import NarnaMcpTools

        out = NarnaMcpTools().call_tool("narna_agent_ask", {})
        self.assertFalse(out.get("ok"))


class ConfigCliTests(unittest.TestCase):
    def test_yaml_and_json_roundtrip(self):
        from uap.narna_config import config_set, config_show, load_narna_config, save_narna_config

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            home = Path(td)
            save_narna_config({"provider": "openai", "apiKey": "sk-test-abcdefgh"}, home)
            cfg = load_narna_config(home)
            self.assertEqual(cfg.get("provider"), "openai")
            out = config_set("shellBackend", "local", home)
            self.assertTrue(out.get("ok"))
            show = config_show(home)
            self.assertEqual(show["config"].get("shellBackend"), "local")
            self.assertIn("…", show["config"].get("apiKey") or "***")

            # YAML wins
            yml = home / "config.yaml"
            yml.write_text("provider: openrouter\nmodel: x\n", encoding="utf-8")
            merged = load_narna_config(home)
            self.assertEqual(merged.get("provider"), "openrouter")
            self.assertEqual(merged.get("model"), "x")


if __name__ == "__main__":
    unittest.main()
