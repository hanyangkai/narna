"""narna-google — Works with Google ADK / Gemini client patterns."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class GoogleAdapter(BaseAdapter):
    id = "google"
    package = "narna-google"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(
            x in blob
            for x in (
                "google.genai",
                "google.generativeai",
                "vertexai",
                "gemini",
                "generativemodel",
                "google.adk",
            )
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in (
            "generate_content",
            "generateContent",
            "send_message",
            "run",
            "invoke",
            "stream",
            "__call__",
        ):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        models = getattr(foreign, "models", None)
        if models is not None and self._wrap_method(models, "generate_content", agent):
            hooks.append("models.generate_content")
        return hooks
