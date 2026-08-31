"""Background services for NARNA Desktop — job ticker + optional gateway (Hermes daemon)."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("narna-desktop")


class DesktopRuntime:
    """Runs scheduled jobs and optional social gateway alongside desktop server."""

    def __init__(self, workspace: Path, *, gateway: bool = False) -> None:
        self.workspace = Path(workspace)
        self.gateway_enabled = gateway
        self._stop = threading.Event()
        self._jobs_thread: threading.Thread | None = None
        self._gateway_thread: threading.Thread | None = None
        self._gateway: Any = None
        self.stats: dict[str, Any] = {"jobsRuns": 0, "jobsHandled": 0, "gateway": "off"}

    def start(self) -> None:
        from .gateway_config import apply_gateway_to_env, load_gateway_config

        apply_gateway_to_env(self.workspace)
        cfg = load_gateway_config(self.workspace)
        gw_on = self.gateway_enabled or bool(cfg.get("gatewayEnabled"))

        self._jobs_thread = threading.Thread(target=self._jobs_loop, name="narna-jobs", daemon=True)
        self._jobs_thread.start()

        if gw_on:
            self._gateway_thread = threading.Thread(target=self._gateway_loop, name="narna-gateway", daemon=True)
            self._gateway_thread.start()
            self.stats["gateway"] = "starting"

    def stop(self) -> None:
        self._stop.set()
        if self._gateway is not None:
            try:
                self._gateway.stop()
            except Exception:
                pass

    def _jobs_loop(self) -> None:
        while not self._stop.is_set():
            try:
                from .narna_config import make_agent

                agent = make_agent(self.workspace)
                ran = agent.run_due_jobs(limit=5)
                if ran:
                    self.stats["jobsRuns"] = int(self.stats.get("jobsRuns") or 0) + 1
                    self.stats["jobsHandled"] = int(self.stats.get("jobsHandled") or 0) + len(ran)
                    logger.info("ran %d scheduled jobs", len(ran))
            except Exception as e:
                logger.warning("job ticker: %s", e)
            self._stop.wait(60.0)

    def _gateway_loop(self) -> None:
        try:
            from .gateway_config import apply_gateway_to_env
            from .gateway_runner import UnifiedGateway, config_from_env
            from .narna_config import make_agent

            apply_gateway_to_env(self.workspace)
            agent = make_agent(self.workspace)

            def ask_fn(message: str, channel: str, external_id: str | None) -> dict:
                return agent.ask(
                    message,
                    channel=channel,
                    external_id=external_id,
                    use_tools=True,
                )

            self._gateway = UnifiedGateway(
                ask_fn=ask_fn,
                config=config_from_env(),
                workspace=self.workspace,
            )
            self.stats["gateway"] = "running"
            self._gateway.run_forever(max_iterations=None)
        except Exception as e:
            self.stats["gateway"] = f"error:{e}"
            logger.warning("gateway: %s", e)

    def status(self) -> dict[str, Any]:
        from .channels.registry import channels_status
        from .gateway_config import gateway_config_masked

        gw_st: dict[str, Any] = {"mode": self.stats.get("gateway", "off")}
        if self._gateway is not None:
            try:
                gw_st = self._gateway.status()
            except Exception:
                pass
        reg = channels_status()
        return {
            "ok": True,
            "runtime": {
                "jobsRuns": self.stats.get("jobsRuns", 0),
                "jobsHandled": self.stats.get("jobsHandled", 0),
                "gatewayThread": bool(self._gateway_thread and self._gateway_thread.is_alive()),
            },
            "config": gateway_config_masked(self.workspace),
            "channels": reg,
            "gateway": gw_st,
        }

    def restart_gateway(self) -> dict[str, Any]:
        """Hot-restart social gateway thread without killing desktop process."""
        from .gateway_config import apply_gateway_to_env, load_gateway_config, save_gateway_config

        apply_gateway_to_env(self.workspace)
        cfg = load_gateway_config(self.workspace)
        if self._gateway is not None:
            try:
                self._gateway.stop()
            except Exception:
                pass
        # Mark enabled so next loop starts
        if not cfg.get("gatewayEnabled"):
            save_gateway_config({**cfg, "gatewayEnabled": True}, self.workspace)
        self.gateway_enabled = True
        if self._gateway_thread and self._gateway_thread.is_alive():
            # Previous run_forever will exit after stop(); start a new thread
            pass
        self._gateway_thread = threading.Thread(
            target=self._gateway_loop, name="narna-gateway", daemon=True
        )
        self._gateway_thread.start()
        self.stats["gateway"] = "restarting"
        return {"ok": True, "gateway": "restarting"}


def write_pid(workspace: Path) -> Path:
    pid_path = Path(workspace) / "desktop.pid"
    pid_path.write_text(str(__import__("os").getpid()) + "\n", encoding="utf-8")
    return pid_path


def remove_pid(workspace: Path) -> None:
    pid_path = Path(workspace) / "desktop.pid"
    if pid_path.exists():
        pid_path.unlink(missing_ok=True)
