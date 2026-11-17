"""Claude Code CLI auth for NARNA Desktop (MausBot-style: open browser + paste code).

Uses the installed `claude` binary (`claude auth login`). Does not store passwords.
OAuth code is submitted once to the CLI process stdin and never logged.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_URL_RE = re.compile(r"https://(?:claude\.ai|claude\.com|platform\.claude\.com)[^\s\"'<>]+", re.I)
_LOGIN_OK_RE = re.compile(r"login successful|logged in|authentication successful", re.I)


def find_claude_bin() -> str | None:
    env = (os.environ.get("NARNA_CLAUDE_BIN") or os.environ.get("CLAUDE_BIN") or "").strip()
    if env and Path(env).exists():
        return env
    return shutil.which("claude")


def credentials_paths() -> list[Path]:
    home = Path.home()
    paths = [
        home / ".claude" / ".credentials.json",
        home / ".config" / "claude" / ".credentials.json",
    ]
    cfg_dir = (os.environ.get("CLAUDE_CONFIG_DIR") or "").strip()
    if cfg_dir:
        paths.insert(0, Path(cfg_dir).expanduser() / ".credentials.json")
    # de-dupe while preserving order
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def claude_logged_in() -> bool:
    """Best-effort: credentials file or `claude auth status`."""
    for p in credentials_paths():
        try:
            if p.is_file() and p.stat().st_size > 8:
                text = p.read_text(encoding="utf-8", errors="ignore")
                if "accessToken" in text or "oauth" in text.lower() or "claudeAiOauth" in text:
                    return True
        except OSError:
            continue
    bin_path = find_claude_bin()
    if not bin_path:
        return False
    try:
        r = subprocess.run(
            [bin_path, "auth", "status"],
            capture_output=True,
            text=True,
            timeout=12,
        )
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0 and ("logged" in out.lower() or "authenticated" in out.lower() or "@" in out):
            return True
        # Some builds print JSON / "Login method"
        if r.returncode == 0 and out.strip() and "not logged" not in out.lower():
            return True
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


@dataclass
class ClaudeLoginSession:
    proc: subprocess.Popen[str] | None = None
    login_url: str | None = None
    output: str = ""
    started_at: float = field(default_factory=time.time)
    done: bool = False
    error: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def append(self, chunk: str) -> None:
        with self.lock:
            self.output += chunk
            if not self.login_url:
                m = _URL_RE.search(self.output)
                if m:
                    self.login_url = m.group(0).rstrip(").,]\"'")


_SESSION: ClaudeLoginSession | None = None
_SESSION_LOCK = threading.Lock()


def get_session() -> ClaudeLoginSession | None:
    return _SESSION


def status() -> dict[str, Any]:
    bin_path = find_claude_bin()
    logged_in = claude_logged_in() if bin_path else False
    sess = get_session()
    pending = bool(sess and sess.proc and sess.proc.poll() is None and not sess.done)
    return {
        "ok": True,
        "claudeInstalled": bool(bin_path),
        "claudeBin": bin_path,
        "loggedIn": logged_in,
        "loginPending": pending,
        "loginUrl": sess.login_url if sess else None,
        "installHint": (
            "Install Claude Code CLI first: https://code.claude.com/docs/en/setup "
            "or `npm install -g @anthropic-ai/claude-code`"
        ),
    }


def _reader(sess: ClaudeLoginSession) -> None:
    proc = sess.proc
    if not proc or not proc.stdout:
        return
    try:
        for line in proc.stdout:
            sess.append(line)
            if _LOGIN_OK_RE.search(line):
                sess.done = True
    except Exception as e:
        sess.error = str(e)
    finally:
        try:
            code = proc.wait(timeout=1)
        except Exception:
            code = proc.poll()
        if code not in (0, None) and not sess.done:
            sess.error = sess.error or f"claude auth login exited ({code})"
        if code == 0:
            sess.done = True


def start_login(*, open_browser: bool = True) -> dict[str, Any]:
    """Start `claude auth login`, capture OAuth URL, optionally open browser."""
    global _SESSION
    bin_path = find_claude_bin()
    if not bin_path:
        return {
            "ok": False,
            "error": "claude_cli_missing",
            "detail": "Claude Code CLI not found on PATH.",
            "installHint": status()["installHint"],
        }

    with _SESSION_LOCK:
        if _SESSION and _SESSION.proc and _SESSION.proc.poll() is None:
            try:
                _SESSION.proc.terminate()
            except Exception:
                pass
        sess = ClaudeLoginSession()
        try:
            sess.proc = subprocess.Popen(
                [bin_path, "auth", "login"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env={**os.environ, "TERM": "dumb", "CI": "1"},
            )
        except OSError as e:
            return {"ok": False, "error": "spawn_failed", "detail": str(e)}
        _SESSION = sess
        threading.Thread(target=_reader, args=(sess,), daemon=True).start()

    # Wait briefly for URL to appear
    deadline = time.time() + 8
    while time.time() < deadline:
        if sess.login_url or sess.error or (sess.proc and sess.proc.poll() is not None and not sess.login_url):
            break
        time.sleep(0.2)

    # Fallback URL if CLI didn't print one yet (user can still paste code after opening Claude)
    if not sess.login_url:
        # Common authorize entry — CLI will still accept the matching code from its own session
        sess.login_url = "https://claude.ai/login"

    opened = False
    if open_browser and sess.login_url:
        try:
            opened = bool(webbrowser.open(sess.login_url))
        except Exception:
            opened = False

    return {
        "ok": True,
        "loginUrl": sess.login_url,
        "browserOpened": opened,
        "loggedIn": claude_logged_in(),
        "hint": "Sign in on the Claude page, then paste the code shown there into NARNA Desktop.",
    }


def complete_login(code: str) -> dict[str, Any]:
    """Paste OAuth code into the pending `claude auth login` process."""
    global _SESSION
    raw = (code or "").strip()
    if not raw:
        return {"ok": False, "error": "empty_code", "detail": "Paste the code from the Claude login page."}

    sess = get_session()
    if not sess or not sess.proc or sess.proc.poll() is not None:
        # Try one-shot: echo code | claude auth login  (some builds accept stdin)
        bin_path = find_claude_bin()
        if not bin_path:
            return {"ok": False, "error": "claude_cli_missing", "detail": "Claude Code CLI not found."}
        try:
            r = subprocess.run(
                [bin_path, "auth", "login"],
                input=raw + "\n",
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, "TERM": "dumb", "CI": "1"},
            )
            out = (r.stdout or "") + (r.stderr or "")
            ok = r.returncode == 0 or _LOGIN_OK_RE.search(out) or claude_logged_in()
            if ok:
                return {"ok": True, "loggedIn": True, "provider": "claude_cli"}
            return {
                "ok": False,
                "error": "login_failed",
                "detail": (out.strip() or "Login did not complete. Click “Sign in with Claude” again, then paste a fresh code.")[
                    :500
                ],
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout", "detail": "Login timed out waiting for Claude CLI."}
        except OSError as e:
            return {"ok": False, "error": "spawn_failed", "detail": str(e)}

    try:
        assert sess.proc.stdin is not None
        sess.proc.stdin.write(raw + "\n")
        sess.proc.stdin.flush()
    except Exception as e:
        return {"ok": False, "error": "write_failed", "detail": str(e)}

    deadline = time.time() + 45
    while time.time() < deadline:
        if sess.done or claude_logged_in():
            try:
                sess.proc.wait(timeout=2)
            except Exception:
                pass
            return {"ok": True, "loggedIn": True, "provider": "claude_cli"}
        if sess.proc.poll() is not None:
            break
        time.sleep(0.25)

    if claude_logged_in():
        return {"ok": True, "loggedIn": True, "provider": "claude_cli"}
    detail = (sess.error or sess.output or "Login did not finish.")[-500:]
    return {"ok": False, "error": "login_failed", "detail": detail}


def cancel_login() -> dict[str, Any]:
    global _SESSION
    sess = get_session()
    if sess and sess.proc and sess.proc.poll() is None:
        try:
            sess.proc.terminate()
        except Exception:
            pass
    _SESSION = None
    return {"ok": True}


def run_claude_print(prompt: str, *, timeout: int = 300) -> str:
    """Non-interactive Claude Code ask using the logged-in subscription."""
    bin_path = find_claude_bin()
    if not bin_path:
        raise RuntimeError("Claude Code CLI not installed")
    if not claude_logged_in():
        raise RuntimeError("Claude Code CLI is not logged in — use Desktop → Sign in with Claude")
    r = subprocess.run(
        [bin_path, "-p", prompt, "--output-format", "text"],
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ},
    )
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if r.returncode != 0 and not out:
        raise RuntimeError(err or f"claude -p failed ({r.returncode})")
    return out or err or "(empty Claude response)"
