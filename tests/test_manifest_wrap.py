from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class ManifestAndWrapTest(unittest.TestCase):
    def test_compile_example_narna_yaml(self) -> None:
        from narna import load_or_compile_constitution

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            src = REPO / "specs" / "examples" / "narna.yaml"
            dest = ws / "narna.yaml"
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            doc = load_or_compile_constitution(dest, workspace=ws)
            self.assertEqual(doc["kind"], "Constitution")
            self.assertTrue((ws / "constitution.yaml").exists())
            self.assertIn("web_search", doc["spec"]["capability"]["supports"])

    def test_wrap_attaches_adapter_metadata(self) -> None:
        from narna import wrap

        class FakeLangGraph:
            name = "graph"

        # pretend module
        FakeLangGraph.__module__ = "langgraph.graph.graph"

        with tempfile.TemporaryDirectory() as td:
            agent = wrap(FakeLangGraph(), workspace=td, vap=False)
            self.assertEqual(getattr(agent, "_framework", None), "langgraph")
            self.assertEqual(agent._adapter["package"], "narna-langgraph")

    def test_track_decorator_preserves_return(self) -> None:
        from narna import track

        with tempfile.TemporaryDirectory() as td:
            @track(workspace=td, vap=False)
            def add(x: int, y: int) -> int:
                return x + y

            self.assertEqual(add(2, 3), 5)


if __name__ == "__main__":
    unittest.main()
