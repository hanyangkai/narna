"""E2E stub — OpenAI Agents-style wrap (no API key)."""

from pathlib import Path

from narna import wrap
from uap.governance_runtime import ConstitutionRuntime


def main() -> None:
    ws = Path(__file__).resolve().parent / "_demo_openai"
    ws.mkdir(exist_ok=True)
    ConstitutionRuntime(ws).load(provider="eu-ai-act", version="2.0.0")

    class FakeOpenAIAgent:
        def run(self, prompt: str) -> str:
            return f"ok:{prompt}"

    FakeOpenAIAgent.__module__ = "agents.agent"
    agent = wrap(FakeOpenAIAgent(), workspace=ws, vap=True, mode="enforce")
    assert agent._adapter["package"] == "narna-openai"
    assert agent._wrapped.run("hi") == "ok:hi"
    print("e2e_openai: PASS", agent._adapter)


if __name__ == "__main__":
    main()
