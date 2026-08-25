"""AI Gateway — NGS-0021 citizen interaction check."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .capability_gov import CapabilityGovernor, MODE_RANK
from .citizen_profile import passport_document, resolve_capability
from .citizen_registry import CitizenRegistry
from .collective import CollectiveDefense
from .council import GuardianConstitution
from .cti_hub import CTIHub
from .reputation import ReputationStore
from .universal_ai_passport import UniversalAIPassport


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


KNOWN_PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "chatgpt",
        "name": "ChatGPT",
        "origins": ["https://chatgpt.com/*", "https://chat.openai.com/*"],
    },
    {
        "id": "claude",
        "name": "Claude",
        "origins": ["https://claude.ai/*"],
    },
    {
        "id": "gemini",
        "name": "Gemini",
        "origins": ["https://gemini.google.com/*"],
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "origins": ["https://chat.deepseek.com/*"],
    },
    {
        "id": "copilot",
        "name": "Copilot",
        "origins": ["https://copilot.microsoft.com/*"],
    },
]


def _worse(a: str, b: str) -> str:
    order = {"allow": 0, "warn": 1, "ask": 2, "deny": 3}
    return a if order.get(a, 0) >= order.get(b, 0) else b


def _mode_to_decision(mode: str) -> str:
    m = mode.lower()
    if m == "allow":
        return "allow"
    if m in {"ask", "multisig", "restricted", "sandbox", "whitelist"}:
        return "ask" if m in {"ask", "multisig"} else ("warn" if m == "sandbox" else "ask")
    return "deny"


class AIGateway:
    """Compose Guardian layers into a single citizen check."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def providers(self) -> list[dict[str, Any]]:
        return list(KNOWN_PROVIDERS)

    def check(
        self,
        *,
        provider: str | None = None,
        url: str | None = None,
        action: str = "message.send",
        text: str | None = None,
        agent_hint: str | None = None,
        capability: str | None = None,
        approval_token: str | None = None,
        device_id: str | None = None,
        profile: str = "citizen",
    ) -> dict[str, Any]:
        reasons: list[str] = []
        decision = "allow"
        band = "trusted"

        # 1) Universal AI Passport
        passport = UniversalAIPassport(self.workspace).resolve(
            provider=provider, agent_hint=agent_hint
        )
        passport_status = passport["passportStatus"]
        band = passport.get("band") or band
        if passport_status == "blocked":
            decision = "deny"
            reasons.append(passport.get("reason") or "passport blocked")
        elif passport_status == "unverified":
            band = "caution"
            reasons.append("passport unverified — caution")

        # 2) Constitution (install default if missing)
        try:
            const = GuardianConstitution(self.workspace)
            try:
                const.load()
            except FileNotFoundError:
                const.install_default()
            # Map dangerous text to constitutional actions when obvious
            probe_action = "content.generate"
            low = (text or "").lower()
            if re.search(r"\b(kill|harm|weapon)\b.{0,40}\b(human|people)\b", low):
                probe_action = "harm.human"
            ce = const.evaluate(action=probe_action, agent_id=agent_hint or "citizen")
            if ce.get("decision") == "deny":
                decision = "deny"
                band = "dangerous"
                reasons.extend(ce.get("reasons") or ["constitution deny"])
        except Exception as e:
            reasons.append(f"constitution skip: {e}")

        # 3) Reputation (if agent hint)
        if agent_hint:
            try:
                rep = ReputationStore(self.workspace).get(agent_hint)
                rband = str(rep.get("band") or "medium")
                if rband == "critical":
                    decision = "deny"
                    band = "dangerous"
                    reasons.append("reputation critical")
                elif rband == "low":
                    decision = _worse(decision, "ask")
                    band = "caution" if band == "trusted" else band
                    reasons.append("reputation low → ask")
            except Exception:
                pass

        # 4) Collective / CTI pattern match on text
        if text:
            try:
                cd = CollectiveDefense(self.workspace)
                # soft opt-in for citizen gateway matching local inbox/outbox
                hits = cd.match(patterns=None)  # all local
                low = text.lower()
                for h in hits:
                    for p in h.get("patterns") or []:
                        if str(p).lower() in low:
                            decision = "deny"
                            band = "dangerous"
                            reasons.append(f"collective hit: {p}")
                            break
                # CTI hub feed patterns
                for sig in CTIHub(self.workspace).feed_list(limit=100):
                    for p in sig.get("patterns") or []:
                        if str(p).lower() in low:
                            decision = "deny"
                            band = "dangerous"
                            reasons.append(f"cti hit: {p}")
                            break
            except Exception as e:
                reasons.append(f"cti skip: {e}")

        # 5) Capability (citizen / family profile)
        cap = resolve_capability(action=action, capability=capability, text=text)
        if passport_status == "unverified" and cap in {
            "payment",
            "wallet",
            "trade",
            "contract",
            "create.agent",
            "device",
        }:
            decision = "deny"
            reasons.append(f"unverified + dangerous capability {cap}")

        gov = CapabilityGovernor(self.workspace).evaluate(
            capability=cap,
            agent_id=agent_hint or "citizen",
            document=passport_document(profile),
            profile="guardian",
        )
        mode = str(gov.get("decision") or "deny")
        cap_decision = _mode_to_decision(mode)
        if mode == "deny":
            decision = "deny"
            reasons.extend(gov.get("reasons") or [f"capability {cap} deny"])
        elif cap_decision == "ask":
            decision = _worse(decision, "ask")
            reasons.extend(gov.get("reasons") or [f"capability {cap} ask"])
        elif MODE_RANK.get(mode, 0) >= MODE_RANK.get("sandbox", 0) and mode != "allow":
            decision = _worse(decision, "warn")
            reasons.append(f"capability mode={mode}")

        approval_required = decision == "ask"
        if decision == "ask" and approval_token:
            reg = CitizenRegistry(self.workspace)
            if reg.consume_approval(approval_token, capability=cap):
                decision = "allow"
                approval_required = False
                reasons.append("approval token accepted")
            else:
                decision = "deny"
                reasons.append("invalid or expired approval token")

        # Heuristic: payment-like text always at least ask/deny under citizen
        if text and re.search(
            r"wire\s+money|send\s+\$|transfer\s+funds|bank\s+transfer", text, re.I
        ):
            if decision == "allow":
                decision = "deny"
                reasons.append("payment heuristic deny (citizen)")
                band = "dangerous"

        out = {
            "ok": True,
            "decision": decision,
            "band": band,
            "reasons": reasons,
            "passportStatus": passport_status,
            "passport": passport,
            "approvalRequired": approval_required,
            "capability": cap,
            "capabilityMode": mode,
            "provider": provider,
            "url": url,
            "action": action,
            "profile": profile,
            "checkedAt": _now(),
            "standard": "NGS-0021",
        }

        # Audit
        try:
            CitizenRegistry(self.workspace).audit(
                {
                    "deviceId": device_id,
                    "decision": decision,
                    "capability": cap,
                    "provider": provider,
                    "band": band,
                    "passportStatus": passport_status,
                }
            )
        except Exception:
            pass
        return out

    def citizen_cti_feed(self, *, limit: int = 50, since: str | None = None) -> dict[str, Any]:
        """Privacy-preserving feed for extension sync."""
        items = []
        for sig in CTIHub(self.workspace).feed_list(limit=limit * 2):
            if since and str(sig.get("hubReceivedAt") or "") <= since:
                continue
            items.append(
                {
                    "signatureId": sig.get("signatureId"),
                    "patterns": sig.get("patterns") or [],
                    "patternHash": sig.get("patternHash"),
                    "riskBand": sig.get("riskBand"),
                    "receivedAt": sig.get("hubReceivedAt"),
                }
            )
            if len(items) >= limit:
                break
        return {"ok": True, "feed": items, "standard": "NGS-0020-citizen", "count": len(items)}
