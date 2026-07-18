"""Privacy-preserving Governance Telemetry tests."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from uap.telemetry import (
    agent_class,
    build_contribution_from_events,
    capability_family,
    strip_forbidden,
)


class TestTelemetrySanitizer(unittest.TestCase):
    def test_strip_forbidden_keys(self) -> None:
        dirty = {
            "decision": "allow",
            "prompt": "SECRET PROMPT",
            "tool": {"name": "sql", "arguments": {"q": "SELECT * FROM users"}, "result": "pii"},
            "nested": {"email": "a@b.com", "ok": 1},
        }
        clean = strip_forbidden(dirty)
        self.assertEqual(clean.get("decision"), "allow")
        self.assertNotIn("prompt", clean)
        self.assertNotIn("arguments", clean.get("tool", {}))
        self.assertNotIn("result", clean.get("tool", {}))
        self.assertNotIn("email", clean.get("nested", {}))
        self.assertEqual(clean.get("nested", {}).get("ok"), 1)

    def test_taxonomy(self) -> None:
        self.assertEqual(capability_family("postgres.query"), "database.query")
        self.assertEqual(capability_family("playwright_browse"), "browser.navigate")
        self.assertEqual(agent_class("finance-bot", "Bank Agent"), "finance")

    def test_build_contribution_no_prompt_leak(self) -> None:
        events = [
            {
                "eventType": "PolicyEvaluated",
                "sessionId": "session_abc",
                "payload": {
                    "decision": {
                        "decision": "ask",
                        "permission": "database.query",
                        "policyRef": "gdpr@2.0.0",
                        "reasons": ["human oversight"],
                    }
                },
            },
            {
                "eventType": "ExecutionUnitStarted",
                "sessionId": "session_abc",
                "payload": {
                    "executionUnit": {
                        "unitId": "eu_1",
                        "unitKind": "tool",
                        "toolName": "sql.execute",
                        "guCost": 1,
                        "label": "run query",
                    }
                },
            },
            {
                "eventType": "ExecutionUnitCompleted",
                "payload": {"prompt": "SHOULD NOT APPEAR", "output": "SECRET"},
            },
            {"eventType": "Completed", "payload": {}},
        ]
        contrib = build_contribution_from_events(
            events=events,
            org_id=42,
            agent_id="finance-agent",
            agent_name="Finance",
            trust_score=96,
            telemetry_opt_in=True,
        )
        blob = json.dumps(contrib)
        self.assertNotIn("SHOULD NOT APPEAR", blob)
        self.assertNotIn("SECRET", blob)
        self.assertNotIn("session_abc", blob)
        self.assertTrue(contrib["spec"]["tenantHash"].startswith("th_"))
        self.assertTrue(contrib["spec"]["sessionHash"].startswith("sh_"))
        self.assertEqual(contrib["spec"]["nodes"][0]["agentClass"], "finance")
        self.assertEqual(contrib["spec"]["nodes"][0]["capabilityFamily"], "database.query")
        self.assertEqual(contrib["spec"]["nodes"][0]["decision"], "ask")
        self.assertTrue(contrib["spec"]["nodes"][0]["humanApproval"])
        self.assertEqual(contrib["kind"], "GovernanceTelemetryContribution")

    def test_opt_out_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_contribution_from_events(
                events=[],
                org_id=1,
                telemetry_opt_in=False,
            )


class TestTelemetryCloudApi(unittest.TestCase):
    """Hit running API if available; otherwise skip."""

    def test_consent_and_contribute_roundtrip(self) -> None:
        try:
            import urllib.request
        except Exception:
            self.skipTest("urllib missing")

        base = os.environ.get("UAP_CLOUD_URL", "http://127.0.0.1:8000").rstrip("/")
        key = os.environ.get("UAP_CLOUD_KEY", "uap_live_dev_local_key_change_in_prod")

        def _req(method: str, path: str, body: dict | None = None) -> dict:
            data = None if body is None else json.dumps(body).encode("utf-8")
            r = urllib.request.Request(
                f"{base}{path}",
                data=data,
                method=method,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(r, timeout=5) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                self.skipTest(f"cloud not reachable: {e}")

        # health
        try:
            with urllib.request.urlopen(f"{base}/v1/health", timeout=3) as resp:
                if resp.status != 200:
                    self.skipTest("cloud unhealthy")
        except Exception as e:
            self.skipTest(f"cloud not up: {e}")

        consent = _req(
            "POST",
            "/v1/telemetry/consent",
            {"telemetryOptIn": True, "trainOptIn": False},
        )
        self.assertTrue(consent.get("telemetryOptIn"))

        events = [
            {
                "eventType": "ExecutionUnitStarted",
                "sessionId": "session_test",
                "payload": {
                    "executionUnit": {
                        "unitId": "eu_t1",
                        "unitKind": "tool",
                        "toolName": "browser.open",
                        "guCost": 2,
                    }
                },
            },
            {"eventType": "Completed", "payload": {}},
        ]
        out = _req(
            "POST",
            "/v1/telemetry/contribute",
            {
                "events": events,
                "agentId": "browser-agent",
                "agentName": "Browser Bot",
                "trustScore": 88,
            },
        )
        self.assertTrue(out.get("ok"))
        self.assertGreaterEqual(out.get("nodeCount", 0), 1)

        try:
            r = urllib.request.Request(
                f"{base}/v1/telemetry/aggregate?k=1",
                headers={"Authorization": f"Bearer {key}"},
            )
            with urllib.request.urlopen(r, timeout=5) as resp:
                agg = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            self.skipTest(str(e))
        self.assertTrue(agg.get("ok"))
        self.assertIsInstance(agg.get("rows"), list)


if __name__ == "__main__":
    unittest.main()
