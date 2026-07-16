from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from uap.agent import Agent
from uap.policy import PolicyEngine
from uap.spec import load_agent_spec
from uap.tools import TOOL_ADAPTERS
from uap.verify import verify_proof_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_SPEC = REPO_ROOT / "specs" / "examples" / "trading-agent.yaml"


def _setup_workspace(workspace: Path) -> None:
    import shutil

    if not (workspace / "policies").exists() and (REPO_ROOT / "policies").exists():
        shutil.copytree(REPO_ROOT / "policies", workspace / "policies")


class UapSmokeTest(unittest.TestCase):
    def test_agent_spec_validates(self) -> None:
        spec = load_agent_spec(EXAMPLE_SPEC)
        self.assertEqual(spec.name, "Trading Agent")

    def test_price_run_prove_verify(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            _setup_workspace(workspace)
            agent = Agent.from_spec(EXAMPLE_SPEC, workspace=workspace)
            result = agent.run(input="btc price")
            self.assertEqual(result.state, "Completed")
            bundle = agent.prove(result.run_id)
            ok, problems = verify_proof_bundle(bundle)
            self.assertTrue(ok, msg="\n".join(problems))
            self.assertTrue(bundle["evidence"])

    def test_wallet_ask_flow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            _setup_workspace(workspace)
            agent = Agent.from_spec(EXAMPLE_SPEC, workspace=workspace)
            pending = agent.run(input="wallet transfer")
            self.assertEqual(pending.state, "AwaitingInput")
            done = agent.resolve_ask(pending.run_id, approved=True)
            self.assertEqual(done.state, "Completed")

    def test_init_register_marketplace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            _setup_workspace(workspace)
            import shutil

            shutil.copy(EXAMPLE_SPEC, workspace / "agent.yaml")
            agent = Agent.from_spec(workspace / "agent.yaml", workspace=workspace)
            entry = agent.register()
            self.assertIn("agentId", entry)
            index = agent.marketplace_index()
            self.assertIn("trade", index)


class PolicyTest(unittest.TestCase):
    def test_deny_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            _setup_workspace(ws)
            engine = PolicyEngine(ws)
            decision = engine.evaluate(
                policy_ref="policies/local-default@0.0.0",
                agent_permissions=[],
                permission="wallet.transfer",
            )
            self.assertEqual(decision["decision"], "deny")


class ToolsTest(unittest.TestCase):
    def test_tools_registered(self) -> None:
        self.assertIn("coinbase.spot_price", TOOL_ADAPTERS)
        self.assertIn("wallet.transfer", TOOL_ADAPTERS)


if __name__ == "__main__":
    unittest.main()
