"""P5 TUI + P8 gateway pairing tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from uap.gateway_pairing import GatewayPairingStore, gate_inbound, pairing_enabled
from uap.gateway_runner import UnifiedGateway
from uap.slash_commands import SLASH_CMDS, parse_slash
from uap.tui_app import run_tui


class PairingTests(unittest.TestCase):
    def test_gate_blocks_then_pairs(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            with mock.patch.dict(os.environ, {"UAP_GATEWAY_PAIRING": "1"}):
                self.assertTrue(pairing_enabled())
                blocked = gate_inbound(
                    channel="telegram",
                    external_id="99",
                    text="hello",
                    workspace=td,
                )
                self.assertIsNotNone(blocked)
                assert blocked is not None
                self.assertTrue(blocked.get("blocked"))
                code = blocked.get("pairingCode")
                self.assertTrue(code)
                confirm = gate_inbound(
                    channel="telegram",
                    external_id="99",
                    text=f"/pair {code}",
                    workspace=td,
                )
                self.assertTrue(confirm and confirm.get("paired"))
                allow = gate_inbound(
                    channel="telegram",
                    external_id="99",
                    text="hello again",
                    workspace=td,
                )
                self.assertIsNone(allow)

    def test_pairing_off_allows(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            env = {k: v for k, v in os.environ.items() if k != "UAP_GATEWAY_PAIRING"}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertIsNone(
                    gate_inbound(
                        channel="telegram",
                        external_id="1",
                        text="hi",
                        workspace=td,
                    )
                )

    def test_store_status_and_direct_pair(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            store = GatewayPairingStore(td)
            out = store.pair_direct("telegram", "42")
            self.assertTrue(out["ok"])
            self.assertTrue(store.is_paired("telegram", "42") or not pairing_enabled())
            st = store.status()
            self.assertIn("pairedCount", st)

    def test_gateway_handle_inbound_pairing(self):
        calls: list[str] = []

        def ask_fn(msg: str, channel: str, external_id: str | None) -> dict:
            calls.append(msg)
            return {"ok": True, "answer": "ok", "dqs": 80}

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            with mock.patch.dict(os.environ, {"UAP_GATEWAY_PAIRING": "1"}):
                gw = UnifiedGateway(ask_fn=ask_fn, workspace=td)
                out = gw.handle_inbound(channel="telegram", text="yo", external_id="7")
                self.assertTrue(out.get("pairing"))
                self.assertEqual(calls, [])
                code = None
                # extract code from answer
                for part in str(out.get("answer") or "").split():
                    if len(part) == 6 and part.isalnum():
                        code = part
                        break
                self.assertTrue(code)
                gw.handle_inbound(channel="telegram", text=f"/pair {code}", external_id="7")
                out2 = gw.handle_inbound(channel="telegram", text="real", external_id="7")
                self.assertEqual(calls, ["real"])
                self.assertEqual(out2.get("answer"), "ok")


class TuiTests(unittest.TestCase):
    def test_slash_cmds_export(self):
        self.assertIn("/help", SLASH_CMDS)
        self.assertEqual(parse_slash("/new")["cmd"], "/new")

    def test_tui_without_textual_exits_1(self):
        import sys

        # Force ImportError path by hiding textual
        with mock.patch.dict(sys.modules, {"textual": None, "textual.app": None}):
            # If textual is installed, run_tui imports succeed — skip soft
            try:
                import textual  # noqa: F401

                self.skipTest("textual installed — exit-1 path not exercised")
            except ImportError:
                code = run_tui(provider="mock")
                self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
