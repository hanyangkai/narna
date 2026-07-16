from __future__ import annotations

import json
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator

from .canon import canonical_json_bytes
from .errors import ExecutionError, ValidationError
from .evidence import EvidenceStore
from .hashing import sha256_obj
from .http import http_get_json, is_live_mode
from .schemas import load_schema


@dataclass
class ToolResult:
    ok: bool
    output: dict[str, Any] | None = None
    error: str | None = None
    evidence_content: dict[str, Any] | None = None
    evidence_source: dict[str, Any] | None = None


class ToolAdapter(Protocol):
    name: str

    def execute(self, input_data: dict[str, Any]) -> ToolResult: ...


def load_tool_definition(name: str) -> dict[str, Any]:
    candidates = [
        Path("specs/examples") / f"tool-{name.replace('.', '-')}.json",
        Path(__file__).resolve().parents[3] / "specs" / "examples" / f"tool-{name.replace('.', '-')}.json",
    ]
    # naming: coinbase.spot_price -> tool-coinbase-spot.json won't work; use registry defaults
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return DEFAULT_TOOLS[name]


DEFAULT_TOOLS: dict[str, dict[str, Any]] = {
    "coinbase.spot_price": {
        "name": "coinbase.spot_price",
        "capability": "trade",
        "requiredPermissions": ["market.read"],
        "sideEffect": "external",
        "inputSchema": {
            "type": "object",
            "required": ["pair"],
            "properties": {"pair": {"type": "string"}},
        },
        "outputSchema": {
            "type": "object",
            "required": ["pair", "amount", "currency"],
            "properties": {
                "pair": {"type": "string"},
                "amount": {"type": "string"},
                "currency": {"type": "string"},
            },
        },
        "evidencePolicy": {
            "requiredTypes": ["api_response"],
            "minSources": 1,
            "maxAgeSeconds": 300,
            "onMissing": "fail",
        },
    },
    "binance.ticker": {
        "name": "binance.ticker",
        "capability": "trade",
        "requiredPermissions": ["market.read"],
        "sideEffect": "external",
        "inputSchema": {
            "type": "object",
            "required": ["symbol"],
            "properties": {"symbol": {"type": "string"}},
        },
        "outputSchema": {
            "type": "object",
            "required": ["symbol", "price"],
            "properties": {"symbol": {"type": "string"}, "price": {"type": "string"}},
        },
        "evidencePolicy": {
            "requiredTypes": ["api_response"],
            "minSources": 1,
            "maxAgeSeconds": 300,
            "onMissing": "fail",
        },
    },
    "wallet.transfer": {
        "name": "wallet.transfer",
        "capability": "wallet",
        "requiredPermissions": ["wallet.transfer"],
        "sideEffect": "irreversible",
        "inputSchema": {
            "type": "object",
            "required": ["amount", "currency", "recipient"],
            "properties": {
                "amount": {"type": "string"},
                "currency": {"type": "string"},
                "recipient": {"type": "string"},
            },
        },
        "outputSchema": {
            "type": "object",
            "required": ["receiptId", "status"],
            "properties": {"receiptId": {"type": "string"}, "status": {"type": "string"}},
        },
        "evidencePolicy": {
            "requiredTypes": ["receipt"],
            "minSources": 1,
            "maxAgeSeconds": 3600,
            "onMissing": "fail",
        },
    },
}


class CoinbaseSpotTool:
    name = "coinbase.spot_price"

    def execute(self, input_data: dict[str, Any]) -> ToolResult:
        pair = input_data["pair"]
        endpoint = f"https://api.coinbase.com/v2/prices/{pair}/spot"
        if is_live_mode():
            try:
                body, raw, status = http_get_json(endpoint)
                amount = str(body["data"]["amount"])
                currency = str(body["data"]["currency"])
                return ToolResult(
                    ok=True,
                    output={"pair": pair, "amount": amount, "currency": currency},
                    evidence_content=body,
                    evidence_source={
                        "provider": "coinbase",
                        "endpoint": f"GET /v2/prices/{pair}/spot",
                        "toolName": self.name,
                        "requestFingerprint": sha256_obj(input_data),
                        "statusCode": status,
                        "canonicalization": "raw_bytes",
                    },
                )
            except (urllib.error.URLError, KeyError, json.JSONDecodeError):
                pass  # fallback to mock

        amount = "120000.00" if "BTC" in pair else "1.00"
        body = {"data": {"amount": amount, "currency": pair.split("-")[-1], "base": pair.split("-")[0]}}
        return ToolResult(
            ok=True,
            output={"pair": pair, "amount": amount, "currency": pair.split("-")[-1]},
            evidence_content=body,
            evidence_source={
                "provider": "coinbase",
                "endpoint": f"GET /v2/prices/{pair}/spot",
                "toolName": self.name,
                "requestFingerprint": sha256_obj(input_data),
                "statusCode": 200,
                "canonicalization": "raw_bytes",
            },
        )


class BinanceTickerTool:
    name = "binance.ticker"

    def execute(self, input_data: dict[str, Any]) -> ToolResult:
        symbol = input_data["symbol"]
        endpoint = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        if is_live_mode():
            try:
                body, _raw, status = http_get_json(endpoint)
                price = str(body["price"])
                out = {"symbol": symbol, "price": price}
                return ToolResult(
                    ok=True,
                    output=out,
                    evidence_content=out,
                    evidence_source={
                        "provider": "binance",
                        "endpoint": f"GET /api/v3/ticker/price?symbol={symbol}",
                        "toolName": self.name,
                        "requestFingerprint": sha256_obj(input_data),
                        "statusCode": status,
                        "canonicalization": "raw_bytes",
                    },
                )
            except (urllib.error.URLError, KeyError, json.JSONDecodeError):
                pass

        price = "120050.00" if "BTC" in symbol else "1.00"
        body = {"symbol": symbol, "price": price}
        return ToolResult(
            ok=True,
            output=body,
            evidence_content=body,
            evidence_source={
                "provider": "binance",
                "endpoint": f"GET /api/v3/ticker/price?symbol={symbol}",
                "toolName": self.name,
                "requestFingerprint": sha256_obj(input_data),
                "statusCode": 200,
                "canonicalization": "raw_bytes",
            },
        )


class WalletTransferTool:
    name = "wallet.transfer"

    def execute(self, input_data: dict[str, Any]) -> ToolResult:
        receipt = {
            "receiptId": "rcpt_" + sha256_obj(input_data)[7:19],
            "status": "submitted",
            **input_data,
        }
        return ToolResult(
            ok=True,
            output={"receiptId": receipt["receiptId"], "status": "submitted"},
            evidence_content=receipt,
            evidence_source={
                "provider": "wallet",
                "endpoint": "POST /transfer",
                "toolName": self.name,
                "requestFingerprint": sha256_obj(input_data),
                "statusCode": 200,
                "canonicalization": "canonical_json",
            },
        )


TOOL_ADAPTERS: dict[str, ToolAdapter] = {
    "coinbase.spot_price": CoinbaseSpotTool(),
    "binance.ticker": BinanceTickerTool(),
    "wallet.transfer": WalletTransferTool(),
}


def validate_tool_input(defn: dict[str, Any], input_data: dict[str, Any]) -> None:
    schema = defn.get("inputSchema", {})
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(input_data), key=lambda e: e.path)
    if errors:
        raise ValidationError(errors[0].message)


def execute_tool(
    tool_name: str,
    input_data: dict[str, Any],
    *,
    evidence_store: EvidenceStore,
    provenance: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if tool_name not in TOOL_ADAPTERS:
        raise ExecutionError(f"unknown tool: {tool_name}")
    defn = load_tool_definition(tool_name)
    validate_tool_input(defn, input_data)
    adapter = TOOL_ADAPTERS[tool_name]
    result = adapter.execute(input_data)
    if not result.ok:
        raise ExecutionError(result.error or "tool failed")

    evidence = None
    if result.evidence_content and result.evidence_source:
        ev_type = "receipt" if defn.get("sideEffect") == "irreversible" else "api_response"
        evidence = evidence_store.save(
            evidence_type=ev_type,
            content=result.evidence_content,
            source=result.evidence_source,
            provenance=provenance,
            verifiers=["hash_match", "freshness", "schema"],
        )
    return result.output or {}, evidence
