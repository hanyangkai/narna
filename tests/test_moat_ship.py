from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class InitValidateTest(unittest.TestCase):
    def test_init_creates_narna_yaml(self) -> None:
        from uap.cli import cmd_init
        import argparse

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            prev = Path.cwd()
            try:
                import os

                os.chdir(ws)
                rc = cmd_init(argparse.Namespace(name="TestBot"))
                self.assertEqual(rc, 0)
                self.assertTrue((ws / "narna.yaml").exists())
                self.assertTrue((ws / "constitution.yaml").exists())
            finally:
                os.chdir(prev)

    def test_validate_passes_after_init(self) -> None:
        from uap.cli import cmd_init, cmd_validate
        import argparse

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            prev = Path.cwd()
            try:
                import os

                os.chdir(ws)
                cmd_init(argparse.Namespace(name="ValidBot"))
                rc = cmd_validate(argparse.Namespace(manifest=None, spec="agent.yaml", compile=False, skip_manifest=False, full=False))
                self.assertEqual(rc, 0)
            finally:
                os.chdir(prev)


class NarnaScoreTest(unittest.TestCase):
    def test_score_returns_0_100(self) -> None:
        from uap.narna_score import compute_narna_score

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / ".uap" / "identity").mkdir(parents=True)
            (ws / "narna.yaml").write_text(
                (REPO / "specs/examples/narna-governance-binding.yaml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            out = compute_narna_score(ws)
            self.assertIn("narnaScore", out)
            self.assertGreaterEqual(out["narnaScore"], 0)
            self.assertLessEqual(out["narnaScore"], 100)
            self.assertEqual(len(out["breakdown"]), 6)


class DecoratorTest(unittest.TestCase):
    def test_agent_decorator_runs(self) -> None:
        from narna import agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)

            @agent(workspace=ws, vap=False)
            def hello(q: str) -> str:
                return f"hi:{q}"

            self.assertEqual(hello("world"), "hi:world")


class AdapterTest(unittest.TestCase):
    def test_openai_adapter_matches(self) -> None:
        from narna.adapters.openai_agents import OpenAIAdapter

        class FakeOpenAI:
            __module__ = "openai.resources.chat.completions"

            def create(self, *a, **k):
                return "ok"

        ad = OpenAIAdapter()
        self.assertTrue(ad.matches(FakeOpenAI()))

    def test_mcp_adapter_matches(self) -> None:
        from narna.adapters.mcp import McpAdapter

        class FakeMCP:
            __module__ = "mcp.server"

            def call_tool(self, name: str) -> str:
                return name

        ad = McpAdapter()
        self.assertTrue(ad.matches(FakeMCP()))

    def test_otel_adapter_matches(self) -> None:
        from narna.adapters.otel import OpenTelemetryAdapter

        class Span:
            pass

        Span.__module__ = "opentelemetry.trace"
        ad = OpenTelemetryAdapter()
        self.assertTrue(ad.matches(Span()))


class ManifestGovernanceBindingTest(unittest.TestCase):
    def test_governance_package_field_loads(self) -> None:
        from uap.manifest import bind_governance_from_manifest
        import yaml

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            doc = yaml.safe_load(
                """
apiVersion: narna.ai/v1alpha1
kind: Manifest
identity: {id: test-agent}
governance:
  package: eu-ai-act@1.0.0
"""
            )
            result = bind_governance_from_manifest(doc, ws)
            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result["binding"]["provider"], "eu-ai-act")


class PassportSignTest(unittest.TestCase):
    def test_sign_and_verify_passport(self) -> None:
        from uap.passport_sign import verify_passport_signature
        from uap.agent import Agent
        from uap.manifest import ensure_workspace_manifest, load_or_compile_constitution
        from uap.identity import IdentityStore
        from uap.registry import AgentRegistry

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            ensure_workspace_manifest(ws, agent_name="SignBot")
            load_or_compile_constitution(ws / "narna.yaml", workspace=ws)
            agent = Agent(workspace=ws, name="SignBot")
            IdentityStore(ws).issue(agent.spec)
            spec_path = ws / "agent.yaml"
            import yaml

            spec_path.write_text(yaml.safe_dump(agent.spec.raw, sort_keys=False), encoding="utf-8")
            AgentRegistry(ws).register(spec_path, workspace=ws)
            passport = agent.passport(refresh=True)
            self.assertIn("signature", passport)
            ok, problems = verify_passport_signature(passport, workspace=ws)
            self.assertTrue(ok, problems)


class OtelExportTest(unittest.TestCase):
    def test_otel_export_dry_run(self) -> None:
        from narna.adapters.otel_export import export_run_to_otlp

        out = export_run_to_otlp({"agentId": "a1", "runId": "r1"}, dry_run=True)
        self.assertIn("attributes", out)
        self.assertEqual(out["attributes"]["narna.agent_id"], "a1")
        self.assertTrue(out.get("dryRun"))


if __name__ == "__main__":
    unittest.main()
