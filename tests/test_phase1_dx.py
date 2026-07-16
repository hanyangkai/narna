from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class Phase1DxTest(unittest.TestCase):
    def test_pip_style_import_and_zero_config_run(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent(workspace=ws)
            result = agent.run()
            self.assertEqual(result.state, "Completed")
            self.assertTrue(result.run_id)

    def test_named_agent_and_vap(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("Researcher", workspace=ws)
            agent.enable_vap()
            result = agent.run("hello world")
            self.assertEqual(result.state, "Completed")
            bundle_path = ws / ".uap" / "runs" / result.run_id / "proof-bundle.json"
            self.assertTrue(bundle_path.exists())

    def test_wrap_creates_agent(self) -> None:
        from narna import wrap

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)

            class FakeGraph:
                name = "LangGraphDemo"

            agent = wrap(FakeGraph(), workspace=ws)
            result = agent.run("ping")
            self.assertEqual(result.state, "Completed")
            self.assertIsNotNone(agent._wrapped)

    def test_publish_local(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("Publisher", workspace=ws)
            out = agent.publish()
            self.assertEqual(out.get("status"), "local")
            self.assertIn("agentId", out)


if __name__ == "__main__":
    unittest.main()
