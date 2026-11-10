"""Onboarding: external AI (BYOK / Claude·ChatGPT sub) OR NARNA Pro subscription.

MausBot-style: model credentials live on desktop or org cloud config.
Mobile guides the user; IAP is Apple/Google only (no crypto in apps).
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db
from .models import MobileDevice, Organization

router = APIRouter()

# Pending pairing invites (desktop → phone). Push delivery later.
_PAIRING_INVITES: dict[str, dict[str, Any]] = {}

PROVIDERS = (
    {
        "id": "anthropic",
        "name": "Claude",
        "modes": ["subscription_cli", "api_key"],
        "hint": "Sign in Claude Code / Claude CLI on desktop, or paste Anthropic API key for cloud.",
        "env": "ANTHROPIC_API_KEY",
    },
    {
        "id": "openai",
        "name": "ChatGPT / OpenAI",
        "modes": ["subscription_cli", "api_key"],
        "hint": "Sign in Codex / ChatGPT CLI on desktop, or paste OpenAI API key for cloud.",
        "env": "OPENAI_API_KEY",
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "modes": ["api_key"],
        "hint": "Paste OpenRouter key to route many models via cloud agent.",
        "env": "OPENROUTER_API_KEY",
    },
    {
        "id": "google",
        "name": "Gemini",
        "modes": ["api_key"],
        "hint": "Paste Google AI Studio / Gemini API key.",
        "env": "GOOGLE_API_KEY",
    },
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _auth_device(mobile_token: str, db: Session) -> tuple[MobileDevice, Organization]:
    if not mobile_token:
        raise HTTPException(status_code=401, detail="missing mobile token")
    device = db.query(MobileDevice).filter(MobileDevice.mobile_token == mobile_token).first()
    if not device:
        raise HTTPException(status_code=401, detail="Invalid or expired mobile token")
    if device.expires_at and _now() > device.expires_at:
        raise HTTPException(status_code=401, detail="Mobile token expired")
    org = db.query(Organization).filter(Organization.id == device.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return device, org


def _mask(key: str | None) -> str | None:
    if not key:
        return None
    k = key.strip()
    if len(k) <= 8:
        return "••••"
    return f"{k[:4]}…{k[-4:]}"


def _llm_cfg(org: Organization) -> dict[str, Any]:
    raw = getattr(org, "llm_config_json", None)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _provider_connected(cfg: dict[str, Any], provider_id: str) -> bool:
    p = str(cfg.get("provider") or "").lower()
    key = str(cfg.get("apiKey") or cfg.get("api_key") or "").strip()
    keys = cfg.get("keys") if isinstance(cfg.get("keys"), dict) else {}
    if provider_id == p and key:
        return True
    return bool(str(keys.get(provider_id) or "").strip())


# ── Models ──


class ProviderConfigureRequest(BaseModel):
    api_key: str = Field(..., min_length=8)
    set_as_default: bool = True
    model: str | None = None


class StoreVerifyRequest(BaseModel):
    platform: str  # ios | android
    product_id: str
    transaction_id: str
    receipt_data: str | None = None
    purchase_token: str | None = None


class PairingInviteRequest(BaseModel):
    pairing_code: str
    org_name: str | None = None
    device_hint: str | None = None
    expires_in_sec: int = 300


# ── Onboarding status ──


@router.get("/v1/mobile/onboarding/status")
def onboarding_status(mobile_token: str | None = None, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Dual path: external AI (BYOK/sub) vs NARNA Pro subscription."""
    paired = False
    plan = "free"
    org_id = None
    cfg: dict[str, Any] = {}
    ai_ready = False

    if mobile_token:
        try:
            _device, org = _auth_device(mobile_token, db)
            paired = True
            plan = (org.plan or "free").lower()
            if plan == "pro":
                plan = "cloud"
            org_id = org.id
            cfg = _llm_cfg(org)
            ai_ready = bool(
                _provider_connected(cfg, "anthropic")
                or _provider_connected(cfg, "openai")
                or _provider_connected(cfg, "openrouter")
                or _provider_connected(cfg, "google")
                or str(cfg.get("apiKey") or "").strip()
            )
        except HTTPException:
            paired = False

    providers = []
    for p in PROVIDERS:
        connected = _provider_connected(cfg, p["id"]) if paired else False
        providers.append({**p, "connected": connected, "masked_key": None})

    if paired and cfg.get("apiKey"):
        # reflect default provider mask
        for row in providers:
            if row["id"] == str(cfg.get("provider") or "").lower() or (
                not cfg.get("provider") and row["id"] in ("openrouter", "openai", "anthropic")
            ):
                if _provider_connected(cfg, row["id"]) or cfg.get("apiKey"):
                    row["masked_key"] = _mask(str(cfg.get("apiKey")))
                    row["connected"] = True
                    break

    return {
        "ok": True,
        "paired": paired,
        "plan": plan,
        "org_id": org_id,
        "ai_ready": ai_ready,
        "needs_onboarding": (not paired) or (paired and not ai_ready and plan == "free"),
        "paths": [
            {
                "id": "external_ai",
                "title": "Dùng AI của bạn (Claude / ChatGPT)",
                "subtitle": "Giống MausBot — dùng subscription hoặc API key của bạn",
                "recommended": True,
                "steps": [
                    "Cài NARNA Desktop (Mac/Windows) hoặc mở cloud agent",
                    "Đăng nhập Claude CLI / Codex (ChatGPT) — dùng gói Pro bạn đã mua",
                    "Hoặc dán API key Anthropic / OpenAI / OpenRouter trong Settings",
                    "Trên Desktop bấm Pair → quét QR bằng app điện thoại",
                    "Chat & duyệt lệnh trên phone; token model trừ vào tài khoản AI của bạn",
                ],
                "cta": "Kết nối AI ngoài",
            },
            {
                "id": "narna_pro",
                "title": "Mua NARNA Pro",
                "subtitle": "Cloud agent always-on, inbox, routines, voice, sync — thanh toán App Store / Play",
                "recommended": False,
                "steps": [
                    "Mua Pro trong app (Apple / Google) — không dùng crypto trên mobile",
                    "Gắn API key Claude/OpenAI vào cloud (Settings → AI Providers) để agent chạy khi máy tắt",
                    "Hoặc vẫn pair Desktop nếu bạn dùng CLI subscription",
                    "Pro mở cloud features; phí model vẫn do bạn trả provider (BYOK)",
                ],
                "cta": "Xem gói NARNA",
                "products": [
                    {"product_id": "narna_pro_monthly", "plan": "cloud", "price": "$19.99", "period": "month"},
                    {"product_id": "narna_pro_yearly", "plan": "cloud", "price": "$159.99", "period": "year"},
                    {"product_id": "narna_team_seat_monthly", "plan": "team", "price": "$99.99", "period": "seat/month"},
                ],
            },
        ],
        "providers": providers,
        "pairing": {
            "how": "Desktop tạo mã 6 số / QR → app quét. Có thể gửi invite push khi desktop mở pairing.",
            "desktop_command": "narna desktop  # rồi mở Pairing",
        },
        "billing_policy": {
            "mobile": "app_store_or_play_only",
            "web": "usdc_usdt",
            "model_tokens": "byok_user_pays_provider",
        },
    }


@router.get("/v1/mobile/ai/providers")
def list_ai_providers(mobile_token: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    _device, org = _auth_device(mobile_token, db)
    cfg = _llm_cfg(org)
    rows = []
    for p in PROVIDERS:
        connected = _provider_connected(cfg, p["id"])
        masked = None
        keys = cfg.get("keys") if isinstance(cfg.get("keys"), dict) else {}
        if connected:
            masked = _mask(str(keys.get(p["id"]) or cfg.get("apiKey") or ""))
        rows.append({**p, "connected": connected, "masked_key": masked})
    return {
        "ok": True,
        "default_provider": cfg.get("provider"),
        "providers": rows,
        "note": "CLI subscription logins stay on Desktop. API keys may be stored on org for cloud agent.",
    }


@router.post("/v1/mobile/ai/providers/{provider_id}/configure")
def configure_ai_provider(
    provider_id: str,
    body: ProviderConfigureRequest,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Save BYOK API key on org for cloud agent (not for leaking to client logs)."""
    _device, org = _auth_device(mobile_token, db)
    provider_id = provider_id.lower().strip()
    if provider_id not in {p["id"] for p in PROVIDERS}:
        raise HTTPException(status_code=404, detail="Unknown provider")

    cfg = _llm_cfg(org)
    keys = cfg.get("keys") if isinstance(cfg.get("keys"), dict) else {}
    keys[provider_id] = body.api_key.strip()
    cfg["keys"] = keys
    if body.set_as_default:
        # Cloud ModelRouter supports openrouter|openai|ollama|mock.
        # Claude subscription → Desktop CLI (pair phone). Anthropic API key → prefer OpenRouter Claude routes or Desktop.
        if provider_id == "openai":
            cfg["provider"] = "openai"
            cfg["apiKey"] = body.api_key.strip()
        elif provider_id in {"openrouter", "anthropic", "google"}:
            cfg["provider"] = "openrouter"
            cfg["apiKey"] = body.api_key.strip()
        else:
            cfg["provider"] = "openrouter"
            cfg["apiKey"] = body.api_key.strip()
        if body.model:
            cfg["modelReason"] = body.model
            cfg["modelCheap"] = body.model

    org.llm_config_json = json.dumps(cfg)
    db.add(org)
    db.commit()

    return {
        "ok": True,
        "provider": provider_id,
        "connected": True,
        "masked_key": _mask(body.api_key),
        "default_provider": cfg.get("provider"),
        "message": "Key saved for cloud agent. Desktop CLI logins are configured on the computer, not here.",
    }


@router.delete("/v1/mobile/ai/providers/{provider_id}")
def clear_ai_provider(
    provider_id: str,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _device, org = _auth_device(mobile_token, db)
    provider_id = provider_id.lower().strip()
    cfg = _llm_cfg(org)
    keys = cfg.get("keys") if isinstance(cfg.get("keys"), dict) else {}
    keys.pop(provider_id, None)
    cfg["keys"] = keys
    if str(cfg.get("provider") or "").lower() in {provider_id, "anthropic" if provider_id == "anthropic" else ""}:
        if not keys:
            cfg.pop("apiKey", None)
            cfg["provider"] = "mock"
        else:
            nxt = next(iter(keys))
            cfg["provider"] = nxt
            cfg["apiKey"] = keys[nxt]
    org.llm_config_json = json.dumps(cfg)
    db.add(org)
    db.commit()
    return {"ok": True, "provider": provider_id, "connected": False}


# ── Store subscription verify (IAP / Play) ──


@router.get("/v1/mobile/subscription/products")
def subscription_products() -> dict[str, Any]:
    return {
        "ok": True,
        "store_only": True,
        "crypto_in_app": False,
        "products": [
            {
                "product_id": "narna_pro_monthly",
                "plan": "cloud",
                "title": "NARNA Pro",
                "price": "$19.99",
                "period": "month",
                "includes": [
                    "Cloud agent always-on",
                    "Inbox · Routines · Voice · Push",
                    "Sync multi-device",
                    "Still BYOK for Claude/ChatGPT tokens",
                ],
            },
            {
                "product_id": "narna_pro_yearly",
                "plan": "cloud",
                "title": "NARNA Pro Annual",
                "price": "$159.99",
                "period": "year",
                "includes": ["Same as Pro monthly", "~2 months free"],
            },
            {
                "product_id": "narna_team_seat_monthly",
                "plan": "team",
                "title": "NARNA Team seat",
                "price": "$99.99",
                "period": "seat/month",
                "includes": ["Shared bots", "Org inbox", "Min 3 seats"],
            },
        ],
        "manage_urls": {
            "ios": "https://apps.apple.com/account/subscriptions",
            "android": "https://play.google.com/store/account/subscriptions",
        },
    }


@router.post("/v1/billing/store/verify")
def verify_store_purchase(
    body: StoreVerifyRequest,
    mobile_token: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Verify App Store / Play purchase and set org plan.

    Production must call Apple/Google APIs. This accepts signed-off product mapping
    after client completes StoreKit/Play Billing (no crypto).
    """
    _device, org = _auth_device(mobile_token, db)
    platform = body.platform.lower().strip()
    if platform not in {"ios", "android"}:
        raise HTTPException(status_code=422, detail="platform must be ios|android")

    product_map = {
        "narna_pro_monthly": ("cloud", 30),
        "narna_pro_yearly": ("cloud", 365),
        "narna_team_seat_monthly": ("team", 30),
    }
    mapped = product_map.get(body.product_id)
    if not mapped:
        raise HTTPException(status_code=404, detail="Unknown product_id")

    # TODO: real Apple App Store Server API / Google Play Developer API verify
    # For now require a non-empty transaction id from the store SDK.
    if not (body.transaction_id or "").strip():
        raise HTTPException(status_code=400, detail="transaction_id required from store SDK")
    if platform == "ios" and not (body.receipt_data or body.transaction_id):
        raise HTTPException(status_code=400, detail="iOS receipt/transaction required")
    if platform == "android" and not (body.purchase_token or body.transaction_id):
        raise HTTPException(status_code=400, detail="Android purchase_token/transaction required")

    plan, days = mapped
    org.plan = plan
    org.plan_expires_at = _now() + timedelta(days=days)
    if plan == "team" and (org.seat_count or 1) < 3:
        org.seat_count = 3
    db.add(org)
    db.commit()

    return {
        "ok": True,
        "plan": org.plan,
        "plan_expires_at": org.plan_expires_at.isoformat() if org.plan_expires_at else None,
        "product_id": body.product_id,
        "verified": True,
        "verification_mode": "transaction_accepted_pending_store_api_wiring",
        "message": "Subscription applied. Add real Apple/Google verify before production.",
    }


# ── Pairing invite (desktop notifies phone) ──


@router.post("/v1/mobile/pairing/invite")
def create_pairing_invite(body: PairingInviteRequest) -> dict[str, Any]:
    """Desktop calls this when opening pairing window (public + short-lived)."""
    code = body.pairing_code.strip()
    if len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=422, detail="pairing_code must be 6 digits")
    invite_id = secrets.token_urlsafe(12)
    expires = _now() + timedelta(seconds=max(60, min(body.expires_in_sec, 600)))
    _PAIRING_INVITES[invite_id] = {
        "invite_id": invite_id,
        "pairing_code": code,
        "org_name": body.org_name or "NARNA",
        "device_hint": body.device_hint,
        "expires_at": expires.isoformat(),
        "created_at": _now().isoformat(),
    }
    # Keep index by code for poll
    _PAIRING_INVITES[f"code:{code}"] = _PAIRING_INVITES[invite_id]
    return {
        "ok": True,
        "invite_id": invite_id,
        "expires_at": expires.isoformat(),
        "push": {
            "title": "NARNA Desktop sẵn sàng ghép nối",
            "body": f"Mở app NARNA và nhập mã {code} hoặc quét QR.",
            "status": "queued_local",
            "note": "Wire APNs/FCM to deliver this to registered devices.",
        },
    }


@router.get("/v1/mobile/pairing/invite/latest")
def latest_pairing_invite(code: str | None = None) -> dict[str, Any]:
    """Phone can poll for an open invite (optional; usually user scans QR)."""
    if code:
        row = _PAIRING_INVITES.get(f"code:{code.strip()}")
        if not row:
            raise HTTPException(status_code=404, detail="No invite for code")
        return {"ok": True, "invite": row}
    # return most recent non-code index
    invites = [v for k, v in _PAIRING_INVITES.items() if not str(k).startswith("code:")]
    if not invites:
        return {"ok": True, "invite": None}
    invites.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return {"ok": True, "invite": invites[0]}
