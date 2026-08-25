"""Tier C — federation demo + docker container plan."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class FederationDemoTest(unittest.TestCase):
    def test_script_local(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts" / "federation_demo.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=60,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
        self.assertIn("NGS-0020", proc.stdout)
        self.assertIn('"ok": true', proc.stdout)


class DockerRunnerTest(unittest.TestCase):
    def test_dry_run_plan(self) -> None:
        from uap.container_runner import DockerContainerRunner

        with tempfile.TemporaryDirectory() as td:
            out = DockerContainerRunner(td).run(dry_run=True, agent_id="demo")
            self.assertTrue(out["ok"])
            self.assertTrue(out["dryRun"])
            self.assertIn("--network", out["argv"])
            self.assertIn("none", out["argv"])


if __name__ == "__main__":
    unittest.main()
