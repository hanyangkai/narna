"""Paddle Billing API client (replaces Stripe for NARNA Cloud payments).

Docs: https://developer.paddle.com/api-reference/overview
Auth: Bearer pdl_live_apikey_… / pdl_sdbx_apikey_…
"""

from __future__ import annotations

import os
from typing import Any

import urllib.error
import urllib.request
import json


def paddle_api_key() -> str:
    return (os.environ.get("PADDLE_API_KEY") or "").strip()


def paddle_api_base() -> str:
    key = paddle_api_key()
    # Sandbox keys use sandbox-api.paddle.com
    if key.startswith("pdl_sdbx_"):
        return "https://sandbox-api.paddle.com"
    return os.environ.get("PADDLE_API_BASE", "https://api.paddle.com").rstrip("/")


def paddle_product_id() -> str:
    return (os.environ.get("PADDLE_PRODUCT_ID") or "").strip()


def paddle_request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    key = paddle_api_key()
    if not key:
        raise RuntimeError("PADDLE_API_KEY missing")

    url = f"{paddle_api_base()}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method.upper(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Paddle-Version": "1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"error": {"detail": err_body or str(e)}}
        detail = (
            (parsed.get("error") or {}).get("detail")
            or (parsed.get("error") or {}).get("code")
            or err_body
            or str(e)
        )
        code = (parsed.get("error") or {}).get("code") or ""
        raise RuntimeError(f"paddle {e.code}: {code} {detail}".strip()) from e


def create_package_checkout(
    *,
    package_id: str,
    package_name: str,
    price_cents: int,
    org_id: int,
    take_rate_bps: int,
    gu_charged: int,
    success_url: str | None = None,
) -> dict[str, Any]:
    """Create a one-time Paddle transaction + checkout URL for a Governance Package.

    Uses non-catalog price attached to PADDLE_PRODUCT_ID so each package can have
    a dynamic amount without creating a Price row per SKU.
    """
    product_id = paddle_product_id()
    if not product_id:
        raise RuntimeError("PADDLE_PRODUCT_ID missing — create a product in Paddle Dashboard or via API")

    amount = str(int(price_cents))
    payload: dict[str, Any] = {
        "items": [
            {
                "quantity": 1,
                "price": {
                    "description": f"NARNA Governance Package · {package_id}",
                    "name": package_name[:100] or package_id,
                    "product_id": product_id,
                    "unit_price": {"amount": amount, "currency_code": "USD"},
                    "tax_mode": "account_setting",
                },
            }
        ],
        "currency_code": "USD",
        "collection_mode": "automatic",
        "custom_data": {
            "kind": "package",
            "package_id": package_id,
            "org_id": str(org_id),
            "price_usd": amount,
            "take_rate_bps": str(take_rate_bps),
            "gu_charged": str(gu_charged),
        },
    }
    if success_url:
        # Approved domain payment link base; Paddle appends ?_ptxn=
        payload["checkout"] = {"url": success_url}

    resp = paddle_request("POST", "/transactions", payload)
    data = resp.get("data") or {}
    checkout = data.get("checkout") or {}
    return {
        "transactionId": data.get("id"),
        "status": data.get("status"),
        "checkoutUrl": checkout.get("url"),
        "raw": data,
    }


def get_transaction(transaction_id: str) -> dict[str, Any]:
    resp = paddle_request("GET", f"/transactions/{transaction_id}")
    return resp.get("data") or {}


def create_plan_checkout(
    *,
    plan: str,
    org_id: int,
    price_cents: int,
    success_url: str | None = None,
) -> dict[str, Any]:
    """One-time / first payment for a Cloud plan via Paddle (non-catalog)."""
    product_id = paddle_product_id()
    if not product_id:
        raise RuntimeError("PADDLE_PRODUCT_ID missing")

    payload: dict[str, Any] = {
        "items": [
            {
                "quantity": 1,
                "price": {
                    "description": f"NARNA Cloud plan {plan}",
                    "name": f"NARNA {plan.title()}",
                    "product_id": product_id,
                    "unit_price": {"amount": str(int(price_cents)), "currency_code": "USD"},
                    "tax_mode": "account_setting",
                    "billing_cycle": {"interval": "month", "frequency": 1},
                },
            }
        ],
        "currency_code": "USD",
        "collection_mode": "automatic",
        "custom_data": {
            "kind": "subscription",
            "plan": plan,
            "org_id": str(org_id),
        },
    }
    if success_url:
        payload["checkout"] = {"url": success_url}

    resp = paddle_request("POST", "/transactions", payload)
    data = resp.get("data") or {}
    checkout = data.get("checkout") or {}
    return {
        "transactionId": data.get("id"),
        "status": data.get("status"),
        "checkoutUrl": checkout.get("url"),
        "raw": data,
    }
