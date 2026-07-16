from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class CertificationLevelsTest(unittest.TestCase):
    def test_l1_without_vap(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("L1Bot", workspace=ws)
            # no VAP — still L1 via constitution + identity + passport cite
            cert = agent.certify(level="L1", remote=False)
            self.assertEqual(cert["status"], "passed")
            self.assertEqual(cert["level"], "L1")
            self.assertEqual(cert["badge"], "NARNA Certified")

    def test_l2_with_vap(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("L2Bot", workspace=ws)
            agent.enable_vap()
            agent.run("hello")
            cert = agent.certify(level="L2", remote=False)
            self.assertEqual(cert["status"], "passed")
            self.assertIn(cert["level"], {"L2", "L3"})
            self.assertIn(cert["badge"], {"NARNA Certified+", "Enterprise Ready"})

    def test_l3_enterprise_ready(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("L3Bot", workspace=ws)
            agent.enable_vap()
            agent.run("hello")
            cert = agent.certify(level="L3", remote=False)
            self.assertEqual(cert["status"], "passed")
            self.assertEqual(cert["level"], "L3")
            self.assertEqual(cert["badge"], "Enterprise Ready")
            self.assertTrue(any(c["id"] == "governance" and c["passed"] for c in cert["checks"]))

    def test_target_l2_fails_without_vap_but_reports_l1(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("Partial", workspace=ws)
            agent.run("hello")  # no vap
            cert = agent.certify(level="L2", remote=False)
            self.assertEqual(cert["status"], "failed")
            self.assertEqual(cert["level"], "L1")
            self.assertTrue(any("ProofBundle" in f for f in cert["failures"]))


class Phase4CertificationCompatTest(unittest.TestCase):
    """Keep remote submit path green with new level fields."""

    def test_remote_certify_submit(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "cert.db"
        env = {
            **os.environ,
            "UAP_DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
        }
        proc = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8772"],
            cwd=str(REPO / "web" / "backend"),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            import time
            import urllib.request

            for _ in range(40):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8772/v1/health", timeout=1):
                        break
                except Exception:
                    time.sleep(0.2)
            else:
                self.fail("API did not start")

            from narna import Agent

            with tempfile.TemporaryDirectory() as td:
                ws = Path(td)
                agent = Agent("CloudCertL", workspace=ws)
                agent.enable_vap()
                agent.run("ping")
                agent.publish(
                    remote=True,
                    registry_url="http://127.0.0.1:8772",
                    api_key="uap_live_dev_local_key_change_in_prod",
                )
                cert = agent.certify(
                    level="L3",
                    remote=True,
                    registry_url="http://127.0.0.1:8772",
                    api_key="uap_live_dev_local_key_change_in_prod",
                )
                self.assertEqual(cert["level"], "L3")
                if cert.get("remote"):
                    aid = agent.spec.agent_id
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:8772/v1/passport/{aid}", timeout=5
                    ) as resp:
                        passport = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(passport.get("verified"))
                    self.assertEqual(passport.get("level"), "L3")
                    self.assertEqual(passport.get("badge"), "Enterprise Ready")
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
