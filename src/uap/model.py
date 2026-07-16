from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from .hashing import sha256_hex


@dataclass
class ModelIntent:
    tool_name: str | None
    tool_input: dict[str, Any] | None
    artifact_hash: str
    raw_input: str


class ModelAdapter(Protocol):
    def understand(self, user_input: str) -> ModelIntent: ...


class StubModelAdapter:
    """Maps simple text to tool intents (default, offline)."""

    def understand(self, user_input: str) -> ModelIntent:
        text = user_input.strip().lower()
        artifact = "sha256:" + sha256_hex(user_input.encode("utf-8"))

        if "compare" in text or ("btc" in text and "binance" in text):
            return ModelIntent(
                tool_name="binance.ticker",
                tool_input={"symbol": "BTCUSDT"},
                artifact_hash=artifact,
                raw_input=user_input,
            )
        if "transfer" in text or "wallet" in text:
            return ModelIntent(
                tool_name="wallet.transfer",
                tool_input={"amount": "50", "currency": "USDT", "recipient": "0xabc"},
                artifact_hash=artifact,
                raw_input=user_input,
            )
        if "binance" in text:
            return ModelIntent(
                tool_name="binance.ticker",
                tool_input={"symbol": "BTCUSDT"},
                artifact_hash=artifact,
                raw_input=user_input,
            )
        if "price" in text or "btc" in text:
            return ModelIntent(
                tool_name="coinbase.spot_price",
                tool_input={"pair": "BTC-USD"},
                artifact_hash=artifact,
                raw_input=user_input,
            )
        return ModelIntent(tool_name=None, tool_input=None, artifact_hash=artifact, raw_input=user_input)


class OllamaModelAdapter:
    """Optional local LLM via Ollama /api/generate (JSON intent)."""

    def __init__(self, *, model: str = "llama3.2", host: str | None = None) -> None:
        self.model = model
        self.host = (host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self._fallback = StubModelAdapter()

    def understand(self, user_input: str) -> ModelIntent:
        prompt = (
            "You are a UAP agent planner. Return ONLY JSON with keys: "
            'tool_name (coinbase.spot_price|binance.ticker|wallet.transfer|null), '
            "tool_input (object). User: "
            + user_input
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        try:
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            parsed = json.loads(data.get("response", "{}"))
            tool_name = parsed.get("tool_name")
            tool_input = parsed.get("tool_input")
            if tool_name == "null":
                tool_name = None
            artifact = "sha256:" + sha256_hex(user_input.encode("utf-8"))
            return ModelIntent(
                tool_name=tool_name,
                tool_input=tool_input,
                artifact_hash=artifact,
                raw_input=user_input,
            )
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError):
            return self._fallback.understand(user_input)


def create_model_adapter(spec: dict[str, Any] | None = None) -> ModelAdapter:
    provider = (os.environ.get("UAP_MODEL") or (spec or {}).get("provider") or "stub").lower()
    preference = (spec or {}).get("preference") or os.environ.get("UAP_MODEL_NAME", "llama3.2")
    if provider in {"ollama", "local"}:
        return OllamaModelAdapter(model=str(preference))
    return StubModelAdapter()
