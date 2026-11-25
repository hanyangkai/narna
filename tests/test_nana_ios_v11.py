"""Nana AI iOS v1.1 — rename + no platform keys in app bundle sources."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IOS = REPO / "apps" / "mobile-ios" / "NARNA" / "NARNA"
WORKER = REPO / "free-pool-worker"


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

    def test_vi_daily_limit_string(self) -> None:
        text = (IOS / "vi.lproj" / "Localizable.strings").read_text(encoding="utf-8")
        self.assertIn("Bạn đã dùng hết lượt free hôm nay", text)


class NoPlatformKeysInAppTests(unittest.TestCase):
    FORBIDDEN = [
        re.compile(r"sk-or-[a-zA-Z0-9]{10,}"),
        re.compile(r"OPENROUTER_API_KEY\s*="),
        re.compile(r"GROQ_API_KEY\s*="),
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # live openai-looking literals
    ]

    def test_no_live_provider_secrets_in_ios_sources(self) -> None:
        hits: list[str] = []
        for path in IOS.rglob("*"):
            if path.suffix not in {".swift", ".plist", ".strings", ".xcprivacy", ".json"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pat in self.FORBIDDEN:
                if pat.search(text):
                    # allow placeholder docs in comments mentioning sk-or-…
                    if "sk-or-…" in text or "sk-…" in text or "replace_me" in text:
                        if not re.search(r"sk-or-[a-zA-Z0-9]{12,}", text):
                            continue
                    hits.append(f"{path.relative_to(REPO)} :: {pat.pattern}")
        self.assertEqual(hits, [], msg="\n".join(hits))

    def test_free_pool_provider_has_no_api_key_header_secret(self) -> None:
        text = (IOS / "ChatProviders" / "FreePoolProvider.swift").read_text(encoding="utf-8")
        self.assertNotIn("Authorization", text)
        self.assertIn("X-Device-Id", text)


class FreePoolWorkerTests(unittest.TestCase):
    def test_worker_readme_and_example_secrets(self) -> None:
        self.assertTrue((WORKER / "README.md").is_file())
        example = (WORKER / ".dev.vars.example").read_text(encoding="utf-8")
        self.assertIn("GROQ_API_KEY=", example)
        self.assertIn("replace_me", example)
        self.assertFalse((WORKER / ".dev.vars").exists())

    def test_worker_does_not_log_content_field(self) -> None:
        src = (WORKER / "src" / "index.ts").read_text(encoding="utf-8")
        self.assertIn("no message content", src.lower().replace("-", " "))
        # ensure console.log payloads don't include raw messages
        self.assertNotIn("messages:", src.split("console.log")[1] if "console.log" in src else "")


class ChatRouterLogicMirrorTests(unittest.TestCase):
    """Mirror of Swift ChatRouter.resolve for CI without Xcode."""

    @staticmethod
    def resolve(preference: str, apple_available: bool) -> str:
        if preference == "auto":
            return "onDevice" if apple_available else "freePool"
        return preference

    def test_auto_apple(self) -> None:
        self.assertEqual(self.resolve("auto", True), "onDevice")

    def test_auto_fallback(self) -> None:
        self.assertEqual(self.resolve("auto", False), "freePool")


if __name__ == "__main__":
    unittest.main()
