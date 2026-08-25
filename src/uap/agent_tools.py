"""NARNA Agent tools — Hermes-style tool surface (safe subset)."""

from __future__ import annotations

import ast
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def _http_get(url: str, *, timeout: int = 20, max_bytes: int = 200_000) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "narna-agent/0.2 (+https://narna.org)"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(max_bytes)
    return raw.decode("utf-8", errors="replace")


def tool_web_fetch(args: dict[str, Any]) -> dict[str, Any]:
    url = str(args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "url must start with http(s)://"}
    try:
        text = _http_get(url)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Strip tags lightly for HTML pages
    if "<html" in text.lower() or "<body" in text.lower():
        text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
        text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
        text = re.sub(r"(?is)<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
    return {"ok": True, "url": url, "text": text[:8000]}


def tool_web_search(args: dict[str, Any]) -> dict[str, Any]:
    """DuckDuckGo Instant Answer API (no key). Fallback: empty hits."""
    q = str(args.get("query") or "").strip()
    if not q:
        return {"ok": False, "error": "query required"}
    url = "https://api.duckduckgo.com/?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "no_html": 1, "skip_disambig": 1}
    )
    try:
        data = json.loads(_http_get(url, timeout=15))
    except Exception as e:
        return {"ok": False, "error": str(e), "query": q, "hits": []}
    hits: list[dict[str, str]] = []
    abstract = str(data.get("AbstractText") or "").strip()
    if abstract:
        hits.append(
            {
                "title": str(data.get("Heading") or q),
                "url": str(data.get("AbstractURL") or ""),
                "snippet": abstract[:500],
            }
        )
    for topic in (data.get("RelatedTopics") or [])[:5]:
        if isinstance(topic, dict) and topic.get("Text"):
            hits.append(
                {
                    "title": str(topic.get("Text") or "")[:80],
                    "url": str(topic.get("FirstURL") or ""),
                    "snippet": str(topic.get("Text") or "")[:400],
                }
            )
    return {"ok": True, "query": q, "hits": hits}


def tool_calculator(args: dict[str, Any]) -> dict[str, Any]:
    expr = str(args.get("expression") or "").strip()
    if not expr:
        return {"ok": False, "error": "expression required"}
    try:
        node = ast.parse(expr, mode="eval")
        allowed = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Constant,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Pow,
            ast.Mod,
            ast.FloorDiv,
            ast.USub,
            ast.UAdd,
            ast.Call,
            ast.Name,
            ast.Load,
            ast.Tuple,
        )
        for n in ast.walk(node):
            if not isinstance(n, allowed):
                return {"ok": False, "error": f"disallowed syntax: {type(n).__name__}"}
            if isinstance(n, ast.Call):
                if not isinstance(n.func, ast.Name) or n.func.id not in {"abs", "round", "min", "max"}:
                    return {"ok": False, "error": "only abs/round/min/max allowed"}
            if isinstance(n, ast.Name) and n.id not in {"abs", "round", "min", "max"}:
                return {"ok": False, "error": f"name not allowed: {n.id}"}
        value = eval(  # noqa: S307 — guarded AST
            compile(node, "<calc>", "eval"),
            {"__builtins__": {}},
            {"abs": abs, "round": round, "min": min, "max": max, "pi": math.pi, "e": math.e},
        )
        return {"ok": True, "expression": expr, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_datetime_now(_args: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {"ok": True, "utc": now.isoformat().replace("+00:00", "Z"), "unix": int(now.timestamp())}


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


def tool_code_exec(args: dict[str, Any]) -> dict[str, Any]:
    """Hermes-like sandbox: pure Python expressions / short scripts, no I/O imports."""
    code = str(args.get("code") or args.get("source") or "").strip()
    if not code:
        return {"ok": False, "error": "code required"}
    if len(code) > 4000:
        return {"ok": False, "error": "code too long (max 4000)"}
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return {"ok": False, "error": f"syntax: {e}"}
    for node in ast.walk(tree):
        if type(node) in _CODE_FORBIDDEN:
            return {"ok": False, "error": f"disallowed: {type(node).__name__}"}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "open", "compile", "__import__", "input", "breakpoint"}:
                return {"ok": False, "error": f"call not allowed: {node.func.id}"}
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return {"ok": False, "error": "dunder attributes blocked"}
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
        "print": lambda *a, **k: None,
    }
    local: dict[str, Any] = {}
    try:
        exec(compile(tree, "<narna-sandbox>", "exec"), {"__builtins__": safe_builtins}, local)  # noqa: S102
    except Exception as e:
        return {"ok": False, "error": str(e)}
    # Prefer explicit result / out variable
    result = local.get("result", local.get("out"))
    if result is None and len(local) == 1:
        result = next(iter(local.values()))
    return {
        "ok": True,
        "result": result if _jsonable(result) else str(result)[:2000],
        "locals": {k: (_jsonable(v) and v) or str(v)[:200] for k, v in list(local.items())[:20]},
    }


def _jsonable(v: Any) -> bool:
    try:
        json.dumps(v)
        return True
    except Exception:
        return False


def _safe_workspace_path(root: Path, rel: str) -> Path | None:
    rel = (rel or "").replace("\\", "/").lstrip("/")
    if not rel or ".." in rel.split("/"):
        return None
    base = (root / ".uap" / "agent-workspace").resolve()
    base.mkdir(parents=True, exist_ok=True)
    target = (base / rel).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        return None
    return target


TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "web_search",
        "description": "Search the public web (DuckDuckGo). Use for current facts.",
        "parameters": {"query": "string"},
    },
    {
        "name": "web_fetch",
        "description": "Fetch a URL and return readable text (truncated).",
        "parameters": {"url": "string"},
    },
    {
        "name": "calculator",
        "description": "Evaluate a simple arithmetic expression.",
        "parameters": {"expression": "string"},
    },
    {
        "name": "code_exec",
        "description": "Run sandboxed Python (no imports/I/O). Set result=... to return a value.",
        "parameters": {"code": "string"},
    },
    {
        "name": "datetime_now",
        "description": "Current UTC time.",
        "parameters": {},
    },
    {
        "name": "workspace_list",
        "description": "List files in the agent workspace sandbox.",
        "parameters": {"path": "string"},
    },
    {
        "name": "workspace_read",
        "description": "Read a text file from the agent workspace sandbox.",
        "parameters": {"path": "string"},
    },
    {
        "name": "workspace_write",
        "description": "Write a text file into the agent workspace sandbox.",
        "parameters": {"path": "string", "text": "string"},
    },
    {
        "name": "memory_query",
        "description": "Query NARNA Decision Memory priors/lessons.",
        "parameters": {"action": "string", "limit": "int"},
    },
    {
        "name": "skill_list",
        "description": "List saved agent skills.",
        "parameters": {},
    },
    {
        "name": "skill_get",
        "description": "Load a skill by id.",
        "parameters": {"skillId": "string"},
    },
    {
        "name": "skill_save",
        "description": "Save or update a reusable skill from this session.",
        "parameters": {"name": "string", "body": "string", "tags": "list"},
    },
]


class AgentToolbelt:
    def __init__(
        self,
        *,
        memory: Any = None,
        skills: Any = None,
        workspace: Path | str | None = None,
    ) -> None:
        self.memory = memory
        self.skills = skills
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "web_search": tool_web_search,
            "web_fetch": tool_web_fetch,
            "calculator": tool_calculator,
            "code_exec": tool_code_exec,
            "datetime_now": tool_datetime_now,
            "workspace_list": self._workspace_list,
            "workspace_read": self._workspace_read,
            "workspace_write": self._workspace_write,
            "memory_query": self._memory_query,
            "skill_list": self._skill_list,
            "skill_get": self._skill_get,
            "skill_save": self._skill_save,
        }

    def specs(self) -> list[dict[str, Any]]:
        return list(TOOL_SPECS)

    def call(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        fn = self._handlers.get(name)
        if not fn:
            return {"ok": False, "error": f"unknown tool: {name}"}
        try:
            return fn(dict(args or {}))
        except Exception as e:
            return {"ok": False, "error": str(e), "tool": name}

    def _workspace_list(self, args: dict[str, Any]) -> dict[str, Any]:
        rel = str(args.get("path") or ".")
        if rel in {".", ""}:
            base = (self.workspace / ".uap" / "agent-workspace").resolve()
            base.mkdir(parents=True, exist_ok=True)
            path = base
        else:
            path = _safe_workspace_path(self.workspace, rel)
            if path is None:
                return {"ok": False, "error": "invalid path"}
        if not path.exists():
            return {"ok": True, "entries": []}
        if path.is_file():
            return {"ok": True, "entries": [{"name": path.name, "type": "file", "size": path.stat().st_size}]}
        entries = []
        for p in sorted(path.iterdir())[:100]:
            entries.append(
                {
                    "name": p.name,
                    "type": "dir" if p.is_dir() else "file",
                    "size": p.stat().st_size if p.is_file() else None,
                }
            )
        return {"ok": True, "entries": entries}

    def _workspace_read(self, args: dict[str, Any]) -> dict[str, Any]:
        path = _safe_workspace_path(self.workspace, str(args.get("path") or ""))
        if path is None or not path.is_file():
            return {"ok": False, "error": "file not found or invalid path"}
        text = path.read_text(encoding="utf-8", errors="replace")
        return {"ok": True, "path": str(args.get("path")), "text": text[:20000]}

    def _workspace_write(self, args: dict[str, Any]) -> dict[str, Any]:
        path = _safe_workspace_path(self.workspace, str(args.get("path") or ""))
        if path is None:
            return {"ok": False, "error": "invalid path"}
        text = str(args.get("text") or "")
        if len(text) > 100_000:
            return {"ok": False, "error": "text too large"}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return {"ok": True, "path": str(args.get("path")), "bytes": len(text.encode("utf-8"))}

    def _memory_query(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.memory is None:
            return {"ok": False, "error": "memory not configured"}
        limit = int(args.get("limit") or 5)
        rows = self.memory.query(action=args.get("action"), limit=limit)
        compact = [
            {
                "decisionId": r.get("decisionId"),
                "dqs": r.get("dqs"),
                "guardian": r.get("guardian"),
                "lesson": r.get("lesson"),
                "action": r.get("action"),
            }
            for r in rows
        ]
        return {"ok": True, "records": compact}

    def _skill_list(self, _args: dict[str, Any]) -> dict[str, Any]:
        if self.skills is None:
            return {"ok": False, "error": "skills not configured"}
        return {"ok": True, "skills": self.skills.list_skills()}

    def _skill_get(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.skills is None:
            return {"ok": False, "error": "skills not configured"}
        sid = str(args.get("skillId") or args.get("id") or "")
        row = self.skills.get(sid)
        if not row:
            return {"ok": False, "error": f"unknown skill: {sid}"}
        return {"ok": True, "skill": row}

    def _skill_save(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.skills is None:
            return {"ok": False, "error": "skills not configured"}
        name = str(args.get("name") or "").strip()
        body = str(args.get("body") or "").strip()
        if not name or not body:
            return {"ok": False, "error": "name and body required"}
        tags = args.get("tags") if isinstance(args.get("tags"), list) else []
        row = self.skills.save(name=name, body=body, tags=[str(t) for t in tags])
        return {"ok": True, "skill": row}
