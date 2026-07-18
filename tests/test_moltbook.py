from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "narna-moltbook"


class MoltbookClientTest(unittest.TestCase):
    def test_browse_hot_parses_response(self) -> None:
        sys_path = str(PLUGIN / "src")
        import sys

        sys.path.insert(0, sys_path)
        from client import MoltbookClient  # noqa: E402

        payload = {"success": True, "posts": [{"id": "p1", "title": "hello"}]}
        with patch("client.urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
                payload
            ).encode()
            out = MoltbookClient(api_key="test").browse_hot(limit=1)
        self.assertEqual(out["posts"][0]["title"], "hello")

    def test_save_and_load_credentials(self) -> None:
        sys_path = str(PLUGIN / "src")
        import sys

        sys.path.insert(0, sys_path)
        from client import load_credentials, save_credentials  # noqa: E402

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "credentials.json"
            save_credentials("moltbook_sk_test", "NARNA-Gov", path=path)
            creds = load_credentials(path)
            self.assertEqual(creds["api_key"], "moltbook_sk_test")
            self.assertEqual(creds["agent_name"], "NARNA-Gov")


class MoltbookAdapterTest(unittest.TestCase):
    def test_adapter_detects_moltbook_client(self) -> None:
        from narna.adapters import ADAPTER_CATALOG, detect_framework, resolve_adapter

        class MoltbookClient:
            pass

        MoltbookClient.__module__ = "narna_moltbook.client"
        self.assertEqual(detect_framework(MoltbookClient()), "moltbook")
        adapter = resolve_adapter("moltbook", MoltbookClient())
        assert adapter is not None
        self.assertEqual(adapter.package, "narna-moltbook")
        ids = {row["id"] for row in ADAPTER_CATALOG}
        self.assertIn("moltbook", ids)


class MoltbookPluginTest(unittest.TestCase):
    def test_discover_plugin(self) -> None:
        from uap.plugins import discover_plugins

        found = discover_plugins(REPO / "plugins")
        ids = {p["id"] for p in found}
        self.assertIn("narna-moltbook", ids)

    def test_register_plugin_hooks(self) -> None:
        from uap.plugins import attach_plugin

        class Agent:
            pass

        agent = Agent()
        out = attach_plugin(agent, PLUGIN)
        self.assertTrue(out.get("ok"))
        self.assertIn("moltbook", agent._plugins)


if __name__ == "__main__":
    unittest.main()
