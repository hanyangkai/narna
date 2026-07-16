from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class ConstitutionSpecTest(unittest.TestCase):
    def test_example_constitution_validates(self) -> None:
        from narna import load_constitution

        path = REPO / "specs" / "examples" / "constitution.yaml"
        doc = load_constitution(path)
        self.assertEqual(doc["kind"], "Constitution")
        self.assertEqual(doc["metadata"]["entityKind"], "Agent")
        self.assertIn("browser", doc["spec"]["capability"]["supports"])

    def test_agent_writes_constitution(self) -> None:
        from narna import Agent, load_constitution

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("ConstAgent", workspace=ws)
            path = ws / "constitution.yaml"
            self.assertTrue(path.exists())
            doc = load_constitution(path)
            self.assertEqual(doc["metadata"]["entityId"], agent.spec.agent_id)
            loaded = agent.constitution()
            self.assertEqual(loaded["kind"], "Constitution")


if __name__ == "__main__":
    unittest.main()
