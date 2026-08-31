"""Persistent Playwright browser session — Hermes-like computer-use v0."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any


_lock = threading.Lock()
_sessions: dict[str, Any] = {}


class BrowserSession:
    """One headless Chromium context per workspace key."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self._pw = None
        self._browser = None
        self._page = None
        self._engine = "none"

    def _ensure(self) -> None:
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as e:
            raise RuntimeError(
                "playwright not installed — pip install playwright && playwright install chromium"
            ) from e
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._page = self._browser.new_page()
        self._engine = "playwright"

    def close(self) -> None:
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        self._page = None
        self._browser = None
        self._pw = None

    def navigate(self, url: str, *, timeout_ms: int = 20000) -> dict[str, Any]:
        self._ensure()
        assert self._page is not None
        self._page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        self._ensure()
        assert self._page is not None
        title = self._page.title()
        url = self._page.url
        text = self._page.inner_text("body")[:6000]
        links = []
        for a in self._page.query_selector_all("a[href]")[:25]:
            links.append(
                {
                    "text": (a.inner_text() or "")[:80],
                    "href": a.get_attribute("href") or "",
                }
            )
        return {
            "ok": True,
            "engine": self._engine,
            "url": url,
            "title": title,
            "text": text,
            "links": links,
        }

    def click(self, selector: str, *, timeout_ms: int = 10000) -> dict[str, Any]:
        self._ensure()
        assert self._page is not None
        sel = (selector or "").strip()
        if not sel:
            return {"ok": False, "error": "selector required"}
        self._page.click(sel, timeout=timeout_ms)
        return {"ok": True, "action": "click", "selector": sel, **self.snapshot()}

    def type_text(
        self,
        selector: str,
        text: str,
        *,
        clear: bool = True,
        timeout_ms: int = 10000,
    ) -> dict[str, Any]:
        self._ensure()
        assert self._page is not None
        sel = (selector or "").strip()
        if not sel:
            return {"ok": False, "error": "selector required"}
        if clear:
            self._page.fill(sel, text or "", timeout=timeout_ms)
        else:
            self._page.type(sel, text or "", timeout=timeout_ms)
        return {
            "ok": True,
            "action": "type",
            "selector": sel,
            "chars": len(text or ""),
            **self.snapshot(),
        }

    def wait(self, *, selector: str | None = None, ms: int = 1000) -> dict[str, Any]:
        self._ensure()
        assert self._page is not None
        if selector:
            self._page.wait_for_selector(selector, timeout=max(ms, 1000))
        else:
            self._page.wait_for_timeout(min(max(ms, 0), 15000))
        return {"ok": True, "action": "wait", **self.snapshot()}

    def screenshot(self, *, name: str = "browser.png") -> dict[str, Any]:
        self._ensure()
        assert self._page is not None
        out_dir = (self.workspace / ".uap" / "browser").resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        safe = "".join(c for c in name if c.isalnum() or c in "._-")[:64] or "browser.png"
        if not safe.endswith(".png"):
            safe += ".png"
        path = out_dir / safe
        self._page.screenshot(path=str(path), full_page=False)
        return {
            "ok": True,
            "action": "screenshot",
            "path": str(path),
            "url": self._page.url,
            "title": self._page.title(),
        }


def get_browser_session(workspace: Path | str) -> BrowserSession:
    key = str(Path(workspace).resolve())
    with _lock:
        sess = _sessions.get(key)
        if sess is None:
            sess = BrowserSession(Path(key))
            _sessions[key] = sess
        return sess


def browser_ready() -> dict[str, Any]:
    """Probe Playwright + Chromium availability without launching a long session."""
    import os

    enabled = str(os.environ.get("UAP_BROWSER_ENABLED") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as e:
        return {
            "ready": False,
            "enabled": enabled,
            "engine": None,
            "error": f"playwright import failed: {e}",
        }
    try:
        with sync_playwright() as p:
            # executable_path raises if browser not installed
            path = p.chromium.executable_path
            return {
                "ready": True,
                "enabled": enabled,
                "engine": "playwright",
                "chromium": str(path),
            }
    except Exception as e:
        return {
            "ready": False,
            "enabled": enabled,
            "engine": "playwright",
            "error": str(e)[:300],
        }


def setup_browser(*, with_deps: bool = False) -> dict[str, Any]:
    """Install playwright + chromium (Hermes computer-use one-click setup)."""
    import subprocess
    import sys

    steps: list[str] = []
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "playwright"],
            timeout=300,
        )
        steps.append("pip playwright")
    except Exception as e:
        return {"ok": False, "error": f"pip install playwright failed: {e}", "steps": steps}
    cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
    if with_deps:
        cmd.append("--with-deps")
    try:
        subprocess.check_call(cmd, timeout=600)
        steps.append("playwright install chromium")
    except Exception as e:
        return {"ok": False, "error": f"playwright install failed: {e}", "steps": steps}
    probe = browser_ready()
    return {"ok": bool(probe.get("ready")), "steps": steps, **probe}
