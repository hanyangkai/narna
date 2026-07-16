from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class AnthropicGoogleAdaptersTest(unittest.TestCase):
    def test_anthropic_adapter_wraps_messages_create(self) -> None:
        from narna import wrap

        class FakeMessages:
            def __init__(self) -> None:
                self.calls = 0

            def create(self, **kwargs: object) -> dict:
                self.calls += 1
                return {"id": "msg_1", "content": "hi"}

        class FakeAnthropic:
            def __init__(self) -> None:
                self.messages = FakeMessages()

        FakeAnthropic.__module__ = "anthropic"

        with tempfile.TemporaryDirectory() as td:
            foreign = FakeAnthropic()
            agent = wrap(foreign, workspace=td, vap=False)
            self.assertEqual(agent._adapter["package"], "narna-anthropic")
            out = foreign.messages.create(model="claude-3", max_tokens=10, messages=[])
            self.assertEqual(out["id"], "msg_1")
            self.assertEqual(foreign.messages.calls, 1)
            self.assertTrue(agent.runtime.list_runs())

    def test_google_adapter_detect(self) -> None:
        from narna.adapters import detect_framework

        class GenerativeModel:
            pass

        GenerativeModel.__module__ = "google.generativeai"
        self.assertEqual(detect_framework(GenerativeModel()), "google")

    def test_catalog_includes_anthropic_google(self) -> None:
        from narna.adapters import ADAPTER_CATALOG

        ids = {row["id"] for row in ADAPTER_CATALOG}
        self.assertIn("anthropic", ids)
        self.assertIn("google", ids)
        self.assertIn("openshell", ids)


class PluginEconomyTest(unittest.TestCase):
    def test_discover_and_register_local(self) -> None:
        from uap.plugins import discover_plugins, list_local_plugins, register_plugin_local

        found = discover_plugins(REPO / "plugins")
        ids = {p["id"] for p in found}
        self.assertIn("narna-slack", ids)

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            entry = register_plugin_local(ws, REPO / "plugins" / "narna-slack")
            self.assertEqual(entry["pluginId"], "narna-slack")
            listed = list_local_plugins(ws)
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["pluginId"], "narna-slack")

    def test_cli_plugin_list(self) -> None:
        from uap.cli import cmd_plugin_list
        import argparse

        args = argparse.Namespace(root=str(REPO / "plugins"))
        self.assertEqual(cmd_plugin_list(args), 0)


if __name__ == "__main__":
    unittest.main()
