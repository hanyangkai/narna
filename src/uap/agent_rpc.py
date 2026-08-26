"""Hermes-like execute_code RPC — call agent tools from sandboxed Python."""

from __future__ import annotations

import ast
import json
from typing import Any, Callable

ToolCaller = Callable[[str, dict[str, Any]], dict[str, Any]]

_MAX_NESTED_CALLS = 3
_CODE_FORBIDDEN = {
    ast.Import,
    ast.ImportFrom,
    ast.With,
    ast.AsyncWith,
    ast.AsyncFunctionDef,
    ast.AsyncFor,
    ast.ClassDef,
    ast.Global,
    ast.Nonlocal,
    ast.Lambda,
    ast.Yield,
    ast.YieldFrom,
    ast.Await,
}


def _validate_code(code: str) -> str | None:
    if not code.strip():
        return "code required"
    if len(code) > 8000:
        return "code too long (max 8000)"
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return f"syntax: {e}"
    for node in ast.walk(tree):
        if type(node) in _CODE_FORBIDDEN:
            return f"disallowed: {type(node).__name__}"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "open", "compile", "__import__", "input", "breakpoint"}:
                return f"call not allowed: {node.func.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return "dunder attributes blocked"
    return None


def run_execute_code(
    code: str,
    call_tool: ToolCaller,
    *,
    max_calls: int = _MAX_NESTED_CALLS,
) -> dict[str, Any]:
    """Run user code with injected call_tool(name, args) -> dict."""
    err = _validate_code(code)
    if err:
        return {"ok": False, "error": err}

    calls: list[dict[str, Any]] = []
    budget = {"left": max(1, int(max_calls))}

    def _call_tool(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        if budget["left"] <= 0:
            return {"ok": False, "error": "nested tool call budget exhausted"}
        budget["left"] -= 1
        out = call_tool(str(name), dict(args or {}))
        calls.append({"tool": name, "args": args or {}, "result": out})
        return out

    safe_builtins = {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "sorted": sorted,
        "round": round,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "json": json,
        "print": lambda *a, **k: None,
    }
    local: dict[str, Any] = {"call_tool": _call_tool}
    try:
        tree = ast.parse(code, mode="exec")
        exec(compile(tree, "<narna-rpc>", "exec"), {"__builtins__": safe_builtins}, local)  # noqa: S102
    except Exception as e:
        return {"ok": False, "error": str(e), "toolCalls": calls}

    result = local.get("result", local.get("out"))
    if result is None and len(local) > 1:
        for k, v in local.items():
            if k != "call_tool":
                result = v
                break

    def _jsonable(v: Any) -> bool:
        try:
            json.dumps(v)
            return True
        except Exception:
            return False

    return {
        "ok": True,
        "result": result if _jsonable(result) else str(result)[:2000],
        "toolCalls": calls,
        "callsUsed": len(calls),
    }
