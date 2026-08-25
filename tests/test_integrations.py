"""CMEM bridge + hot-stack adapter integration tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class CmemBridgeTest(unittest.TestCase):
    def test_local_ingest_enrich_boosts_memory(self) -> None:
        from uap.adqa import ADQAEngine
        from uap.cmem_bridge import CmemBridge

        with tempfile.TemporaryDirectory() as td:
            bridge = CmemBridge(td)
            bridge.ingest_local(
                {
                    "summary": "Prior contract.sign required dual approval",
                    "action": "contract.sign",
                    "tags": ["legal"],
                }
            )
            ctx = bridge.enrich_context("contract.sign")
            self.assertGreaterEqual(ctx["_cmem"]["count"], 1)
            out = ADQAEngine(td).check_proposed(
                action="contract.sign",
                provider="legal-decision",
                evidence_present=["policy.decision", "human.review", "contract.hash"],
                context=ctx,
                persist=False,
            )
            mem = out["adqa"]["attributes"]["memory"]
            self.assertGreaterEqual(mem, 70)

    def test_mcp_tools_adqa(self) -> None:
        from narna.mcp_tools import NarnaMcpTools

        with tempfile.TemporaryDirectory() as td:
            tools = NarnaMcpTools(td)
            names = {t["name"] for t in tools.list_tools()}
            self.assertIn("narna_adqa_check", names)
            self.assertIn("narna_cmem_enrich", names)
            r = tools.call_tool(
                "narna_adqa_check",
                {
                    "action": "contract.sign",
                    "provider": "legal-decision",
                    "evidencePresent": ["policy.decision"],
                },
            )
            self.assertTrue(r.get("ok"))
            self.assertIn("adqa", r)


class HotAdaptersTest(unittest.TestCase):
    def test_catalog_includes_cmem_autogen_sk_llama(self) -> None:
        from narna.adapters import ADAPTER_CATALOG

        ids = {a["id"] for a in ADAPTER_CATALOG}
        for need in ("cmem", "autogen", "semantic_kernel", "llamaindex", "openai", "mcp"):
            self.assertIn(need, ids)

    def test_cmem_adapter_matches(self) -> None:
        from narna.adapters import detect_framework

        class FakeCmem:
            pass

        FakeCmem.__module__ = "cmem.client"
        FakeCmem.__name__ = "MemoryClient"
        self.assertEqual(detect_framework(FakeCmem()), "cmem")

    def test_autogen_adapter_hooks(self) -> None:
        from narna.adapters.autogen import AutogenAdapter

        class FakeAgent:
            def generate_reply(self, *a, **k):
                return "ok"

        FakeAgent.__module__ = "autogen.agentchat"
        FakeAgent.__name__ = "ConversableAgent"
        adapter = AutogenAdapter()
        self.assertTrue(adapter.matches(FakeAgent()))

    def test_integration_manifest(self) -> None:
        from narna.integrations import integration_manifest

        m = integration_manifest()
        self.assertTrue(m["ok"])
        self.assertTrue(any(p["id"] == "cmem" for p in m["memoryPartners"]))


if __name__ == "__main__":
    unittest.main()
