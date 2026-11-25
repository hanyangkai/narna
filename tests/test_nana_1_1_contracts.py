"""Static contracts for Nana AI 1.1. No secrets, no network."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IOS = REPO / "apps" / "mobile-ios" / "NARNA" / "NARNA"
WORKER = REPO / "services" / "free-pool-worker"
AGENT = REPO / "services" / "agent-proxy"


class PrivacyAndBrandingTests(unittest.TestCase):
    def test_privacy_manifest_present(self) -> None:
        manifest = (IOS / "PrivacyInfo.xcprivacy").read_text(encoding="utf-8")
        self.assertIn("NSPrivacyCollectedDataTypeDeviceID", manifest)
        self.assertIn("NSPrivacyAccessedAPICategoryUserDefaults", manifest)
        self.assertIn("CA92.1", manifest)

    def test_display_name_is_nana_ai(self) -> None:
        plist = (IOS / "Info.plist").read_text(encoding="utf-8")
        self.assertIn("<string>Nana AI</string>", plist)
        self.assertNotIn("NaNa Bot", plist)

    def test_no_external_ask_chatgpt_gemini_buttons(self) -> None:
        paths = list(IOS.rglob("*.swift"))
        joined = "\n".join(p.read_text(encoding="utf-8") for p in paths)
        self.assertNotIn("ExternalAskLinks", joined)
        self.assertNotIn("Ask ChatGPT", joined)
        self.assertNotIn("Ask Gemini", joined)


class FreePoolAndAgentTests(unittest.TestCase):
    def test_daily_limit_default_is_100(self) -> None:
        toml = (WORKER / "wrangler.toml").read_text(encoding="utf-8")
        router = (WORKER / "src" / "router.js").read_text(encoding="utf-8")
        self.assertIn('DAILY_LIMIT = "100"', toml)
        self.assertIn('|| "100"', router)

    def test_worker_does_not_log_message_content(self) -> None:
        src = (WORKER / "src" / "index.js").read_text(encoding="utf-8").lower()
        self.assertTrue("content" in src or "body" in src)
        # No console.log of the user prompt field.
        for line in src.splitlines():
            if "console.log" in line or "console.info" in line:
                self.assertNotIn("messages", line)
                self.assertNotIn("prompt", line)

    def test_storekit_product_ids_and_caps(self) -> None:
        store = (IOS / "NanaAgent.storekit").read_text(encoding="utf-8")
        self.assertIn("nana.agent.basic.monthly", store)
        self.assertIn("nana.agent.pro.monthly", store)
        plans = (IOS / "Services" / "AgentPlanConfig.swift").read_text(encoding="utf-8")
        self.assertIn("return 200", plans)
        self.assertIn("return 800", plans)
        cfg = (AGENT / "src" / "config.js").read_text(encoding="utf-8")
        self.assertIn("nana.agent.basic.monthly", cfg)
        self.assertIn("credits: 200", cfg)
        self.assertIn("credits: 800", cfg)

    def test_agent_proxy_refuses_to_deploy_from_npm(self) -> None:
        pkg = json.loads((AGENT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("Do not deploy", pkg["scripts"]["deploy"])

    def test_release_uses_production_app_attest(self) -> None:
        ent = (IOS / "NARNA-Release.entitlements").read_text(encoding="utf-8")
        self.assertIn("production", ent)
        debug = (IOS / "NARNA.entitlements").read_text(encoding="utf-8")
        self.assertIn("development", debug)


if __name__ == "__main__":
    unittest.main()
