"""Claude CLI auth helpers + Desktop wiring (no real Claude login)."""

from __future__ import annotations

from pathlib import Path
from fastapi.testclient import TestClient

from uap.claude_cli_auth import claude_logged_in, find_claude_bin, status
from uap.desktop_server import create_app
from uap.model_router import ModelRouter


def test_find_claude_bin_missing(monkeypatch):
    monkeypatch.delenv("NARNA_CLAUDE_BIN", raising=False)
    monkeypatch.delenv("CLAUDE_BIN", raising=False)
    monkeypatch.setattr("uap.claude_cli_auth.shutil.which", lambda _: None)
    assert find_claude_bin() is None


def test_status_without_cli(monkeypatch):
    monkeypatch.setattr("uap.claude_cli_auth.find_claude_bin", lambda: None)
    monkeypatch.setattr("uap.claude_cli_auth.claude_logged_in", lambda: False)
    st = status()
    assert st["ok"] is True
    assert st["claudeInstalled"] is False
    assert st["loggedIn"] is False


def test_claude_logged_in_from_credentials(tmp_path: Path, monkeypatch):
    cred = tmp_path / ".credentials.json"
    cred.write_text('{"claudeAiOauth":{"accessToken":"tok"}}', encoding="utf-8")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr("uap.claude_cli_auth.find_claude_bin", lambda: None)
    assert claude_logged_in() is True


def test_model_router_claude_cli(monkeypatch):
    monkeypatch.setattr(
        "uap.claude_cli_auth.run_claude_print",
        lambda prompt, **_: f"echo:{prompt[:20]}",
    )
    r = ModelRouter(provider="claude_cli")
    out = r.complete(messages=[{"role": "user", "content": "hello world"}], task="reason")
    assert out.provider == "claude_cli"
    assert "echo:" in out.content


def test_desktop_claude_endpoints(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("uap.claude_cli_auth.find_claude_bin", lambda: "/usr/bin/claude")
    monkeypatch.setattr("uap.claude_cli_auth.claude_logged_in", lambda: False)
    monkeypatch.setattr(
        "uap.claude_cli_auth.start_login",
        lambda open_browser=True: {
            "ok": True,
            "loginUrl": "https://claude.ai/login",
            "browserOpened": False,
            "hint": "paste code",
        },
    )
    monkeypatch.setattr(
        "uap.claude_cli_auth.complete_login",
        lambda code: {"ok": True, "loggedIn": True, "provider": "claude_cli"},
    )
    # After complete, status should show logged in for config ready checks
    logged = {"v": False}

    def _logged():
        return logged["v"]

    monkeypatch.setattr("uap.claude_cli_auth.claude_logged_in", _logged)

    app = create_app(workspace=tmp_path)
    client = TestClient(app)

    st = client.get("/v1/desktop/claude/status").json()
    assert st["claudeInstalled"] is True

    start = client.post("/v1/desktop/claude/login/start", json={"openBrowser": False}).json()
    assert start["ok"] is True
    assert "loginUrl" in start

    logged["v"] = True
    done = client.post("/v1/desktop/claude/login/complete", json={"code": "test-code"}).json()
    assert done["ok"] is True
    assert done["provider"] == "claude_cli"

    cfg = client.get("/v1/desktop/config").json()
    assert cfg["provider"] == "claude_cli"
    assert cfg["hasKey"] is True
