"""Nana AI Agent Mode — StoreKit-gated proxy to paid models (keys server-side only)."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/nana", tags=["nana-agent"])

_PLANS_PATH = Path(__file__).with_name("nana_agent_plans.json")
# device_id -> entitlement state (replace with Redis/DB in prod)
_ENTITLEMENTS: dict[str, dict[str, Any]] = {}


def load_plans() -> dict[str, Any]:
    return json.loads(_PLANS_PATH.read_text(encoding="utf-8"))


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad)


def decode_storekit_jws_payload(jws: str) -> dict[str, Any]:
    """Decode JWS payload without full Apple cert chain (dev/mock).

    Production: set NANA_IAP_STRICT=1 and wire App Store Server API / JWS verification.
    """
    parts = (jws or "").strip().split(".")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="invalid_jws")
    try:
        payload = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"jws_decode_failed:{e}") from e
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="jws_payload_not_object")
    return payload


def verify_transaction(jws: str) -> dict[str, Any]:
    payload = decode_storekit_jws_payload(jws)
    product_id = str(
        payload.get("productId")
        or payload.get("product_id")
        or (payload.get("data") or {}).get("productId")
        or ""
    )
    expires = payload.get("expiresDate") or payload.get("expires_date")
    txn = str(payload.get("transactionId") or payload.get("transaction_id") or "")
    strict = (os.environ.get("NANA_IAP_STRICT") or "").strip() in {"1", "true", "yes"}
    if strict:
        # Placeholder for App Store Server API / x5c chain verification.
        # Reject obviously forged empty product ids in strict mode.
        if not product_id or not txn:
            raise HTTPException(status_code=401, detail="iap_verification_failed")
        if expires is not None:
            try:
                if int(expires) < int(time.time() * 1000):
                    raise HTTPException(status_code=401, detail="subscription_expired")
            except HTTPException:
                raise
            except Exception:
                pass
    plans = load_plans()["products"]
    if product_id and product_id not in plans:
        raise HTTPException(status_code=400, detail="unknown_product")
    return {
        "productId": product_id or "nana.agent.basic.monthly",
        "transactionId": txn or "mock",
        "expiresDate": expires,
        "payload": payload,
    }


class VerifyBody(BaseModel):
    deviceId: str = Field(min_length=8)
    signedTransaction: str = Field(min_length=10)


class AgentChatBody(BaseModel):
    deviceId: str = Field(min_length=8)
    messages: list[dict[str, str]]
    signedTransaction: str | None = None
    model: str | None = None


@router.get("/agent/products")
def agent_products() -> dict[str, Any]:
    plans = load_plans()
    return {
        "ok": True,
        "subscriptionGroup": plans.get("subscriptionGroup"),
        "products": [
            {
                "productId": pid,
                "displayName": meta.get("displayName"),
                "period": meta.get("period"),
                "creditsPerPeriod": meta.get("creditsPerPeriod"),
                "features": meta.get("features"),
                # Prices intentionally omitted — App Store Connect is SSOT
            }
            for pid, meta in (plans.get("products") or {}).items()
        ],
        "notes": plans.get("notes"),
    }


@router.post("/agent/verify")
def agent_verify(body: VerifyBody) -> dict[str, Any]:
    verified = verify_transaction(body.signedTransaction)
    product_id = verified["productId"]
    plans = load_plans()["products"]
    meta = plans.get(product_id) or plans["nana.agent.basic.monthly"]
    credits = int(meta.get("creditsPerPeriod") or 500)
    ent = {
        "productId": product_id,
        "creditsRemaining": credits,
        "creditsPerPeriod": credits,
        "transactionId": verified["transactionId"],
        "verifiedAt": int(time.time()),
        "features": meta.get("features") or [],
        "models": meta.get("models") or [],
    }
    _ENTITLEMENTS[body.deviceId] = ent
    return {"ok": True, "entitlement": {k: v for k, v in ent.items() if k != "models"}, "models": ent["models"]}


@router.get("/agent/entitlement")
def agent_entitlement(device_id: str, x_device_id: str | None = Header(default=None)) -> dict[str, Any]:
    did = (device_id or x_device_id or "").strip()
    ent = _ENTITLEMENTS.get(did)
    if not ent:
        return {"ok": True, "active": False, "creditsRemaining": 0}
    return {
        "ok": True,
        "active": True,
        "productId": ent["productId"],
        "creditsRemaining": ent["creditsRemaining"],
        "creditsPerPeriod": ent["creditsPerPeriod"],
        "features": ent.get("features") or [],
    }


def _openrouter_complete(messages: list[dict[str, str]], model: str, max_tokens: int) -> str:
    key = (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("UAP_OPENROUTER_API_KEY") or "").strip()
    if not key:
        # Deterministic offline stub for CI / local without keys
        last = messages[-1]["content"] if messages else ""
        return f"[agent-stub:{model}] {last[:400]}"
    body = {
        "model": model,
        "messages": [{"role": "system", "content": "You are Nana AI Agent. Complete multi-step tasks carefully."}]
        + messages,
        "max_tokens": max_tokens,
        "stream": False,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://narna.org",
            "X-Title": "Nana AI Agent",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        raise HTTPException(status_code=502, detail=f"upstream_{e.code}") from e
    choices = data.get("choices") or []
    if not choices:
        return "(empty)"
    return str((choices[0].get("message") or {}).get("content") or "")


@router.post("/agent/chat")
def agent_chat(body: AgentChatBody) -> dict[str, Any]:
    ent = _ENTITLEMENTS.get(body.deviceId)
    if body.signedTransaction:
        verified = verify_transaction(body.signedTransaction)
        if not ent or ent.get("transactionId") != verified.get("transactionId"):
            # refresh entitlement from this transaction
            agent_verify(VerifyBody(deviceId=body.deviceId, signedTransaction=body.signedTransaction))
            ent = _ENTITLEMENTS.get(body.deviceId)
    if not ent or int(ent.get("creditsRemaining") or 0) <= 0:
        raise HTTPException(status_code=402, detail="agent_paywall")

    plans = load_plans()["products"]
    meta = plans.get(ent["productId"]) or {}
    allowed = list(meta.get("models") or ent.get("models") or [])
    model = body.model or (allowed[0] if allowed else "openai/gpt-4o-mini")
    if allowed and model not in allowed:
        raise HTTPException(status_code=403, detail="model_not_in_plan")

    cost = min(int(meta.get("maxCreditsPerRequest") or 20), max(1, len(json.dumps(body.messages)) // 200 + 1))
    if ent["creditsRemaining"] < cost:
        raise HTTPException(status_code=402, detail="credits_exhausted")

    safe_msgs = [
        {"role": str(m.get("role") or "user")[:16], "content": str(m.get("content") or "")[:12000]}
        for m in body.messages[-30:]
    ]
    content = _openrouter_complete(safe_msgs, model=model, max_tokens=min(1024, cost * 40))
    ent["creditsRemaining"] = int(ent["creditsRemaining"]) - cost
    _ENTITLEMENTS[body.deviceId] = ent

    # Log usage without message content
    print(
        json.dumps(
            {
                "event": "nana_agent_chat",
                "deviceHash": hashlib.sha256(body.deviceId.encode()).hexdigest()[:12],
                "productId": ent["productId"],
                "model": model,
                "creditsUsed": cost,
                "creditsRemaining": ent["creditsRemaining"],
            }
        )
    )
    return {
        "ok": True,
        "content": content,
        "model": model,
        "engineLabel": f"Agent · {model}",
        "creditsUsed": cost,
        "creditsRemaining": ent["creditsRemaining"],
    }
