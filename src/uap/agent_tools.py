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
    if backend == "ssh":
        # Opt-in remote shell: ssh user@host -- allowlisted command (Hermes SSH backend v0)
        host = (os.environ.get("UAP_SHELL_SSH_HOST") or "").strip()
        user = (os.environ.get("UAP_SHELL_SSH_USER") or "").strip()
        if not host:
            return {"ok": False, "error": "UAP_SHELL_SSH_HOST not set"}
        target = f"{user}@{host}" if user else host
        ssh_bin = os.environ.get("UAP_SHELL_SSH_BIN") or "ssh"
        remote = " ".join(shlex.quote(p) for p in parts)
        ssh_cmd = [ssh_bin, "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", target, remote]
        try:
            proc = subprocess.run(  # noqa: S603
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 5,
                shell=False,
            )
        except FileNotFoundError:
            return {"ok": False, "error": "ssh binary not found"}
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
            "backend": "ssh",
            "host": host,
        }
    if backend == "modal":
        from .shell_remote import exec_modal

        remote = " ".join(shlex.quote(p) for p in parts)
        return exec_modal(command=remote, timeout=timeout, cwd=str(cwd))
    if backend == "daytona":
        from .shell_remote import exec_daytona

        remote = " ".join(shlex.quote(p) for p in parts)
        return exec_daytona(command=remote, timeout=timeout, cwd=str(cwd))
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


def tool_browser_navigate(args: dict[str, Any], *, workspace: Path | None = None) -> dict[str, Any]:
    """Navigate — uses persistent Playwright session when available, else one-shot/fetch."""
    url = str(args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "url must start with http(s)://"}
    ws = Path(workspace) if workspace else Path.cwd()
    try:
        from .browser_session import get_browser_session

        return get_browser_session(ws).navigate(url)
    except Exception:
        pass
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
            return {
                "ok": True,
                "engine": "playwright-oneshot",
                "url": url,
                "title": title,
                "text": text,
                "links": links,
            }
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
        "hint": "Install playwright for click/type computer-use",
    }


def tool_browser_snapshot(args: dict[str, Any], *, workspace: Path | None = None) -> dict[str, Any]:
    ws = Path(workspace) if workspace else Path.cwd()
    try:
        from .browser_session import get_browser_session

        return get_browser_session(ws).snapshot()
    except Exception:
        return tool_browser_navigate(args, workspace=ws)


def tool_browser_click(args: dict[str, Any], *, workspace: Path | None = None) -> dict[str, Any]:
    ws = Path(workspace) if workspace else Path.cwd()
    try:
        from .browser_session import get_browser_session

        return get_browser_session(ws).click(str(args.get("selector") or ""))
    except Exception as e:
        return {"ok": False, "error": str(e), "hint": "Requires playwright + prior browser_navigate"}


def tool_browser_type(args: dict[str, Any], *, workspace: Path | None = None) -> dict[str, Any]:
    ws = Path(workspace) if workspace else Path.cwd()
    try:
        from .browser_session import get_browser_session

        return get_browser_session(ws).type_text(
            str(args.get("selector") or ""),
            str(args.get("text") or ""),
            clear=args.get("clear", True) is not False,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_browser_wait(args: dict[str, Any], *, workspace: Path | None = None) -> dict[str, Any]:
    ws = Path(workspace) if workspace else Path.cwd()
    try:
        from .browser_session import get_browser_session

        return get_browser_session(ws).wait(
            selector=str(args.get("selector") or "") or None,
            ms=int(args.get("ms") or 1000),
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_browser_screenshot(args: dict[str, Any], *, workspace: Path | None = None) -> dict[str, Any]:
    ws = Path(workspace) if workspace else Path.cwd()
    try:
        from .browser_session import get_browser_session

        return get_browser_session(ws).screenshot(name=str(args.get("name") or "browser.png"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_browser_vision(args: dict[str, Any], *, workspace: Path | None = None, belt: Any = None) -> dict[str, Any]:
    """Screenshot current browser page (or URL) and describe with vision model (BYOK)."""
    import base64

    ws = Path(workspace) if workspace else Path.cwd()
    question = str(args.get("question") or "Describe this page and list actionable elements.").strip()
    url = str(args.get("url") or "").strip()
    if url:
        nav = tool_browser_navigate({"url": url}, workspace=ws)
        if not nav.get("ok"):
            return nav
    shot = tool_browser_screenshot({"name": str(args.get("name") or "vision.png")}, workspace=ws)
    if not shot.get("ok"):
        return shot
    path = Path(str(shot.get("path") or ""))
    if not path.is_file():
        return {"ok": False, "error": "screenshot missing", "shot": shot}
    raw = path.read_bytes()
    if len(raw) > 4_000_000:
        return {"ok": False, "error": "screenshot too large for vision"}
    b64 = base64.standard_b64encode(raw).decode("ascii")
    data_url = f"data:image/png;base64,{b64}"
    if belt is not None and hasattr(belt, "_vision_describe"):
        vis = belt._vision_describe({"url": data_url, "question": question})
    else:
        return {
            "ok": False,
            "error": "vision requires AgentToolbelt with BYOK credentials",
            "screenshot": str(path),
        }
    if not vis.get("ok"):
        return {**vis, "screenshot": str(path)}
    return {
        "ok": True,
        "description": vis.get("description"),
        "screenshot": str(path),
        "pageUrl": shot.get("url"),
        "model": vis.get("model"),
    }


def tool_execute_code(args: dict[str, Any], *, call_tool: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Hermes RPC: run Python that calls call_tool(name, args) for nested tool use."""
    from .agent_rpc import run_execute_code

    code = str(args.get("code") or args.get("source") or "").strip()
    if call_tool is None:
        return {"ok": False, "error": "execute_code RPC not configured"}
    max_calls = int(args.get("maxCalls") or 3)
    return run_execute_code(code, call_tool, max_calls=max_calls)


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


def tool_http_request(args: dict[str, Any]) -> dict[str, Any]:
    """Allowlisted HTTP client for public APIs (Hermes tool parity v0)."""
    url = str(args.get("url") or "").strip()
    method = str(args.get("method") or "GET").upper()
    if not url.startswith("https://"):
        return {"ok": False, "error": "only https:// URLs allowed"}
    if method not in {"GET", "POST", "HEAD"}:
        return {"ok": False, "error": "method must be GET|POST|HEAD"}
    body = args.get("body")
    data = None
    headers = {"User-Agent": "narna-agent/0.2 (+https://narna.org)"}
    if body is not None and method == "POST":
        raw = body if isinstance(body, (bytes, bytearray)) else str(body).encode("utf-8")
        if len(raw) > 50_000:
            return {"ok": False, "error": "body too large"}
        data = raw
        headers["Content-Type"] = str(args.get("contentType") or "application/json")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            text = resp.read(100_000).decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": getattr(resp, "status", 200),
                "body": text[:20000],
            }
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:2000]
        return {"ok": False, "status": e.code, "error": detail}
    except Exception as e:
        return {"ok": False, "error": str(e)}


_ENV_ALLOW = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "USERNAME",
        "LANG",
        "TZ",
        "TERM",
        "UAP_SHELL_BACKEND",
        "UAP_BROWSER_ENABLED",
        "NARNA_ENV",
        "NODE_ENV",
    }
)


def tool_grep_workspace(args: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    """Search text files under agent-workspace (ripgrep if present, else Python)."""
    import re
    import subprocess

    pattern = str(args.get("pattern") or args.get("query") or "").strip()
    if not pattern:
        return {"ok": False, "error": "pattern required"}
    if len(pattern) > 200:
        return {"ok": False, "error": "pattern too long"}
    base = (workspace / ".uap" / "agent-workspace").resolve()
    base.mkdir(parents=True, exist_ok=True)
    rel = str(args.get("path") or ".").strip() or "."
    root = base if rel in {".", ""} else _safe_workspace_path(workspace, rel)
    if root is None or not root.exists():
        return {"ok": False, "error": "path not found"}
    limit = min(50, int(args.get("limit") or 20))
    # Prefer ripgrep
    try:
        proc = subprocess.run(  # noqa: S603
            ["rg", "-n", "--max-count", str(limit), "-e", pattern, str(root)],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
        if proc.returncode in {0, 1}:
            lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()][:limit]
            return {"ok": True, "matches": lines, "engine": "rg", "n": len(lines)}
    except FileNotFoundError:
        pass
    except Exception:
        pass
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return {"ok": False, "error": f"invalid regex: {e}"}
    matches: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 500_000:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp3", ".ogg", ".bin"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                rel_p = path.relative_to(base) if path.is_relative_to(base) else path.name
                matches.append(f"{rel_p}:{i}:{line.strip()[:200]}")
                if len(matches) >= limit:
                    return {"ok": True, "matches": matches, "engine": "python", "n": len(matches)}
    return {"ok": True, "matches": matches, "engine": "python", "n": len(matches)}


def tool_json_query(args: dict[str, Any]) -> dict[str, Any]:
    """jq-lite: walk dotted path with optional [index] segments."""
    import re

    raw = args.get("json")
    if raw is None:
        return {"ok": False, "error": "json required"}
    if isinstance(raw, (dict, list)):
        data: Any = raw
    else:
        try:
            data = json.loads(str(raw))
        except Exception as e:
            return {"ok": False, "error": f"invalid json: {e}"}
    path = str(args.get("path") or args.get("query") or "").strip()
    if not path or path == ".":
        return {"ok": True, "value": data}
    cur: Any = data
    for part in path.replace("[", ".[").split("."):
        if not part:
            continue
        m = re.fullmatch(r"\[(\d+)\]", part)
        if m:
            idx = int(m.group(1))
            if not isinstance(cur, list) or idx >= len(cur):
                return {"ok": False, "error": f"index out of range: {part}"}
            cur = cur[idx]
            continue
        if not isinstance(cur, dict) or part not in cur:
            return {"ok": False, "error": f"key not found: {part}"}
        cur = cur[part]
    return {"ok": True, "value": cur, "path": path}


def tool_uuid(args: dict[str, Any] | None = None) -> dict[str, Any]:
    import uuid as _uuid

    args = args or {}
    n = min(10, max(1, int(args.get("n") or 1)))
    ids = [str(_uuid.uuid4()) for _ in range(n)]
    return {"ok": True, "uuid": ids[0], "uuids": ids}


def tool_hash(args: dict[str, Any]) -> dict[str, Any]:
    import hashlib

    text = args.get("text")
    if text is None:
        return {"ok": False, "error": "text required"}
    raw = str(text).encode("utf-8")
    if len(raw) > 200_000:
        return {"ok": False, "error": "text too large"}
    algo = str(args.get("algo") or "sha256").lower()
    if algo not in {"sha256", "sha1", "md5"}:
        return {"ok": False, "error": "algo must be sha256|sha1|md5"}
    h = hashlib.new(algo, raw).hexdigest()
    return {"ok": True, "algo": algo, "hex": h, "bytes": len(raw)}


def tool_env_get(args: dict[str, Any]) -> dict[str, Any]:
    key = str(args.get("key") or "").strip()
    if not key:
        return {"ok": False, "error": "key required", "allowlist": sorted(_ENV_ALLOW)}
    if key not in _ENV_ALLOW:
        return {"ok": False, "error": f"key not allowlisted: {key}", "allowlist": sorted(_ENV_ALLOW)}
    return {"ok": True, "key": key, "value": os.environ.get(key), "set": key in os.environ}


def tool_read_url_head(args: dict[str, Any]) -> dict[str, Any]:
    url = str(args.get("url") or "").strip()
    if not url.startswith("https://"):
        return {"ok": False, "error": "https URL required"}
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "narna-agent/0.2 (+https://narna.org)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return {
                "ok": True,
                "status": getattr(resp, "status", 200),
                "url": url,
                "contentType": headers.get("content-type"),
                "contentLength": headers.get("content-length"),
                "headers": {k: headers[k] for k in list(headers)[:20]},
            }
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": str(e.reason)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def tool_text_to_speech(args: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    """OpenAI TTS BYOK → workspace/.uap/audio/out.mp3 (Hermes gap P6)."""
    text = str(args.get("text") or "").strip()
    if not text:
        return {"ok": False, "error": "text required"}
    if len(text) > 4000:
        return {"ok": False, "error": "text too long (max 4000)"}
    key = (
        str(args.get("apiKey") or "").strip()
        or (os.environ.get("UAP_OPENAI_API_KEY") or "").strip()
        or (os.environ.get("OPENAI_API_KEY") or "").strip()
    )
    if not key:
        return {"ok": False, "needsKey": True, "error": "OpenAI API key required for TTS (BYOK)"}
    model = str(args.get("model") or "tts-1").strip()
    voice = str(args.get("voice") or "alloy").strip()
    out_dir = workspace / ".uap" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = str(args.get("name") or "out.mp3").strip().replace("..", "")
    if not name.endswith(".mp3"):
        name = f"{name}.mp3"
    dest = out_dir / Path(name).name
    body = json.dumps({"model": model, "input": text, "voice": voice}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "narna-agent/0.2",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        return {"ok": False, "error": f"TTS HTTP {e.code}: {detail}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if len(audio) < 32:
        return {"ok": False, "error": "empty audio response"}
    dest.write_bytes(audio)
    return {
        "ok": True,
        "path": str(dest.relative_to(workspace)) if dest.is_relative_to(workspace) else str(dest),
        "bytes": len(audio),
        "model": model,
        "voice": voice,
    }


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
        "description": "Open a URL in persistent browser session (Playwright) or fetch fallback.",
        "parameters": {"url": "string"},
    },
    {
        "name": "browser_snapshot",
        "description": "Readable snapshot of the current browser page (or URL).",
        "parameters": {"url": "string"},
    },
    {
        "name": "browser_click",
        "description": "Click a CSS selector in the persistent browser session (computer-use).",
        "parameters": {"selector": "string"},
    },
    {
        "name": "browser_type",
        "description": "Type text into a CSS selector (computer-use).",
        "parameters": {"selector": "string", "text": "string", "clear": "bool"},
    },
    {
        "name": "browser_wait",
        "description": "Wait for selector or milliseconds in browser session.",
        "parameters": {"selector": "string", "ms": "int"},
    },
    {
        "name": "browser_screenshot",
        "description": "Save a screenshot of the current browser page to workspace.",
        "parameters": {"name": "string"},
    },
    {
        "name": "browser_vision",
        "description": "Screenshot + vision describe (computer-use loop). Optional url to navigate first.",
        "parameters": {"url": "string", "question": "string"},
    },
    {
        "name": "execute_code",
        "description": (
            "Run Python with call_tool(name, args) to chain tools in one turn (Hermes RPC). "
            "Set result=... to return."
        ),
        "parameters": {"code": "string", "maxCalls": "int"},
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
    {
        "name": "http_request",
        "description": "HTTP GET/POST to a public https URL (size-limited). Use for APIs.",
        "parameters": {"url": "string", "method": "string", "body": "string"},
    },
    {
        "name": "image_gen",
        "description": "Generate an image via OpenRouter/OpenAI-compatible image API (BYOK).",
        "parameters": {"prompt": "string", "model": "string"},
    },
    {
        "name": "vision_describe",
        "description": "Describe an image URL with a vision-capable chat model (BYOK).",
        "parameters": {"url": "string", "question": "string"},
    },
    {
        "name": "schedule_job",
        "description": "Schedule an Ask job with natural language cron (Hermes-like).",
        "parameters": {"schedule": "string", "prompt": "string"},
    },
    {
        "name": "jobs_list",
        "description": "List scheduled agent jobs.",
        "parameters": {},
    },
    {
        "name": "profile_get",
        "description": "Read user profile notes learned from conversation.",
        "parameters": {},
    },
    {
        "name": "profile_set",
        "description": "Set a user profile note key/value.",
        "parameters": {"key": "string", "value": "string"},
    },
    {
        "name": "grep_workspace",
        "description": "Search files in agent-workspace by regex (ripgrep or Python fallback).",
        "parameters": {"pattern": "string", "path": "string", "limit": "number"},
    },
    {
        "name": "json_query",
        "description": "jq-lite: extract a value from JSON via dotted path (e.g. a.b[0].c).",
        "parameters": {"json": "string", "path": "string"},
    },
    {
        "name": "uuid",
        "description": "Generate one or more UUID4 strings.",
        "parameters": {"n": "number"},
    },
    {
        "name": "hash",
        "description": "Hash text (sha256|sha1|md5) and return hex digest.",
        "parameters": {"text": "string", "algo": "string"},
    },
    {
        "name": "env_get",
        "description": "Read an allowlisted environment variable (no secrets).",
        "parameters": {"key": "string"},
    },
    {
        "name": "read_url_head",
        "description": "HTTP HEAD on an https URL — status, content-type, length.",
        "parameters": {"url": "string"},
    },
    {
        "name": "skill_export_md",
        "description": "Export a saved skill as agentskills.io SKILL.md markdown.",
        "parameters": {"skillId": "string"},
    },
    {
        "name": "skill_import_md",
        "description": "Import a SKILL.md markdown string and save as a skill.",
        "parameters": {"markdown": "string"},
    },
    {
        "name": "text_to_speech",
        "description": "OpenAI TTS (BYOK) → save mp3 under .uap/audio/.",
        "parameters": {"text": "string", "voice": "string", "name": "string", "apiKey": "string"},
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
        jobs: Any = None,
        llm_api_key: str | None = None,
        llm_provider: str | None = None,
        llm_base_url: str | None = None,
    ) -> None:
        self.memory = memory
        self.skills = skills
        self.sessions = sessions
        self.skill_hub = skill_hub
        self.fts = fts
        self.jobs = jobs
        self.llm_api_key = llm_api_key
        self.llm_provider = (llm_provider or "").lower() or None
        self.llm_base_url = llm_base_url
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self._delegate_fn = delegate_fn
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "web_search": tool_web_search,
            "web_fetch": tool_web_fetch,
            "calculator": tool_calculator,
            "code_exec": tool_code_exec,
            "shell_exec": self._shell_exec,
            "browser_navigate": self._browser_navigate,
            "browser_snapshot": self._browser_snapshot,
            "browser_click": self._browser_click,
            "browser_type": self._browser_type,
            "browser_wait": self._browser_wait,
            "browser_screenshot": self._browser_screenshot,
            "browser_vision": self._browser_vision,
            "execute_code": self._execute_code,
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
            "http_request": tool_http_request,
            "image_gen": self._image_gen,
            "vision_describe": self._vision_describe,
            "schedule_job": self._schedule_job,
            "jobs_list": self._jobs_list,
            "profile_get": self._profile_get,
            "profile_set": self._profile_set,
            "grep_workspace": self._grep_workspace,
            "json_query": tool_json_query,
            "uuid": tool_uuid,
            "hash": tool_hash,
            "env_get": tool_env_get,
            "read_url_head": tool_read_url_head,
            "skill_export_md": self._skill_export_md,
            "skill_import_md": self._skill_import_md,
            "text_to_speech": self._text_to_speech,
        }

    def specs(self) -> list[dict[str, Any]]:
        return list(TOOL_SPECS)

    def call(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        fn = self._handlers.get(name)
        if not fn:
            return {"ok": False, "error": f"unknown tool: {name}"}
        timeout = 25
        if name in {
            "web_search",
            "web_fetch",
            "browser_navigate",
            "browser_snapshot",
            "browser_click",
            "browser_type",
            "browser_wait",
            "browser_screenshot",
            "browser_vision",
        }:
            timeout = 30
        if name == "execute_code":
            timeout = 20
        if name == "code_exec":
            timeout = 5
        if name == "shell_exec":
            timeout = 20
        if name in {"image_gen", "vision_describe", "text_to_speech"}:
            timeout = 90
        if name == "http_request":
            timeout = 30
        if name in {"grep_workspace", "read_url_head"}:
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

    def _browser_navigate(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_browser_navigate(args, workspace=self.workspace)

    def _browser_snapshot(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_browser_snapshot(args, workspace=self.workspace)

    def _browser_click(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_browser_click(args, workspace=self.workspace)

    def _browser_type(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_browser_type(args, workspace=self.workspace)

    def _browser_wait(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_browser_wait(args, workspace=self.workspace)

    def _browser_screenshot(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_browser_screenshot(args, workspace=self.workspace)

    def _browser_vision(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_browser_vision(args, workspace=self.workspace, belt=self)

    def _execute_code(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_execute_code(args, call_tool=self.call)

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

    def _llm_creds(self) -> tuple[str, str, str]:
        key = (
            self.llm_api_key
            or os.environ.get("UAP_OPENROUTER_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("UAP_OPENAI_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        ).strip()
        if self.llm_provider:
            provider = self.llm_provider
        elif os.environ.get("UAP_OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY"):
            provider = "openrouter"
        elif key:
            provider = "openai"
        else:
            provider = "mock"
        base = (self.llm_base_url or "").rstrip("/")
        if not base:
            if provider == "openrouter":
                base = "https://openrouter.ai/api/v1"
            elif provider == "openai":
                base = "https://api.openai.com/v1"
            else:
                base = ""
        return key, provider, base

    def _image_gen(self, args: dict[str, Any]) -> dict[str, Any]:
        prompt = str(args.get("prompt") or "").strip()
        if not prompt:
            return {"ok": False, "error": "prompt required"}
        key, provider, base = self._llm_creds()
        if not key or not base:
            return {"ok": False, "error": "BYOK API key required for image_gen"}
        model = str(args.get("model") or "google/gemini-2.5-flash-image-preview")
        # OpenRouter image via chat completions with modalities
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if provider == "openrouter":
            body["modalities"] = ["image", "text"]
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "User-Agent": "narna-agent/0.2",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"ok": False, "error": str(e)}
        msg = ((data.get("choices") or [{}])[0].get("message") or {})
        images = msg.get("images") or []
        urls = []
        for im in images:
            u = (im.get("image_url") or {}).get("url") if isinstance(im, dict) else None
            if u:
                urls.append(u)
        return {
            "ok": True,
            "provider": provider,
            "model": model,
            "text": str(msg.get("content") or "")[:2000],
            "images": urls[:4],
        }

    def _vision_describe(self, args: dict[str, Any]) -> dict[str, Any]:
        url = str(args.get("url") or "").strip()
        question = str(args.get("question") or "Describe this image briefly.").strip()
        if not url.startswith(("http://", "https://", "data:")):
            return {"ok": False, "error": "url must be http(s) or data:image"}
        key, provider, base = self._llm_creds()
        if not key or not base:
            return {"ok": False, "error": "BYOK API key required for vision_describe"}
        model = str(
            args.get("model")
            or ("openai/gpt-4o-mini" if provider == "openrouter" else "gpt-4o-mini")
        )
        content = [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": url}},
        ]
        body = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 600,
        }
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "User-Agent": "narna-agent/0.2",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"ok": False, "error": str(e)}
        text = str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
        return {"ok": True, "description": text[:4000], "model": model, "provider": provider}

    def _schedule_job(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.jobs is None:
            return {"ok": False, "error": "jobs not configured"}
        from .nl_cron import parse_nl_schedule

        schedule = str(args.get("schedule") or args.get("when") or "").strip()
        prompt = str(args.get("prompt") or "").strip()
        if not schedule and not prompt:
            return {"ok": False, "error": "schedule or prompt required"}
        text = schedule if schedule else prompt
        if prompt and schedule and prompt not in schedule:
            text = f"{schedule} {prompt}"
        try:
            parsed = parse_nl_schedule(text)
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        try:
            row = self.jobs.create(
                prompt=str(parsed.get("prompt") or prompt or text),
                every_minutes=parsed.get("everyMinutes"),
                run_at=parsed.get("runAt"),
                channel=str(parsed.get("channel") or "job"),
                deliver_to=str(parsed.get("deliverTo") or "") or None,
            )
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "job": row, "parsed": parsed}

    def _jobs_list(self, _args: dict[str, Any]) -> dict[str, Any]:
        if self.jobs is None:
            return {"ok": False, "error": "jobs not configured"}
        return {"ok": True, "jobs": self.jobs.list_jobs()}

    def _profile_get(self, _args: dict[str, Any]) -> dict[str, Any]:
        if self.fts is None:
            return {"ok": False, "error": "profile store not configured"}
        return {"ok": True, "profile": self.fts.get_profile()}

    def _profile_set(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.fts is None:
            return {"ok": False, "error": "profile store not configured"}
        key = str(args.get("key") or "").strip()
        value = str(args.get("value") or "").strip()
        if not key or not value:
            return {"ok": False, "error": "key and value required"}
        if len(key) > 64 or len(value) > 2000:
            return {"ok": False, "error": "key/value too long"}
        self.fts.set_profile(key, value)
        return {"ok": True, "profile": self.fts.get_profile()}

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

    def _skill_export_md(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.skills is None:
            return {"ok": False, "error": "skills not configured"}
        from .skill_md import skill_to_markdown

        sid = str(args.get("skillId") or args.get("id") or "")
        row = self.skills.get(sid)
        if not row:
            return {"ok": False, "error": f"unknown skill: {sid}"}
        md = skill_to_markdown(row)
        return {"ok": True, "skillId": sid, "markdown": md}

    def _skill_import_md(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.skills is None:
            return {"ok": False, "error": "skills not configured"}
        from .skill_md import markdown_to_skill

        md = str(args.get("markdown") or args.get("md") or "").strip()
        if not md:
            return {"ok": False, "error": "markdown required"}
        parsed = markdown_to_skill(md)
        name = str(parsed.get("name") or "imported")
        body = str(parsed.get("body") or "")
        tags = parsed.get("tags") if isinstance(parsed.get("tags"), list) else []
        if not body:
            return {"ok": False, "error": "empty skill body"}
        row = self.skills.save(name=name, body=body, tags=[str(t) for t in tags])
        return {"ok": True, "skill": row}

    def _grep_workspace(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_grep_workspace(args, workspace=self.workspace)

    def _text_to_speech(self, args: dict[str, Any]) -> dict[str, Any]:
        return tool_text_to_speech(args, workspace=self.workspace)
