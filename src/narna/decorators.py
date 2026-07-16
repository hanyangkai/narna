"""Lightweight SDK decorators — Identity, Policy, Audit without a framework."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Callable, TypeVar

from uap.agent import Agent

F = TypeVar("F", bound=Callable[..., Any])


def agent(
    _fn: F | None = None,
    *,
    name: str | None = None,
    vap: bool = True,
    workspace: str | Path | None = None,
) -> Any:
    """Decorator: register a function as a NARNA-governed agent.

    Example::

        from narna import agent

        @agent
        def research(query: str) -> str:
            return llm(query)
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            label = name or getattr(fn, "__name__", "agent")
            ws = Path(workspace) if workspace else Path.cwd()
            governed = Agent(str(label), workspace=ws, vap=vap)
            governed._wrapped = fn
            from narna.adapters import attach_adapter

            attach_adapter(governed, fn, "callable")
            user_input = None
            if args and isinstance(args[0], str):
                user_input = args[0]
            result = fn(*args, **kwargs)
            try:
                governed.run(user_input or f"agent:{label}")
            except Exception:
                pass
            governed._tracked_result = result  # type: ignore[attr-defined]
            return result

        return wrapper  # type: ignore[return-value]

    if _fn is not None:
        return decorator(_fn)
    return decorator


def policy(
    permission: str,
    *,
    mode: str = "allow",
    workspace: str | Path | None = None,
) -> Callable[[F], F]:
    """Decorator: enforce a permission before executing.

    Example::

        from narna import policy

        @policy("wallet.transfer", mode="deny")
        def pay(amount: float) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ws = Path(workspace) if workspace else Path.cwd()
            from uap.policy import PolicyEngine

            engine = PolicyEngine(ws)
            decision = engine.evaluate(
                policy_ref="policies/local-default@0.0.0",
                agent_permissions=[{"name": permission, "mode": mode}],
                permission=permission,
                parameters=kwargs,
            )
            if decision.get("decision") == "deny":
                raise PermissionError(f"NARNA policy denied: {permission}")
            if decision.get("decision") == "ask":
                raise PermissionError(f"NARNA policy requires approval: {permission}")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def audit(
    _fn: F | None = None,
    *,
    agent_id: str | None = None,
    workspace: str | Path | None = None,
) -> Any:
    """Decorator: audit function execution via NARNA event log.

    Example::

        from narna import audit

        @audit
        def transfer_funds(amount: float) -> str:
            ...
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ws = Path(workspace) if workspace else Path.cwd()
            label = agent_id or getattr(fn, "__name__", "audited")
            governed = Agent(str(label), workspace=ws, vap=True)
            governed._wrapped = fn
            result = fn(*args, **kwargs)
            try:
                run = governed.run(f"audit:{label}")
                audit_report = governed.audit(run.run_id)
                wrapper._last_audit = audit_report  # type: ignore[attr-defined]
            except Exception:
                pass
            return result

        return wrapper  # type: ignore[return-value]

    if _fn is not None:
        return decorator(_fn)
    return decorator
