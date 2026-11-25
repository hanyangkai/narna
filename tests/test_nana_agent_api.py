"""Nana Agent IAP verify + paywall gating (no network / no sqlalchemy)."""

from __future__ import annotations

import base64
import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MOD_PATH = REPO / "web" / "backend" / "app" / "nana_agent_api.py"


def _load_api():
    # Load module file directly to avoid importing web.backend.app package (sqlalchemy).
    spec = importlib.util.spec_from_file_location("nana_agent_api_isolated", MOD_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Minimal fastapi stubs if fastapi missing
    try:
        import fastapi  # noqa: F401
        import pydantic  # noqa: F401
    except ImportError:
        # Skip — environment without web deps
        return None
    sys.modules["nana_agent_api_isolated"] = mod
    spec.loader.exec_module(mod)
    return mod


def _fake_jws(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"eyJhbGciOiJub25lIn0.{body}.x"


class NanaAgentAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api = _load_api()

    def setUp(self) -> None:
        if self.api is None:
            self.skipTest("fastapi/pydantic not installed")
        self.api._ENTITLEMENTS.clear()

    def test_verify_grants_basic_credits(self) -> None:
        jws = _fake_jws(
            {
                "productId": "nana.agent.basic.monthly",
                "transactionId": "txn-1",
                "expiresDate": 9999999999999,
            }
        )
        out = self.api.agent_verify(
            self.api.VerifyBody(deviceId="device-abc-12345", signedTransaction=jws)
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["entitlement"]["creditsRemaining"], 500)

    def test_chat_requires_entitlement(self) -> None:
        from fastapi import HTTPException

        with self.assertRaises(HTTPException) as ctx:
            self.api.agent_chat(
                self.api.AgentChatBody(
                    deviceId="device-abc-12345",
                    messages=[{"role": "user", "content": "hi"}],
                )
            )
        self.assertEqual(ctx.exception.status_code, 402)

    def test_chat_after_verify_burns_credits(self) -> None:
        jws = _fake_jws(
            {
                "productId": "nana.agent.basic.monthly",
                "transactionId": "txn-2",
                "expiresDate": 9999999999999,
            }
        )
        self.api.agent_verify(
            self.api.VerifyBody(deviceId="device-xyz-99999", signedTransaction=jws)
        )
        out = self.api.agent_chat(
            self.api.AgentChatBody(
                deviceId="device-xyz-99999",
                messages=[{"role": "user", "content": "hello agent"}],
                signedTransaction=jws,
            )
        )
        self.assertTrue(out["ok"])
        self.assertIn("content", out)
        self.assertLess(out["creditsRemaining"], 500)


if __name__ == "__main__":
    unittest.main()
