"""E2E stub — MCP client wrap + HIPAA package deny."""

from pathlib import Path

from narna import wrap
from uap.governance_runtime import ConstitutionRuntime


def main() -> None:
    ws = Path(__file__).resolve().parent / "_demo_mcp"
    ws.mkdir(exist_ok=True)
    ConstitutionRuntime(ws).load(provider="hipaa", version="2.0.0")

    class FakeMcpClient:
        def call_tool(self, name: str, arguments: dict | None = None):
            return {"tool": name, "arguments": arguments or {}}

    FakeMcpClient.__module__ = "mcp.client"
    agent = wrap(FakeMcpClient(), workspace=ws, vap=True, mode="enforce")
    assert agent._adapter["package"] == "narna-mcp"
    out = agent._wrapped.call_tool("memory.read", {})
    assert out["tool"] == "memory.read"
    denied = ConstitutionRuntime(ws).execute(action="phi.exfiltrate")
    assert denied["decision"] == "deny"
    print("e2e_mcp: PASS", denied["reasons"])


if __name__ == "__main__":
    main()
