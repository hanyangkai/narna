"""Desktop agent config unification tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.narna_config import (
    make_agent,
    resolve_workspace,
    router_from_config,
    save_narna_config,
)


class DesktopAgentConfigTests(unittest.TestCase):
    def test_resolve_workspace_creates_home(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            ws = resolve_workspace(td)
            self.assertTrue(ws.is_dir())

    def test_router_from_config_mock_without_key(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            save_narna_config({"provider": "openrouter"}, td)
            router = router_from_config(td)
            self.assertEqual(router.provider, "mock")

    def test_make_agent_ask_mock(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            agent = make_agent(td)
            out = agent.ask("Hello?", use_tools=False)
            self.assertTrue(out.get("answer"))


if __name__ == "__main__":
    unittest.main()
