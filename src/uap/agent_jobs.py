"""Agent scheduled jobs — Hermes-like cron for Ask (v0)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class AgentJobStore:
    """Persist recurring / one-shot Ask jobs under .uap/agent-jobs."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "agent-jobs"
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "index.json"

    def _read(self) -> dict[str, Any]:
        if not self.index.exists():
            return {"jobs": []}
        return json.loads(self.index.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.index.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def list_jobs(self) -> list[dict[str, Any]]:
        return list(self._read().get("jobs") or [])

    def get(self, job_id: str) -> dict[str, Any] | None:
        path = self.root / f"{job_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def create(
        self,
        *,
        prompt: str,
        every_minutes: int | None = None,
        run_at: str | None = None,
        channel: str = "job",
        deliver_to: str | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError("prompt required")
        jid = new_id("job")
        now = _now()
        if run_at:
            next_run = run_at
        elif every_minutes and every_minutes > 0:
            next_run = _iso(now + timedelta(minutes=int(every_minutes)))
        else:
            next_run = _iso(now)
        row = {
            "jobId": jid,
            "prompt": prompt[:4000],
            "everyMinutes": int(every_minutes) if every_minutes else None,
            "channel": channel,
            "deliverTo": (deliver_to or "").strip() or None,
            "enabled": bool(enabled),
            "nextRunAt": next_run,
            "lastRunAt": None,
            "lastDecisionId": None,
            "lastDelivery": None,
            "runCount": 0,
            "createdAt": _iso(now),
            "updatedAt": _iso(now),
            "standard": "NGS-0029-jobs",
        }
        (self.root / f"{jid}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        idx = self._read()
        jobs = [j for j in (idx.get("jobs") or []) if j.get("jobId") != jid]
        jobs.append(
            {
                "jobId": jid,
                "prompt": row["prompt"][:120],
                "everyMinutes": row["everyMinutes"],
                "enabled": row["enabled"],
                "nextRunAt": row["nextRunAt"],
            }
        )
        idx["jobs"] = jobs[-200:]
        self._write(idx)
        return row

    def due_jobs(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or _now()
        due: list[dict[str, Any]] = []
        for meta in self.list_jobs():
            row = self.get(str(meta.get("jobId") or ""))
            if not row or not row.get("enabled"):
                continue
            nxt = str(row.get("nextRunAt") or "")
            try:
                when = datetime.fromisoformat(nxt.replace("Z", "+00:00"))
            except Exception:
                when = now
            if when <= now:
                due.append(row)
        return due

    def mark_ran(
        self,
        job_id: str,
        *,
        decision_id: str | None = None,
        delivery: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self.get(job_id)
        if not row:
            raise KeyError(job_id)
        now = _now()
        row["lastRunAt"] = _iso(now)
        row["lastDecisionId"] = decision_id
        if delivery is not None:
            row["lastDelivery"] = delivery
        row["runCount"] = int(row.get("runCount") or 0) + 1
        every = row.get("everyMinutes")
        if every and int(every) > 0:
            row["nextRunAt"] = _iso(now + timedelta(minutes=int(every)))
        else:
            row["enabled"] = False
            row["nextRunAt"] = None
        row["updatedAt"] = _iso(now)
        (self.root / f"{job_id}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        idx = self._read()
        jobs = []
        for j in idx.get("jobs") or []:
            if j.get("jobId") == job_id:
                j = {
                    **j,
                    "enabled": row["enabled"],
                    "nextRunAt": row["nextRunAt"],
                }
            jobs.append(j)
        idx["jobs"] = jobs
        self._write(idx)
        return row
