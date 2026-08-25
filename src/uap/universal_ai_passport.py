"""Universal AI Passport (consumer) — NGS-0023 Verified / Unverified / Blocked."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .kill import KillStore

# Platform-verified provider seeds (v0 stubs)
VERIFIED_PROVIDERS: dict[str, dict[str, Any]] = {
    "chatgpt": {"name": "ChatGPT", "vendor": "OpenAI", "status": "verified"},
    "openai": {"name": "OpenAI", "vendor": "OpenAI", "status": "verified"},
    "claude": {"name": "Claude", "vendor": "Anthropic", "status": "verified"},
    "anthropic": {"name": "Anthropic", "vendor": "Anthropic", "status": "verified"},
    "gemini": {"name": "Gemini", "vendor": "Google", "status": "verified"},
    "google": {"name": "Google AI", "vendor": "Google", "status": "verified"},
    "deepseek": {"name": "DeepSeek", "vendor": "DeepSeek", "status": "verified"},
    "copilot": {"name": "Copilot", "vendor": "Microsoft", "status": "verified"},
}


class UniversalAIPassport:
    """Consumer passport status for gateway / extension badges."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def resolve(
        self,
        *,
        provider: str | None = None,
        agent_hint: str | None = None,
    ) -> dict[str, Any]:
        key = (provider or "").strip().lower()
        hint = (agent_hint or "").strip()

        # Blocked via kill store
        if hint:
            ks = KillStore(self.workspace)
            if ks.is_agent_killed(hint):
                return {
                    "passportStatus": "blocked",
                    "band": "dangerous",
                    "displayName": hint,
                    "reason": "agent has active kill token",
                    "standard": "NGS-0023",
                }

        if key in VERIFIED_PROVIDERS:
            meta = VERIFIED_PROVIDERS[key]
            return {
                "passportStatus": "verified",
                "band": "trusted",
                "displayName": meta["name"],
                "vendor": meta["vendor"],
                "providerId": key,
                "standard": "NGS-0023",
            }

        if hint and hint.lower() in VERIFIED_PROVIDERS:
            meta = VERIFIED_PROVIDERS[hint.lower()]
            return {
                "passportStatus": "verified",
                "band": "trusted",
                "displayName": meta["name"],
                "vendor": meta["vendor"],
                "providerId": hint.lower(),
                "standard": "NGS-0023",
            }

        return {
            "passportStatus": "unverified",
            "band": "caution",
            "displayName": hint or provider or "Unknown AI",
            "reason": "no platform-attested passport",
            "standard": "NGS-0023",
        }
