"""Thick e2e — MCP + NARNA MCP tools (ADQA) side-by-side with CMEM-style memory."""

from __future__ import annotations

import os
from pathlib import Path

from narna import NarnaMcpTools, wrap
from uap.cmem_bridge import CmemBridge
from uap.governance_runtime import ConstitutionRuntime


def main() -> None:
    os.environ["NARNA_ADQA"] = "1"
    ws = Path(__file__).resolve().parent / "_demo_mcp_adqa"
    ws.mkdir(exist_ok=True)
    ConstitutionRuntime(ws).load(provider="legal-decision", version="1.0.0")

    class FakeMcpClient:
        def call_tool(self, name: str, arguments: dict | None = None):
            return {"tool": name, "arguments": arguments or {}}

    FakeMcpClient.__module__ = "mcp.client"
    agent = wrap(FakeMcpClient(), workspace=ws, vap=True, mode="enforce")
    assert agent._adapter["package"] == "narna-mcp"

    CmemBridge(ws).ingest_local(
        {"summary": "Prior dual-approval for contract.sign", "action": "contract.sign"}
    )
    tools = NarnaMcpTools(ws)
    enrich = tools.call_tool("narna_cmem_enrich", {"action": "contract.sign"})
    assert enrich.get("ok")
    adqa = tools.call_tool(
        "narna_adqa_check",
        {
            "action": "contract.sign",
            "provider": "legal-decision",
            "evidencePresent": ["policy.decision", "human.review", "contract.hash"],
        },
    )
    assert adqa.get("ok") and "adqa" in adqa
    print("e2e_mcp_adqa: PASS", adqa["adqa"]["dqs"], enrich["cmem"]["count"])


if __name__ == "__main__":
    main()
