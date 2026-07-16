from __future__ import annotations

import os
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class CloudIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.ws = Path(cls._tmp.name)
        import shutil

        shutil.copytree(REPO / "policies", cls.ws / "policies")
        shutil.copy(REPO / "specs" / "examples" / "trading-agent.yaml", cls.ws / "agent.yaml")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_push_run_to_cloud_api(self) -> None:
        db_path = self.ws / "test_cloud.db"
        env = {
            **os.environ,
            "UAP_DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
        }
        proc = subprocess.Popen(
            [
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
            ],
            cwd=str(REPO / "web" / "backend"),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            import time
            import urllib.request

            for _ in range(30):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8765/v1/health", timeout=1):
                        break
                except Exception:
                    time.sleep(0.2)
            else:
                self.fail("API did not start")

            from uap.agent import Agent
            from uap_cloud import push_run

            agent = Agent.from_spec(self.ws / "agent.yaml", workspace=self.ws)
            result = agent.run(input="btc price")
            agent.prove(result.run_id)

            resp = push_run(
                workspace=self.ws,
                run_id=result.run_id,
                api_key="uap_live_dev_local_key_change_in_prod",
                base_url="http://127.0.0.1:8765",
                agent_id=agent.spec.agent_id,
                agent_name=agent.spec.name,
            )
            self.assertTrue(resp.get("ok"))
            self.assertGreater(resp.get("eventsIngested", 0), 0)
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_billing_mock_and_metrics(self) -> None:
        db_path = self.ws / "test_cloud.db"
        env = {
            **os.environ,
            "UAP_DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
        }
        proc = subprocess.Popen(
            [
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8766",
            ],
            cwd=str(REPO / "web" / "backend"),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            import time
            import urllib.request

            for _ in range(30):
                try:
                    with urllib.request.urlopen(
                        "http://127.0.0.1:8766/v1/health", timeout=1
                    ):
                        break
                except Exception:
                    time.sleep(0.2)
            else:
                self.fail("API did not start")

            api_key = "uap_live_dev_local_key_change_in_prod"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            req = urllib.request.Request(
                "http://127.0.0.1:8766/v1/billing/mock/set-plan",
                data=json.dumps({"plan": "pro"}).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(body.get("ok"))

            req2 = urllib.request.Request(
                "http://127.0.0.1:8766/v1/metrics",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                metrics = json.loads(resp2.read().decode("utf-8"))
            self.assertEqual(metrics.get("plan"), "pro")

            req3 = urllib.request.Request(
                "http://127.0.0.1:8766/v1/billing/status",
                headers={"Authorization": f"Bearer {api_key}"},
                method="GET",
            )
            with urllib.request.urlopen(req3, timeout=10) as resp3:
                status = json.loads(resp3.read().decode("utf-8"))
            self.assertEqual(status.get("plan"), "pro")
            self.assertIn("eventsInPeriod", status)

            req4 = urllib.request.Request(
                "http://127.0.0.1:8766/v1/billing/crypto/checkout-session",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
                data=json.dumps({"plan": "team", "asset": "usdc", "network": "polygon"}).encode("utf-8"),
            )
            with urllib.request.urlopen(req4, timeout=10) as resp4:
                crypto = json.loads(resp4.read().decode("utf-8"))
            self.assertTrue(crypto.get("ok"))
            self.assertEqual(crypto.get("asset"), "usdc")
            self.assertEqual(crypto.get("plan"), "team")
            self.assertEqual(crypto.get("network"), "polygon")
            self.assertIn("recipientWallet", crypto)
            self.assertIn("expectedAmount", crypto)
            self.assertIn("expiresAt", crypto)
            self.assertIn("qrPayload", crypto)

            req5 = urllib.request.Request(
                "http://127.0.0.1:8766/v1/billing/crypto/networks",
                method="GET",
            )
            with urllib.request.urlopen(req5, timeout=10) as resp5:
                networks = json.loads(resp5.read().decode("utf-8"))
            self.assertGreaterEqual(len(networks), 5)
            ids = {n.get("id") for n in networks}
            self.assertIn("ethereum", ids)
            self.assertIn("polygon", ids)
            self.assertIn("base", ids)

            with urllib.request.urlopen(req3, timeout=10) as resp6:
                status2 = json.loads(resp6.read().decode("utf-8"))
            self.assertEqual(status2.get("plan"), "team")
        finally:
            proc.terminate()
            proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
