from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


class Phase3RegistryTest(unittest.TestCase):
    def test_local_publish_and_trending(self) -> None:
        from narna import Agent

        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            agent = Agent("TradingBot", workspace=ws)
            agent.enable_vap()
            agent.run("hello")
            out = agent.publish(remote=False, category="trade")
            self.assertIn("agentId", out)
            self.assertEqual(out.get("category"), "trade")
            self.assertEqual(out.get("status"), "local")
            trend = agent.registry_trending(category="trade")
            self.assertTrue(any(r["agentId"] == out["agentId"] for r in trend))
            hits = agent.registry_search(capability="general")
            self.assertTrue(hits or agent.registry_search(q="Trading"))

    def test_remote_publish_to_cloud(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "reg.db"
        env = {
            **os.environ,
            "UAP_DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
        }
        proc = subprocess.Popen(
            ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8770"],
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
                    with urllib.request.urlopen("http://127.0.0.1:8770/v1/health", timeout=1):
                        break
                except Exception:
                    time.sleep(0.2)
            else:
                self.fail("API did not start")

            from narna import Agent

            with tempfile.TemporaryDirectory() as td:
                ws = Path(td)
                agent = Agent("CloudBot", workspace=ws)
                agent.enable_vap()
                agent.run("ping")
                out = agent.publish(
                    remote=True,
                    category="code",
                    registry_url="http://127.0.0.1:8770",
                    api_key="uap_live_dev_local_key_change_in_prod",
                )
                self.assertIn(out.get("status"), {"published", "local"})
                if out.get("status") == "published":
                    aid = out["agentId"]
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:8770/v1/passport/{aid}", timeout=5
                    ) as resp:
                        passport = json.loads(resp.read().decode("utf-8"))
                    self.assertEqual(passport["name"], "CloudBot")
                    with urllib.request.urlopen(
                        "http://127.0.0.1:8770/v1/registry/trending", timeout=5
                    ) as resp2:
                        trend = json.loads(resp2.read().decode("utf-8"))
                    self.assertTrue(any(a["agentId"] == aid for a in trend))
        finally:
            proc.terminate()
            proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
