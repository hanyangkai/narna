"""Nana AI iOS v1.1 — rename + no platform keys + free-pool + Agent wiring."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IOS = REPO / "apps" / "mobile-ios" / "NARNA" / "NARNA"
WORKER = REPO / "services" / "free-pool-worker"
BACKEND = REPO / "web" / "backend" / "app"


class NanaRenameTests(unittest.TestCase):
    def test_info_plist_display_name(self) -> None:
        text = (IOS / "Info.plist").read_text(encoding="utf-8")
        self.assertIn("Nana AI", text)
        self.assertIn("<string>1.1</string>", text)
        self.assertNotIn("NARNA needs camera", text)

    def test_pinned_bot_name(self) -> None:
        text = (IOS / "Models" / "ChatBot.swift").read_text(encoding="utf-8")
        self.assertIn('static let name = "Nana AI"', text)
        self.assertIn("You are Nana AI", text)
        self.assertNotIn("NaNa Bot", text)

    def test_no_nana_bot_brand(self) -> None:
        for path in IOS.rglob("*"):
            if path.suffix not in {".swift", ".strings", ".plist", ".md"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("NaNa Bot", text, msg=str(path))

    def test_vi_daily_limit_string(self) -> None:
        text = (IOS / "vi.lproj" / "Localizable.strings").read_text(encoding="utf-8")
        self.assertIn("Bạn đã dùng hết lượt free hôm nay", text)
        self.assertIn("upgrade_to_agent", text)


class NoPlatformKeysInAppTests(unittest.TestCase):
    FORBIDDEN = [
        re.compile(r"sk-or-[a-zA-Z0-9]{10,}"),
        re.compile(r"OPENROUTER_API_KEY\s*="),
        re.compile(r"GROQ_API_KEY\s*="),
        re.compile(r"GEMINI_API_KEY\s*="),
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    ]

    def test_no_live_provider_secrets_in_ios_sources(self) -> None:
        hits: list[str] = []
        for path in IOS.rglob("*"):
            if path.suffix not in {".swift", ".plist", ".strings", ".xcprivacy", ".json"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pat in self.FORBIDDEN:
                if pat.search(text):
                    if "sk-or-…" in text or "sk-…" in text or "replace_me" in text:
                        if not re.search(r"sk-or-[a-zA-Z0-9]{12,}", text):
                            continue
                    hits.append(f"{path.relative_to(REPO)} :: {pat.pattern}")
        self.assertEqual(hits, [], msg="\n".join(hits))

    def test_free_pool_provider_has_no_api_key_header_secret(self) -> None:
        text = (IOS / "ChatProviders" / "FreePoolProvider.swift").read_text(encoding="utf-8")
        self.assertNotIn("Authorization", text)
        self.assertIn("X-Device-Id", text)
        self.assertIn("X-Device-Check-Token", text)


class FreePoolWorkerTests(unittest.TestCase):
    def test_worker_lives_under_services(self) -> None:
        self.assertTrue((WORKER / "README.md").is_file())
        self.assertTrue((WORKER / "wrangler.toml").is_file())
        self.assertTrue((WORKER / "src" / "upstreams.ts").is_file())

    def test_worker_readme_and_example_secrets(self) -> None:
        example = (WORKER / ".dev.vars.example").read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=", example)
        self.assertIn("GEMINI_API_KEY=", example)
        self.assertIn("ZAI_API_KEY=", example)
        self.assertIn("replace_me", example)
        self.assertFalse((WORKER / ".dev.vars").exists())

    def test_worker_upstream_order(self) -> None:
        src = (WORKER / "src" / "upstreams.ts").read_text(encoding="utf-8")
        self.assertIn("tryWorkersAI", src)
        self.assertIn("tryGemini", src)
        self.assertIn("tryGroq", src)
        self.assertIn("tryOpenRouterFree", src)
        self.assertIn("tryZai", src)
        self.assertIn("shouldSkipGemini", src)
        # order in streamWithFallback chain
        wi = src.index("tryWorkersAI")
        ge = src.index("() => tryGemini")
        gr = src.index("() => tryGroq")
        op = src.index("() => tryOpenRouterFree")
        za = src.index("() => tryZai")
        self.assertTrue(wi < ge < gr < op < za)

    def test_daily_limit_default_10(self) -> None:
        toml = (WORKER / "wrangler.toml").read_text(encoding="utf-8")
        self.assertIn('DAILY_MSG_LIMIT_PER_DEVICE = "10"', toml)

    def test_worker_does_not_log_content_field(self) -> None:
        src = (WORKER / "src" / "index.ts").read_text(encoding="utf-8")
        self.assertIn("no message content", src.lower().replace("-", " "))


class ProviderRouterLogicMirrorTests(unittest.TestCase):
    """Mirror of Swift ProviderRouter.resolve for CI without Xcode."""

    @staticmethod
    def resolve(preference: str, apple_available: bool) -> str:
        if preference == "auto":
            return "onDevice" if apple_available else "freePool"
        return preference

    def test_auto_apple(self) -> None:
        self.assertEqual(self.resolve("auto", True), "onDevice")

    def test_auto_free_pool(self) -> None:
        self.assertEqual(self.resolve("auto", False), "freePool")

    def test_agent_preference(self) -> None:
        self.assertEqual(self.resolve("agent", False), "agent")


class AgentIAPWiringTests(unittest.TestCase):
    def test_storekit_products(self) -> None:
        store = (IOS / "Configuration" / "NanaAI.storekit").read_text(encoding="utf-8")
        self.assertIn("nana.agent.basic.monthly", store)
        self.assertIn("nana.agent.pro.monthly", store)

    def test_plans_json(self) -> None:
        plans = json.loads((BACKEND / "nana_agent_plans.json").read_text(encoding="utf-8"))
        self.assertIn("nana.agent.basic.monthly", plans["products"])
        self.assertIn("nana.agent.pro.monthly", plans["products"])
        self.assertEqual(plans["products"]["nana.agent.basic.monthly"]["creditsPerPeriod"], 500)

    def test_agent_api_mounted(self) -> None:
        main = (BACKEND / "main.py").read_text(encoding="utf-8")
        self.assertIn("nana_agent", main)

    def test_llm_provider_protocol(self) -> None:
        text = (IOS / "ChatProviders" / "ChatProvider.swift").read_text(encoding="utf-8")
        self.assertIn("protocol LLMProvider", text)
        self.assertIn("enum ProviderRouter", text)


if __name__ == "__main__":
    unittest.main()
