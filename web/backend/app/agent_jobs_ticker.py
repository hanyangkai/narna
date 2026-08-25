"""Background ticker — run due Ask agent jobs across all tenant workspaces."""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("uap-cloud.jobs")


def _interval_sec() -> int:
    try:
        return max(60, int(os.environ.get("UAP_AGENT_JOBS_TICK_SEC", "300")))
    except Exception:
        return 300


def _enabled() -> bool:
    return os.environ.get("UAP_AGENT_JOBS_TICKER", "1").strip().lower() not in {
        "0",
        "false",
        "off",
        "no",
    }


def tick_all_tenants(*, limit_per_tenant: int = 3) -> dict[str, Any]:
    from uap.narna_agent import NarnaAgent

    from .tenants import cloud_data_root

    root = cloud_data_root()
    summary: dict[str, Any] = {"tenants": 0, "ran": 0, "errors": []}
    if not root.exists():
        return summary
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        jobs_dir = path / ".uap" / "agent-jobs"
        if not jobs_dir.exists():
            continue
        summary["tenants"] += 1
        try:
            agent = NarnaAgent(workspace=path, tenant_id=path.name)
            due = agent.jobs.due_jobs()
            if not due:
                continue
            ran = agent.run_due_jobs(limit=limit_per_tenant)
            summary["ran"] += len(ran)
        except Exception as e:
            logger.warning("jobs tick failed tenant=%s err=%s", path.name, e)
            summary["errors"].append({"tenant": path.name, "error": str(e)})
    return summary


def start_jobs_ticker() -> None:
    if not _enabled():
        logger.info("agent jobs ticker disabled")
        return

    def loop() -> None:
        # stagger first tick
        time.sleep(45)
        while True:
            try:
                out = tick_all_tenants()
                if out.get("ran") or out.get("errors"):
                    logger.info("agent jobs tick %s", out)
            except Exception as e:
                logger.warning("agent jobs ticker error: %s", e)
            time.sleep(_interval_sec())

    t = threading.Thread(target=loop, name="narna-agent-jobs", daemon=True)
    t.start()
    logger.info("agent jobs ticker started interval=%ss", _interval_sec())
