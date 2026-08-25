"""Thick e2e — OpenAI-style client + ADQA optional gate."""

from __future__ import annotations

import os
from pathlib import Path

from narna import wrap
from uap.adqa import ADQAEngine
from uap.governance_runtime import ConstitutionRuntime


def main() -> None:
    os.environ["NARNA_ADQA"] = "1"
    ws = Path(__file__).resolve().parent / "_demo_openai_adqa"
    ws.mkdir(exist_ok=True)
    ConstitutionRuntime(ws).load(provider="legal-decision", version="1.0.0")

    class Completions:
        def create(self, **kwargs):
            return {"id": "chatcmpl-demo", "choices": [{"message": {"content": "ok"}}]}

    class Chat:
        def __init__(self):
            self.completions = Completions()

    class OpenAI:
        def __init__(self):
            self.chat = Chat()

        def run(self, prompt: str):
            return self.chat.completions.create(messages=[{"role": "user", "content": prompt}])

    OpenAI.__module__ = "openai"
    client = OpenAI()
    agent = wrap(client, workspace=ws, vap=True, mode="enforce")
    assert agent._adapter["package"] == "narna-openai"
    r = agent._wrapped.run("summarize contract")
    assert r["id"].startswith("chatcmpl")
    scored = ADQAEngine(ws).check_proposed(
        action="openai.run",
        provider="legal-decision",
        evidence_present=["policy.decision"],
        persist=False,
    )
    print("e2e_openai_adqa: PASS", scored["adqa"]["guardian"], agent._adapter.get("hooks"))


if __name__ == "__main__":
    main()
