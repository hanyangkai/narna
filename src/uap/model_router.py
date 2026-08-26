"""Model Router — NGS-0028 LLM-agnostic task routing."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


TASK_ALIASES: dict[str, str] = {
    "analyze": "reason",
    "plan": "reason",
    "decide": "reason",
    "cheap": "cheap",
    "reason": "reason",
    "challenge": "challenge",
}

DEFAULT_MODELS: dict[str, dict[str, str]] = {
    "openrouter": {
        "cheap": "openai/gpt-4o-mini",
        "reason": "openai/gpt-4o-mini",
        "challenge": "openai/gpt-4o-mini",
    },
    "openai": {
        "cheap": "gpt-4o-mini",
        "reason": "gpt-4o-mini",
        "challenge": "gpt-4o-mini",
    },
    "ollama": {
        "cheap": "llama3.2",
        "reason": "llama3.2",
        "challenge": "llama3.2",
    },
    "mock": {
        "cheap": "mock-cheap",
        "reason": "mock-reason",
        "challenge": "mock-challenge",
    },
}


@dataclass
class RouterResult:
    content: str
    model: str
    provider: str
    task: str
    usage: dict[str, int]
    tool_calls: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "task": self.task,
            "usage": self.usage,
            "standard": "NGS-0028",
        }
        if self.tool_calls:
            out["toolCalls"] = self.tool_calls
        return out


def normalize_task(task: str | None) -> str:
    t = (task or "reason").strip().lower()
    return TASK_ALIASES.get(t, "reason")


class ModelRouter:
    """Select and invoke a chat model for a cognitive task tag."""

    def __init__(
        self,
        *,
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        models: dict[str, str] | None = None,
    ) -> None:
        self.provider = (provider or os.environ.get("UAP_ROUTER_PROVIDER") or "mock").lower()
        self.api_key = api_key
        self.base_url = base_url
        self.models = models or {}

    def _resolve_key(self) -> str:
        if self.api_key:
            return self.api_key
        if self.provider == "openrouter":
            return os.environ.get("UAP_OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or ""
        if self.provider == "openai":
            return os.environ.get("UAP_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
        return ""

    def _resolve_base(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")
        if self.provider == "openrouter":
            return "https://openrouter.ai/api/v1"
        if self.provider == "openai":
            return "https://api.openai.com/v1"
        if self.provider == "ollama":
            return (
                os.environ.get("UAP_OLLAMA_BASE_URL") or "http://127.0.0.1:11434/v1"
            ).rstrip("/")
        return ""

    def pick_model(self, task: str) -> str:
        tag = normalize_task(task)
        env_map = {
            "cheap": "UAP_ROUTER_MODEL_CHEAP",
            "reason": "UAP_ROUTER_MODEL_REASON",
            "challenge": "UAP_ROUTER_MODEL_CHALLENGE",
        }
        env_key = env_map.get(tag)
        if env_key and os.environ.get(env_key):
            return os.environ[env_key].strip()
        if tag in self.models:
            return self.models[tag]
        defaults = DEFAULT_MODELS.get(self.provider) or DEFAULT_MODELS["mock"]
        return defaults.get(tag) or defaults["reason"]

    def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        task: str = "reason",
        temperature: float = 0.2,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> RouterResult:
        tag = normalize_task(task)
        model = self.pick_model(tag)
        if self.provider == "mock":
            return self._mock_complete(messages=messages, model=model, task=tag)
        return self._openai_compat_complete(
            messages=messages,
            model=model,
            task=tag,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            tool_choice=tool_choice,
        )

    def reason(self, prompt: str, **kwargs: Any) -> RouterResult:
        return self.complete(
            messages=[{"role": "user", "content": prompt}],
            task="reason",
            **kwargs,
        )

    def challenge(self, draft: str, question: str, **kwargs: Any) -> RouterResult:
        prompt = (
            "You are an adversarial challenger. Critique the draft answer. "
            "List risks, missing evidence, and a revised recommendation if needed.\n\n"
            f"Question:\n{question}\n\nDraft:\n{draft}"
        )
        return self.complete(
            messages=[{"role": "user", "content": prompt}],
            task="challenge",
            **kwargs,
        )

    def _mock_complete(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        task: str,
    ) -> RouterResult:
        last = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last = str(m.get("content") or "")
                break
        snippet = last.strip().replace("\n", " ")[:240]
        if task == "challenge":
            content = (
                f"[mock-challenge] Risks: incomplete evidence. "
                f"Recommendation: gather more context before acting. Re: {snippet}"
            )
        else:
            content = (
                f"[mock-{task}] Based on available context, here is a careful recommendation: "
                f"proceed only with explicit human review. Question summary: {snippet}"
            )
        return RouterResult(
            content=content,
            model=model,
            provider="mock",
            task=task,
            usage={"promptTokens": max(1, len(last) // 4), "completionTokens": max(1, len(content) // 4)},
        )

    def _openai_compat_complete(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        task: str,
        temperature: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> RouterResult:
        base = self._resolve_base()
        key = self._resolve_key()
        if self.provider in {"openrouter", "openai"} and not key:
            raise RuntimeError(f"{self.provider} API key not configured")
        if not base:
            raise RuntimeError(f"unsupported provider: {self.provider}")

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice or "auto"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "narna-model-router/0.1",
        }
        if key:
            headers["Authorization"] = f"Bearer {key}"
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = os.environ.get("NARNA_PUBLIC_URL", "https://narna.org")
            headers["X-Title"] = "NARNA Agent"

        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"router HTTP {e.code}: {detail}") from e

        choices = data.get("choices") or []
        content = ""
        native_calls: list[dict[str, Any]] = []
        if choices:
            msg = choices[0].get("message") or {}
            content = str(msg.get("content") or "")
            for tc in msg.get("tool_calls") or []:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function") if isinstance(tc.get("function"), dict) else {}
                name = str(fn.get("name") or "")
                raw_args = fn.get("arguments") or "{}"
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
                except Exception:
                    args = {"_raw": str(raw_args)}
                if name:
                    native_calls.append(
                        {
                            "tool": name,
                            "args": args if isinstance(args, dict) else {},
                            "id": tc.get("id"),
                        }
                    )
        usage_raw = data.get("usage") or {}
        usage = {
            "promptTokens": int(usage_raw.get("prompt_tokens") or 0),
            "completionTokens": int(usage_raw.get("completion_tokens") or 0),
        }
        return RouterResult(
            content=content or ("(tool call)" if native_calls else "(empty model response)"),
            model=str(data.get("model") or model),
            provider=self.provider,
            task=task,
            usage=usage,
            tool_calls=native_calls or None,
        )


def default_router_from_env() -> ModelRouter:
    return ModelRouter()
