from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACKAGES = REPO / "specs" / "examples" / "packages"


class ConstitutionRuntimeTest(unittest.TestCase):
    def test_load_execute_deny_and_switch(self) -> None:
        from uap.governance_runtime import ConstitutionRuntime

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            rt = ConstitutionRuntime(ws)
            loaded = rt.load(provider="eu-ai-act", version="2.0.0")
            self.assertEqual(loaded["binding"]["provider"], "eu-ai-act")
            hash1 = loaded["binding"]["packageHash"]

            denied = rt.execute(action="biometric.scrape")
            self.assertEqual(denied["decision"], "deny")
            self.assertEqual(denied["packageHash"], hash1)

            switched = rt.switch(provider="hipaa", version="2.0.0")
            hash2 = switched["binding"]["packageHash"]
            self.assertNotEqual(hash1, hash2)
            denied2 = rt.execute(action="prescription.autonomous")
            self.assertEqual(denied2["decision"], "deny")
            self.assertEqual(denied2["packageHash"], hash2)

    def test_constitution_yaml_rules_enforced(self) -> None:
        from uap.governance_runtime import ConstitutionRuntime

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            # use anthropic stub which denies network.exfiltrate
            rt = ConstitutionRuntime(ws)
            rt.load(path=PACKAGES / "anthropic-constitution.yaml")
            d = rt.execute(action="network.exfiltrate")
            self.assertEqual(d["decision"], "deny")

    def test_package_registry_local(self) -> None:
        from uap.packages import list_local_packages, register_package_local, search_packages

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            entry = register_package_local(ws, PACKAGES / "eu-ai-act.yaml")
            self.assertEqual(entry["provider"], "eu-ai-act")
            self.assertEqual(len(list_local_packages(ws)), 1)
            found = search_packages(ws, "eu")
            self.assertEqual(len(found), 1)


class PortableGovernanceTest(unittest.TestCase):
    def test_same_package_hash_across_vendor_wrap(self) -> None:
        from narna import wrap
        from uap.governance_runtime import ConstitutionRuntime

        class FakeOpenAI:
            def run(self, prompt: str) -> str:
                return f"openai:{prompt}"

        FakeOpenAI.__module__ = "agents.agent"

        class FakeAnthropic:
            def run(self, prompt: str) -> str:
                return f"anthropic:{prompt}"

        FakeAnthropic.__module__ = "anthropic"

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            rt = ConstitutionRuntime(ws)
            binding = rt.load(provider="eu-ai-act", version="2.0.0")["binding"]
            pkg_hash = binding["packageHash"]

            a1 = wrap(FakeOpenAI(), workspace=ws, vap=False, name="Portable A")
            a2 = wrap(FakeAnthropic(), workspace=ws, vap=False, name="Portable B")

            # same workspace active governance
            active = ConstitutionRuntime(ws).active()
            self.assertIsNotNone(active)
            assert active is not None
            self.assertEqual(active["packageHash"], pkg_hash)
            self.assertEqual(a1._adapter["package"], "narna-openai")
            self.assertEqual(a2._adapter["package"], "narna-anthropic")

    def test_passport_cites_governance_package(self) -> None:
        from narna import Agent
        from uap.governance_runtime import ConstitutionRuntime

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            ConstitutionRuntime(ws).load(provider="eu-ai-act", version="2.0.0")
            agent = Agent(workspace=ws, name="GovBot")
            passport = agent.passport(refresh=True)
            self.assertIn("governance", passport)
            self.assertTrue(passport["governance"]["packageHash"].startswith("sha256:"))
            self.assertEqual(passport["governance"]["provider"], "eu-ai-act")

    def test_agent_load_governance(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent(workspace=ws, name="Loader")
            loaded = agent.load_governance(provider="hipaa", version="2.0.0")
            self.assertEqual(loaded["binding"]["provider"], "hipaa")

    def test_fleet_min_certification_blocks_publish(self) -> None:
        import yaml
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "fleet.yaml").write_text(
                yaml.safe_dump(
                    {
                        "apiVersion": "narna.ai/v1alpha1",
                        "kind": "Fleet",
                        "metadata": {"id": "fleet_test", "orgId": "org"},
                        "spec": {
                            "defaults": {"minCertification": "L2"},
                            "members": [{"entityId": "agent", "role": "worker"}],
                            "roles": {"worker": {"can": ["*"]}},
                        },
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            agent = Agent(workspace=ws, name="FleetBot")
            with self.assertRaises(ValueError) as ctx:
                agent.publish(remote=False)
            self.assertIn("minCertification", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
