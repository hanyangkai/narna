"""narna-semantic-kernel — Works with Microsoft Semantic Kernel."""

from __future__ import annotations

from typing import Any

from .base import BaseAdapter


class SemanticKernelAdapter(BaseAdapter):
    id = "semantic_kernel"
    package = "narna-semantic-kernel"
    default_unit_kind = "workflow_step"

    def matches(self, obj: Any) -> bool:
        if obj is None:
            return False
        mod = (getattr(type(obj), "__module__", "") or "").lower()
        name = type(obj).__name__.lower()
        blob = f"{mod}.{name}"
        return any(
            x in blob
            for x in (
                "semantic_kernel",
                "semantickernel",
                "skfunction",
                "chatcompletionagent",
            )
        ) or (
            ("semantic_kernel" in mod or mod.startswith("sk."))
            and name in {"kernel", "chatcompletionagent", "agentservice"}
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        hooks: list[str] = []
        for method in ("invoke", "ainvoke", "invoke_prompt", "run", "get_chat_message_contents"):
            if self._wrap_method(foreign, method, agent):
                hooks.append(method)
        return hooks
