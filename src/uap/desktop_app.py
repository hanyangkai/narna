"""Launch NARNA Desktop on the local PC."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _free_port(preferred: int = 8765) -> int:
    for port in range(preferred, preferred + 40):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


def run_desktop(
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    workspace: str | Path | None = None,
    open_browser: bool = True,
    tui: bool = False,
    provider: str | None = None,
    gateway: bool = False,
    daemon: bool = False,
    setup_browser: bool = False,
) -> int:
    if setup_browser:
        from .browser_session import setup_browser as do_setup

        out = do_setup()
        print(json.dumps(out, indent=2) if out.get("ok") else f"Browser setup failed: {out.get('error')}")
        return 0 if out.get("ok") else 1

    if tui:
        from .tui_app import run_tui

        return run_tui(provider=provider, workspace=workspace)

    try:
        import uvicorn
    except ImportError:
        print(
            "Desktop needs FastAPI/uvicorn. Install:\n"
            "  pip install 'narna[desktop]'\n"
            "Or: pip install fastapi 'uvicorn[standard]'",
            file=sys.stderr,
        )
        return 1

    from .desktop_runtime import DesktopRuntime, remove_pid, write_pid
    from .desktop_server import create_app, default_workspace

    ws = Path(workspace) if workspace else default_workspace()
    ws.mkdir(parents=True, exist_ok=True)
    listen_port = int(port or os.environ.get("NARNA_DESKTOP_PORT") or _free_port())
    runtime = DesktopRuntime(ws, gateway=gateway)
    app = create_app(workspace=ws, runtime=runtime)
    url = f"http://{host}:{listen_port}/"

    runtime.start()
    if daemon:
        write_pid(ws)

    print(f"NARNA Desktop — local agent")
    print(f"  workspace: {ws}")
    print(f"  open:      {url}")
    print(f"  data:      keys + memory in ~/.narna")
    if gateway:
        print(f"  gateway:   social channels enabled")
    print(f"  jobs:      background ticker (every 60s)")
    print(f"  stop:      Ctrl+C")
    print()

    if open_browser and not daemon:

        def _open() -> None:
            time.sleep(0.8)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    try:
        uvicorn.run(app, host=host, port=listen_port, log_level="warning")
    finally:
        runtime.stop()
        if daemon:
            remove_pid(ws)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="narna desktop", description="Run NARNA on your PC")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--workspace", default=None, help="Default: ~/.narna")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--tui", action="store_true", help="Fullscreen TUI instead of browser")
    p.add_argument("--provider", default=None)
    p.add_argument("--gateway", action="store_true", help="Start social gateway thread (needs tokens in ~/.narna/gateway.json)")
    p.add_argument("--daemon", action="store_true", help="Run in background (no browser open, writes ~/.narna/desktop.pid)")
    p.add_argument("--setup-browser", action="store_true", help="Install Playwright + Chromium then exit")
    args = p.parse_args(argv)
    return run_desktop(
        host=args.host,
        port=args.port,
        workspace=args.workspace,
        open_browser=not args.no_browser,
        tui=args.tui,
        provider=args.provider,
        gateway=args.gateway,
        daemon=args.daemon,
        setup_browser=args.setup_browser,
    )


if __name__ == "__main__":
    raise SystemExit(main())
