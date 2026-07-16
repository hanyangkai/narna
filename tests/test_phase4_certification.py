from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class Phase4CertificationTest(unittest.TestCase):
    def test_certify_passes_with_vap(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("CertBot", workspace=ws)
            agent.enable_vap()
            agent.run("hello")
            cert = agent.certify(remote=False)
            self.assertEqual(cert["status"], "passed")
            self.assertEqual(cert["badge"], "Verified by NARNA")
            self.assertTrue(cert.get("verified"))
            self.assertTrue((ws / ".uap" / "certification" / f"{agent.spec.agent_id}.json").exists())
            entry = agent.registry_search(q="CertBot")
            self.assertTrue(any(e.get("verified") for e in entry))

    def test_certify_fails_without_vap_proof(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("NoVap", workspace=ws)
            # run without VAP → no proof bundle
            agent.run("hello")
            cert = agent.certify(remote=False)
            self.assertEqual(cert["status"], "failed")
            self.assertIsNone(cert.get("badge"))
            self.assertIn("ProofBundle present (VAP)", cert.get("failures", []))

    def test_remote_certify_submit(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "cert.db"
        env = {
            **os.environ,
            "UAP_DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
        }
        proc = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8771"],
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
                    with urllib.request.urlopen("http://127.0.0.1:8771/v1/health", timeout=1):
                        break
                except Exception:
                    time.sleep(0.2)
            else:
                self.fail("API did not start")

            from narna import Agent

            with tempfile.TemporaryDirectory() as td:
                ws = Path(td)
                agent = Agent("CloudCert", workspace=ws)
                agent.enable_vap()
                agent.run("ping")
                agent.publish(
                    remote=True,
                    registry_url="http://127.0.0.1:8771",
                    api_key="uap_live_dev_local_key_change_in_prod",
                )
                cert = agent.certify(
                    remote=True,
                    registry_url="http://127.0.0.1:8771",
                    api_key="uap_live_dev_local_key_change_in_prod",
                )
                self.assertEqual(cert["status"], "passed")
                if cert.get("remote"):
                    aid = agent.spec.agent_id
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:8771/v1/passport/{aid}", timeout=5
                    ) as resp:
                        passport = json.loads(resp.read().decode("utf-8"))
                    self.assertTrue(passport.get("verified"))
                    self.assertEqual(passport.get("badge"), "Verified by NARNA")
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
