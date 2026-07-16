"""Adapter base — Never Replace. Always Extend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AdapterResult:
    framework: str
    package: str
    status: str = "available"
    hooks: list[str] = field(default_factory=list)
    message: str = ""


class BaseAdapter:
    id: str = "generic"
    package: str = "narna-generic"

    def matches(self, obj: Any) -> bool:
        return False

    def attach(self, agent: Any, foreign: Any) -> AdapterResult:
        hooks = self._install_hooks(agent, foreign)
        return AdapterResult(
            framework=self.id,
            package=self.package,
            status="available",
            hooks=hooks,
            message=f"Works with {self.id}. Business logic unchanged.",
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        return []

    def _wrap_method(self, foreign: Any, method_name: str, agent: Any) -> bool:
        """Wrap a method to record a NARNA run around the original call."""
        if foreign is None or not hasattr(foreign, method_name):
            return False
        original = getattr(foreign, method_name)
        if not callable(original):
            return False
        if getattr(original, "__narna_wrapped__", False):
            return True

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            result = original(*args, **kwargs)
            try:
                prompt = None
                if args and isinstance(args[0], str):
                    prompt = args[0]
                elif isinstance(kwargs.get("input"), str):
                    prompt = kwargs["input"]
                agent.run(prompt or f"{self.id}.{method_name}")
            except Exception:
                pass
            return result

        wrapped.__narna_wrapped__ = True  # type: ignore[attr-defined]
        wrapped.__wrapped__ = original  # type: ignore[attr-defined]
        try:
            setattr(foreign, method_name, wrapped)
            return True
        except Exception:
            return False
