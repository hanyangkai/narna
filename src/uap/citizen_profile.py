"""Citizen Capability Profile — NGS-0022 default-deny for public users."""

from __future__ import annotations

from typing import Any


CITIZEN_GRANTS: list[dict[str, Any]] = [
    {"capability": "search", "mode": "allow"},
    {"capability": "read", "mode": "allow"},
    {"capability": "content", "mode": "allow"},
    {"capability": "email", "mode": "ask"},
    {"capability": "payment", "mode": "deny"},
    {"capability": "wallet", "mode": "deny"},
    {"capability": "trade", "mode": "deny"},
    {"capability": "contract", "mode": "deny"},
    {"capability": "create.agent", "mode": "deny"},
    {"capability": "spawn.agent", "mode": "deny"},
    {"capability": "device", "mode": "deny"},
    {"capability": "terminal", "mode": "deny"},
    {"capability": "mcp", "mode": "restricted"},
    {"capability": "code", "mode": "sandbox"},
]

FAMILY_GRANTS: list[dict[str, Any]] = [
    {"capability": "search", "mode": "allow"},
    {"capability": "read", "mode": "allow"},
    {"capability": "content", "mode": "allow"},
    {"capability": "email", "mode": "deny"},
    {"capability": "payment", "mode": "deny"},
    {"capability": "wallet", "mode": "deny"},
    {"capability": "trade", "mode": "deny"},
    {"capability": "contract", "mode": "deny"},
    {"capability": "create.agent", "mode": "deny"},
    {"capability": "device", "mode": "deny"},
    {"capability": "terminal", "mode": "deny"},
    {"capability": "mcp", "mode": "deny"},
    {"capability": "code", "mode": "deny"},
]

# Action / text hints → capability id
ACTION_CAPABILITY: dict[str, str] = {
    "message.send": "content",
    "chat.send": "content",
    "content.create": "content",
    "payment.send": "payment",
    "wallet.transfer": "wallet",
    "trade.execute": "trade",
    "contract.sign": "contract",
    "email.send": "email",
    "agent.create": "create.agent",
    "device.control": "device",
    "mcp.call": "mcp",
    "code.execute": "code",
}

DANGEROUS_TEXT_HINTS: list[tuple[str, str]] = [
    (r"wire\s+money|send\s+(?:\$|usd|btc|eth)|transfer\s+funds|bank\s+transfer", "payment"),
    (r"sign\s+(?:the\s+)?contract|execute\s+agreement", "contract"),
    (r"create\s+(?:a\s+)?(?:new\s+)?agent|spawn\s+agents?|self[- ]?replicat", "create.agent"),
    (r"control\s+(?:my\s+)?(?:phone|computer|device)|install\s+malware", "device"),
    (r"send\s+(?:an?\s+)?email\s+to|mail\s+this\s+to", "email"),
]


def passport_document(profile: str = "citizen") -> dict[str, Any]:
    grants = FAMILY_GRANTS if profile == "family" else CITIZEN_GRANTS
    return {
        "apiVersion": "narna.ai/v1alpha1",
        "kind": "CapabilityPassport",
        "metadata": {"agentId": f"profile:{profile}", "version": "0.1.0", "profile": profile},
        "spec": {
            "grants": grants,
            "quotas": {"maxSpawnDepth": 0, "maxApiCallsPerHour": 200, "maxGuPerDay": 1000},
            "isolation": {"network": "deny-by-default", "filesystem": "none"},
        },
    }


def resolve_capability(*, action: str | None, capability: str | None, text: str | None) -> str:
    if capability:
        return str(capability).strip().lower()
    # Dangerous text wins over generic chat actions
    if text:
        import re

        low = text.lower()
        for pattern, cap in DANGEROUS_TEXT_HINTS:
            if re.search(pattern, low, re.I):
                return cap
    act = str(action or "").strip().lower()
    if act in ACTION_CAPABILITY:
        return ACTION_CAPABILITY[act]
    return "content"
