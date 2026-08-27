"""NARNA Desktop — local Ask API for PC (no cloud required)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel


def default_workspace() -> Path:
    env = (os.environ.get("NARNA_HOME") or os.environ.get("UAP_HOME") or "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".narna"


def config_path(workspace: Path) -> Path:
    return workspace / "config.json"


def load_config(workspace: Path) -> dict[str, Any]:
    from .narna_config import load_narna_config

    return load_narna_config(workspace)


def save_config(workspace: Path, data: dict[str, Any]) -> None:
    from .narna_config import save_narna_config

    save_narna_config(data, workspace)


def static_dir() -> Path:
    """Resolve UI assets for source install and PyInstaller freeze."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(getattr(sys, "_MEIPASS"))
        for candidate in (
            base / "uap" / "desktop_static",
            base / "desktop_static",
            base / "src" / "uap" / "desktop_static",
        ):
            if candidate.is_dir():
                return candidate
    return Path(__file__).resolve().parent / "desktop_static"


class AskBody(BaseModel):
    message: str
    sessionId: str | None = None
    mode: str = "cheap"
    challenge: bool = False
    llmProvider: str | None = None
    llmApiKey: str | None = None
    llmBaseUrl: str | None = None
    model: str | None = None


class ConfigBody(BaseModel):
    provider: str = "openrouter"
    apiKey: str | None = None
    baseUrl: str | None = None
    model: str | None = None


def create_app(*, workspace: Path | None = None) -> FastAPI:
    ws = Path(workspace) if workspace else default_workspace()
    ws.mkdir(parents=True, exist_ok=True)
    assets = static_dir()

    app = FastAPI(title="NARNA Desktop", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.workspace = ws

    @app.get("/v1/health")
    def health() -> dict[str, Any]:
        try:
            from narna import __version__ as app_version
        except Exception:
            app_version = "0.2.1"
        cfg = load_config(ws)
        browser_cfg = cfg.get("browserEnabled")
        if browser_cfg is None:
            browser_on = str(os.environ.get("UAP_BROWSER_ENABLED") or "").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        else:
            browser_on = bool(browser_cfg)
        return {
            "ok": True,
            "mode": "desktop",
            "version": app_version,
            "workspace": str(ws),
            "frozen": bool(getattr(sys, "frozen", False)),
            "shellBackend": (
                os.environ.get("UAP_SHELL_BACKEND") or cfg.get("shellBackend") or "local"
            ),
            "browserEnabled": browser_on,
            "skillsIndexDefault": os.environ.get(
                "UAP_SKILL_HUB_INDEX_URL",
                "https://raw.githubusercontent.com/hanyangkai/narna/main/skills/public-index.json",
            ),
            "standard": "NGS-0029-desktop",
        }

    @app.get("/v1/desktop/config")
    def get_config() -> dict[str, Any]:
        cfg = load_config(ws)
        key = str(cfg.get("apiKey") or "")
        masked = (key[:4] + "…" + key[-4:]) if len(key) > 8 else ("***" if key else "")
        return {
            "ok": True,
            "provider": cfg.get("provider") or "openrouter",
            "hasKey": bool(key),
            "maskedKey": masked,
            "baseUrl": cfg.get("baseUrl"),
            "model": cfg.get("model"),
            "workspace": str(ws),
        }

    @app.put("/v1/desktop/config")
    def put_config(body: ConfigBody) -> dict[str, Any]:
        cfg = load_config(ws)
        cfg["provider"] = (body.provider or "openrouter").lower()
        if body.apiKey is not None:
            cfg["apiKey"] = body.apiKey.strip()
        if body.baseUrl is not None:
            cfg["baseUrl"] = body.baseUrl.strip() or None
        if body.model is not None:
            cfg["model"] = body.model.strip() or None
        save_config(ws, cfg)
        return {"ok": True, **get_config()}

    @app.post("/v1/agent/ask")
    def agent_ask(body: AskBody) -> dict[str, Any]:
        from uap.model_router import ModelRouter
        from uap.narna_agent import NarnaAgent

        cfg = load_config(ws)
        provider = (body.llmProvider or cfg.get("provider") or "openrouter").lower()
        api_key = (body.llmApiKey or cfg.get("apiKey") or "").strip() or None
        base_url = body.llmBaseUrl or cfg.get("baseUrl") or None
        if not api_key:
            provider = "mock"
        models: dict[str, str] = {}
        model = body.model or cfg.get("model")
        if model:
            models = {"cheap": str(model), "reason": str(model), "challenge": str(model)}
        try:
            router = ModelRouter(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                models=models or None,
            )
            agent = NarnaAgent(workspace=ws, router=router)
            out = agent.ask(
                body.message,
                session_id=body.sessionId,
                use_tools=True,
                challenge=bool(body.challenge),
                mode=body.mode or "cheap",
                channel="desktop",
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e)) from e
        return {"ok": True, **out}

    @app.get("/")
    def index() -> HTMLResponse:
        html = assets / "index.html"
        if html.is_file():
            return HTMLResponse(html.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>NARNA Desktop</h1><p>UI missing.</p>")

    @app.get("/ask")
    def ask_page() -> HTMLResponse:
        return index()

    @app.get("/favicon.ico")
    def favicon() -> Any:
        icon = assets / "favicon.svg"
        if icon.is_file():
            return FileResponse(icon, media_type="image/svg+xml")
        return JSONResponse({"ok": False}, status_code=404)

    return app
