"""One-line integration — Borrow the Wave (Never Replace. Always Extend.)."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Callable, TypeVar

from uap.agent import Agent

from .adapters import attach_adapter, detect_framework

F = TypeVar("F", bound=Callable[..., Any])


def wrap(
    foreign: Any = None,
    *,
    name: str | None = None,
    workspace: str | Path | None = None,
    vap: bool = False,
    manifest: str | Path | None = None,
    mode: str | None = None,
) -> Agent:
    """Wrap any existing agent / graph / callable with NARNA.

    Never replaces the underlying framework — only extends it.

    Example::

        from narna import wrap
        agent = wrap(my_openai_agent, vap=True)
        agent.run("summarize")
    """
    if isinstance(foreign, Agent):
        if vap:
            foreign.enable_vap()
        return foreign

    ws = Path(workspace) if workspace else Path.cwd()
    label = name
    framework = detect_framework(foreign)
    if label is None and foreign is not None:
        label = (
            getattr(foreign, "name", None)
            or getattr(foreign, "__name__", None)
            or ((framework.replace("_", " ").title() + " Agent") if framework else None)
        )

    if manifest:
        from uap.manifest import load_or_compile_constitution

        load_or_compile_constitution(manifest, workspace=ws)
    else:
        from uap.manifest import discover_manifest, load_or_compile_constitution

        found = discover_manifest(ws)
        if found and found.name.startswith("narna"):
            try:
                load_or_compile_constitution(found, workspace=ws)
            except Exception:
                pass

    agent = Agent(
        str(label) if label else "Wrapped Agent",
        workspace=ws,
        vap=vap,
    )
    agent._wrapped = foreign
    agent._framework = framework  # type: ignore[attr-defined]
    if mode is not None:
        agent._narna_adapter_mode = mode  # type: ignore[attr-defined]
    attach_adapter(agent, foreign, framework)
    return agent


def track(
    _fn: F | None = None,
    *,
    name: str | None = None,
    vap: bool = True,
    workspace: str | Path | None = None,
) -> Any:
    """Decorator: one-line NARNA tracking around a function.

    Business logic is unchanged — NARNA only records identity/events/trust.

    Example::

        from narna import track

        @track
        def research(query: str) -> str:
            return expensive_llm_call(query)

        research("btc price")
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            label = name or getattr(fn, "__name__", "tracked")
            ws = Path(workspace) if workspace else Path.cwd()
            agent = Agent(str(label), workspace=ws, vap=vap)
            agent._wrapped = fn
            attach_adapter(agent, fn, "callable")

            user_input = None
            if args and isinstance(args[0], str):
                user_input = args[0]
            elif isinstance(kwargs.get("query"), str):
                user_input = kwargs["query"]
            elif isinstance(kwargs.get("input"), str):
                user_input = kwargs["input"]

            value = fn(*args, **kwargs)
            try:
                agent.run(user_input or f"tracked:{label}")
            except Exception:
                pass
            agent._tracked_result = value  # type: ignore[attr-defined]
            return value

        return wrapper  # type: ignore[return-value]

    if _fn is not None:
        return decorator(_fn)
    return decorator
