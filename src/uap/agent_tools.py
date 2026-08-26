"""NARNA Agent tools — Hermes-style tool surface (safe subset)."""

from __future__ import annotations

import ast
import concurrent.futures
import json
import math
import os
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


_SHELL_ALLOW = {
    "ls",
    "dir",
    "pwd",
    "cat",
    "type",
    "head",
    "tail",
    "wc",
    "echo",
    "find",
    "grep",
    "rg",
    "python",
    "python3",
    "py",
    "node",
    "npm",
    "git",
    "which",
    "where",
}
_SHELL_DENY_SUBSTR = (
    "rm ",
    "del ",
    "sudo",
    "chmod",
    "chown",
    "mkfs",
    "dd ",
    ">:",
    "`",
    "$(",
    "curl ",
    "wget ",
    "powershell",
    "cmd.exe",
    "/etc/passwd",
)


def openai_tools_schema(specs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Convert TOOL_SPECS → OpenAI/OpenRouter `tools` array (Hermes-style native tool_calls)."""
    out: list[dict[str, Any]] = []
    for spec in specs or TOOL_SPECS:
        params = spec.get("parameters") or {}
        properties: dict[str, Any] = {}
        required: list[str] = []
        for key, typ in params.items():
            t = str(typ).lower()
            if t.startswith("list"):
                properties[key] = {"type": "array", "items": {"type": "string"}}
            elif t in {"int", "integer", "number", "float"}:
                properties[key] = {"type": "number"}
            elif t in {"bool", "boolean"}:
                properties[key] = {"type": "boolean"}
            else:
                properties[key] = {"type": "string"}
            required.append(str(key))
        out.append(
            {
                "type": "function",
                "function": {
                    "name": spec["name"],
                    "description": spec.get("description") or "",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": True,
                    },
                },
            }
        )
    return out


def tool_shell_exec(args: dict[str, Any], *, cwd: Path) -> dict[str, Any]:
    """Hermes-like allowlisted shell in agent workspace (optional docker backend)."""
    import shlex
    import subprocess

    cmd = str(args.get("command") or args.get("cmd") or "").strip()
    if not cmd:
        return {"ok": False, "error": "command required"}
    if len(cmd) > 500:
        return {"ok": False, "error": "command too long"}
    low = cmd.lower()
    for bad in _SHELL_DENY_SUBSTR:
        if bad in low:
            return {"ok": False, "error": f"blocked pattern: {bad.strip()}"}
    # Interactive approval gate (Hermes-like). Opt-in via env or explicit requireApproval.
    require = str(os.environ.get("UAP_SHELL_REQUIRE_APPROVAL") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if args.get("requireApproval") is True:
        require = True
    approved = args.get("approved") is True or str(args.get("approved") or "").lower() in {
        "1",
        "true",
        "yes",
    }
    if require and not approved:
        return {
            "ok": False,
            "needsApproval": True,
            "command": cmd,
            "error": "shell_exec requires human approval — re-call with approved=true",
        }
    try:
        parts = shlex.split(cmd, posix=os.name != "nt")
    except Exception as e:
        return {"ok": False, "error": f"parse error: {e}"}
    if not parts:
        return {"ok": False, "error": "empty command"}
    bin_name = Path(parts[0]).name.lower().replace(".exe", "")
    if bin_name not in _SHELL_ALLOW:
        return {"ok": False, "error": f"binary not allowlisted: {bin_name}"}
    cwd.mkdir(parents=True, exist_ok=True)
    timeout = int(args.get("timeout") or 15)
    backend = (os.environ.get("UAP_SHELL_BACKEND") or "local").strip().lower()
    if backend == "docker":
        # Opt-in isolated container with workspace bind-mount (read-write).
        image = os.environ.get("UAP_SHELL_DOCKER_IMAGE") or "python:3.12-alpine"
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "-v",
            f"{cwd}:/work",
            "-w",
            "/work",
            image,
            *parts,
        ]
        try:
            proc = subprocess.run(  # noqa: S603
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 5,
                shell=False,
            )
        except FileNotFoundError:
            return {"ok": False, "error": "docker binary not found on host"}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {
            "ok": proc.returncode == 0,
            "exitCode": proc.returncode,
            "stdout": (proc.stdout or "")[:8000],
            "stderr": (proc.stderr or "")[:2000],
            "cwd": str(cwd),
            "backend": "docker",
            "image": image,
        }
    try:
        proc = subprocess.run(  # noqa: S603 — allowlisted argv
            parts,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {
        "ok": proc.returncode == 0,
        "exitCode": proc.returncode,
        "stdout": (proc.stdout or "")[:8000],
        "stderr": (proc.stderr or "")[:2000],
        "cwd": str(cwd),
        "backend": "local",
    }


def tool_browser_navigate(args: dict[str, Any]) -> dict[str, Any]:
    """Lightweight browser: fetch page + extract title/links (Playwright optional)."""
    url = str(args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "url must start with http(s)://"}
    # Prefer playwright if installed
    try:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            title = page.title()
            text = page.inner_text("body")[:6000]
            links = []
            for a in page.query_selector_all("a[href]")[:20]:
                href = a.get_attribute("href") or ""
                links.append({"text": (a.inner_text() or "")[:80], "href": href})
            browser.close()
            return {"ok": True, "engine": "playwright", "url": url, "title": title, "text": text, "links": links}
    except Exception:
        pass
    try:
        html = _http_get(url, timeout=20, max_bytes=300_000)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    title_m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else ""
    links = []
    for m in re.finditer(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html):
        href, label = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        links.append({"text": re.sub(r"\s+", " ", label).strip()[:80], "href": href})
        if len(links) >= 20:
            break
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()[:6000]
    return {
        "ok": True,
        "engine": "fetch",
        "url": url,
        "title": title,
        "text": text,
        "links": links,
    }


def tool_browser_snapshot(args: dict[str, Any]) -> dict[str, Any]:
    """Alias for navigate — returns readable snapshot."""
    return tool_browser_navigate(args)


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
        "name": "shell_exec",
        "description": (
            "Run allowlisted shell command inside agent workspace (ls/cat/python/git/…). "
            "If needsApproval is returned, re-call with approved=true after user consent."
        ),
        "parameters": {"command": "string", "timeout": "int", "approved": "bool"},
    },
    {
        "name": "browser_navigate",
        "description": "Open a URL and return title, text, links (Playwright if available, else fetch).",
        "parameters": {"url": "string"},
    },
    {
        "name": "browser_snapshot",
        "description": "Readable snapshot of a page URL.",
        "parameters": {"url": "string"},
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
        "name": "memory_search",
        "description": "Full-text search across Decision Memory + recent session turns.",
        "parameters": {"query": "string", "limit": "int"},
    },
    {
        "name": "delegate_task",
        "description": "Spawn a short sub-ask (no nested tools) for a focused sub-question.",
        "parameters": {"task": "string"},
    },
    {
        "name": "parallel_delegate",
        "description": "Run up to 3 sub-asks in parallel (no nested tools each).",
        "parameters": {"tasks": "list[string]"},
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
    {
        "name": "skill_hub_list",
        "description": "List skills published to the local Skill Hub.",
        "parameters": {},
    },
    {
        "name": "skill_hub_publish",
        "description": "Publish a skill to the Skill Hub (ClawHub-like).",
        "parameters": {"name": "string", "body": "string", "tags": "list"},
    },
    {
        "name": "skill_hub_install",
        "description": "Install a hub skill into the local skill store.",
        "parameters": {"skillId": "string"},
    },
]


class AgentToolbelt:
    def __init__(
        self,
        *,
        memory: Any = None,
        skills: Any = None,
        workspace: Path | str | None = None,
        sessions: Any = None,
        delegate_fn: Callable[[str], dict[str, Any]] | None = None,
        skill_hub: Any = None,
        fts: Any = None,
    ) -> None:
        self.memory = memory
        self.skills = skills
        self.sessions = sessions
        self.skill_hub = skill_hub
        self.fts = fts
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self._delegate_fn = delegate_fn
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "web_search": tool_web_search,
            "web_fetch": tool_web_fetch,
            "calculator": tool_calculator,
            "code_exec": tool_code_exec,
            "shell_exec": self._shell_exec,
            "browser_navigate": tool_browser_navigate,
            "browser_snapshot": tool_browser_snapshot,
            "datetime_now": tool_datetime_now,
            "workspace_list": self._workspace_list,
            "workspace_read": self._workspace_read,
            "workspace_write": self._workspace_write,
            "memory_query": self._memory_query,
            "memory_search": self._memory_search,
            "delegate_task": self._delegate_task,
            "parallel_delegate": self._parallel_delegate,
            "skill_list": self._skill_list,
            "skill_get": self._skill_get,
            "skill_save": self._skill_save,
            "skill_hub_list": self._skill_hub_list,
            "skill_hub_publish": self._skill_hub_publish,
            "skill_hub_install": self._skill_hub_install,
        }

    def specs(self) -> list[dict[str, Any]]:
        return list(TOOL_SPECS)

    def call(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        fn = self._handlers.get(name)
        if not fn:
            return {"ok": False, "error": f"unknown tool: {name}"}
        timeout = 25
        if name in {"web_search", "web_fetch", "browser_navigate", "browser_snapshot"}:
            timeout = 25
        if name == "code_exec":
            timeout = 5
        if name == "shell_exec":
            timeout = 20
        if name == "parallel_delegate":
            timeout = 90
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                fut = pool.submit(fn, dict(args or {}))
                return fut.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return {"ok": False, "error": f"tool timeout after {timeout}s", "tool": name}
        except Exception as e:
            return {"ok": False, "error": str(e), "tool": name}

    def _shell_exec(self, args: dict[str, Any]) -> dict[str, Any]:
        cwd = (self.workspace / ".uap" / "agent-workspace").resolve()
        return tool_shell_exec(args, cwd=cwd)

    def _parallel_delegate(self, args: dict[str, Any]) -> dict[str, Any]:
        tasks = args.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            return {"ok": False, "error": "tasks list required"}
        if self._delegate_fn is None:
            return {"ok": False, "error": "delegate not configured"}
        cleaned = [str(t).strip() for t in tasks if str(t).strip()][:3]
        results: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futs = {pool.submit(self._delegate_fn, t): t for t in cleaned}
            for fut in concurrent.futures.as_completed(futs):
                task = futs[fut]
                try:
                    out = fut.result()
                    results.append(
                        {
                            "task": task,
                            "ok": True,
                            "answer": out.get("answer"),
                            "dqs": out.get("dqs"),
                            "decisionId": out.get("decisionId"),
                        }
                    )
                except Exception as e:
                    results.append({"task": task, "ok": False, "error": str(e)})
        return {"ok": True, "results": results}

    def _skill_hub_list(self, _args: dict[str, Any]) -> dict[str, Any]:
        if self.skill_hub is None:
            return {"ok": False, "error": "skill hub not configured"}
        return {"ok": True, "skills": self.skill_hub.list_public()}

    def _skill_hub_publish(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.skill_hub is None:
            return {"ok": False, "error": "skill hub not configured"}
        try:
            row = self.skill_hub.publish(
                name=str(args.get("name") or ""),
                body=str(args.get("body") or ""),
                tags=list(args.get("tags") or []) if isinstance(args.get("tags"), list) else [],
                author=str(args.get("author") or "agent"),
            )
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "skill": row}

    def _skill_hub_install(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.skill_hub is None or self.skills is None:
            return {"ok": False, "error": "skill hub/store not configured"}
        sid = str(args.get("skillId") or "")
        try:
            installed = self.skill_hub.install_to_store(sid, skills=self.skills)
        except KeyError:
            return {"ok": False, "error": f"unknown hub skill: {sid}"}
        return {"ok": True, "installed": installed}

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

    def _memory_search(self, args: dict[str, Any]) -> dict[str, Any]:
        q = str(args.get("query") or "").strip().lower()
        if not q:
            return {"ok": False, "error": "query required"}
        limit = max(1, min(int(args.get("limit") or 8), 20))
        hits: list[dict[str, Any]] = []
        if self.memory is not None:
            for r in self.memory.query(limit=50):
                blob = " ".join(
                    [
                        str(r.get("action") or ""),
                        str(r.get("lesson") or ""),
                        str((r.get("context") or {}).get("question") or ""),
                        " ".join(str(x) for x in (r.get("reasoning") or [])[:2]),
                    ]
                ).lower()
                if q in blob or any(tok and tok in blob for tok in q.split()):
                    hits.append(
                        {
                            "source": "decision_memory",
                            "decisionId": r.get("decisionId"),
                            "dqs": r.get("dqs"),
                            "lesson": r.get("lesson"),
                            "question": (r.get("context") or {}).get("question"),
                        }
                    )
                if len(hits) >= limit:
                    break
        if self.sessions is not None and len(hits) < limit:
            root = Path(self.workspace) / ".uap" / "agent-sessions"
            if root.exists():
                for path in sorted(root.glob("*.json"), reverse=True)[:30]:
                    try:
                        row = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    for m in (row.get("messages") or [])[-20:]:
                        content = str(m.get("content") or "")
                        if q in content.lower():
                            hits.append(
                                {
                                    "source": "session",
                                    "sessionId": row.get("sessionId"),
                                    "role": m.get("role"),
                                    "snippet": content[:240],
                                }
                            )
                            if len(hits) >= limit:
                                break
                    if len(hits) >= limit:
                        break
        if self.fts is not None and len(hits) < limit:
            for h in self.fts.search(q, limit=limit - len(hits)):
                hits.append(h)
        return {"ok": True, "query": q, "hits": hits[:limit]}

    def _delegate_task(self, args: dict[str, Any]) -> dict[str, Any]:
        task = str(args.get("task") or args.get("prompt") or "").strip()
        if not task:
            return {"ok": False, "error": "task required"}
        if self._delegate_fn is None:
            return {"ok": False, "error": "delegate not configured"}
        try:
            out = self._delegate_fn(task)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {
            "ok": True,
            "answer": out.get("answer"),
            "dqs": out.get("dqs"),
            "decisionId": out.get("decisionId"),
        }

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
