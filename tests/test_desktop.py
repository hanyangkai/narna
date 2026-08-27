"""NARNA Desktop local server tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from uap.desktop_server import create_app, load_config, save_config


class DesktopServerTests(unittest.TestCase):
    def test_health_and_ask_mock(self):
        try:
            from fastapi.testclient import TestClient  # noqa: F401
        except ImportError:
            self.skipTest("fastapi not installed")
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            app = create_app(workspace=Path(td))
            client = TestClient(app)
            h = client.get("/v1/health")
            self.assertEqual(h.status_code, 200)
            self.assertTrue(h.json()["ok"])
            self.assertEqual(h.json()["mode"], "desktop")
            self.assertIn("version", h.json())
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertIn("NARNA Desktop", page.text)
            ask = client.post("/v1/agent/ask", json={"message": "Should I proceed?"})
            self.assertEqual(ask.status_code, 200)
            body = ask.json()
            self.assertTrue(body.get("answer"))
            self.assertIn("dqs", body)

    def test_config_roundtrip(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            ws = Path(td)
            save_config(ws, {"provider": "openai", "apiKey": "sk-test-12345678"})
            cfg = load_config(ws)
            self.assertEqual(cfg["provider"], "openai")
            app = create_app(workspace=ws)
            client = TestClient(app)
            got = client.get("/v1/desktop/config").json()
            self.assertTrue(got["hasKey"])
            self.assertEqual(got["provider"], "openai")


if __name__ == "__main__":
    unittest.main()
