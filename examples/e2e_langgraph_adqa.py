"""Thick e2e — LangGraph-style graph + ADQA gate (NARNA_ADQA=1)."""

from __future__ import annotations

import os
from pathlib import Path

from narna import wrap
from uap.adqa import ADQAEngine
from uap.governance_runtime import ConstitutionRuntime


def main() -> None:
    os.environ["NARNA_ADQA"] = "1"
    os.environ["NARNA_ADQA_STRICT"] = "0"
    ws = Path(__file__).resolve().parent / "_demo_langgraph_adqa"
    ws.mkdir(exist_ok=True)
    ConstitutionRuntime(ws).load(provider="legal-decision", version="1.0.0")

    class CompiledStateGraph:
        def invoke(self, state: dict):
            return {"ok": True, "state": state}

    CompiledStateGraph.__module__ = "langgraph.graph.state"
    graph = CompiledStateGraph()
    agent = wrap(graph, workspace=ws, vap=True, mode="enforce")
    assert agent._adapter["package"] == "narna-langgraph"

    out = agent._wrapped.invoke({"action": "contract.sign"})
    assert out["ok"] is True
    # Direct ADQA path (Cloud-equivalent)
    adqa = ADQAEngine(ws).check_proposed(
        action="contract.sign",
        provider="legal-decision",
        evidence_present=["policy.decision", "human.review", "contract.hash"],
        persist=False,
    )
    assert "dqs" in adqa["adqa"]
    print("e2e_langgraph_adqa: PASS", adqa["adqa"]["guardian"], adqa["adqa"]["dqs"])


if __name__ == "__main__":
    main()
