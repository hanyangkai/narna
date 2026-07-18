"""UGS conformance CLI tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class ConformanceTest(unittest.TestCase):
    def test_conformance_with_template_manifest(self) -> None:
        from narna.conformance import run_conformance

        root = Path(__file__).resolve().parents[1]
        template = root / "templates" / "narna.yaml"
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / "narna.yaml").write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
            report = run_conformance(workspace=ws)
            self.assertIn("checks", report)
            self.assertTrue(any(c["id"] == "manifest" and c["ok"] for c in report["checks"]))
