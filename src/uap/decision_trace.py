"""Decision Trace — structured record of every agent decision (NGS market moat)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DecisionTraceStore:
    """Persist Decision Traces under .uap/decision-traces/."""

    def __init__(
        self,
        workspace: str | Path | None = None,
        *,
        tenant_id: str | None = None,
    ) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.tenant_id = tenant_id
        if tenant_id:
            self.root = self.workspace / ".uap" / "decision-traces" / "tenants" / tenant_id
        else:
            self.root = self.workspace / ".uap" / "decision-traces"
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "index.json"

    def _read_index(self) -> dict[str, Any]:
        if not self.index.exists():
            return {"traces": [], "tenantId": self.tenant_id}
        return json.loads(self.index.read_text(encoding="utf-8"))

    def _write_index(self, data: dict[str, Any]) -> None:
        data["tenantId"] = self.tenant_id
        self.index.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _path(self, trace_id: str) -> Path:
        return self.root / f"{trace_id}.json"

    def create(
        self,
        *,
        goal: str,
        context: dict[str, Any] | None = None,
        evidence: list[dict[str, Any]] | None = None,
        options: list[dict[str, Any]] | None = None,
        chosen: str | None = None,
        rationale: str | None = None,
        adqa: dict[str, Any] | None = None,
        tools_used: list[dict[str, Any]] | None = None,
        models_used: list[str] | None = None,
        action: str = "recommend",
        decision_id: str | None = None,
        session_id: str | None = None,
        channel: str | None = None,
        answer: str | None = None,
    ) -> dict[str, Any]:
        tid = new_id("trace")
        row: dict[str, Any] = {
            "traceId": tid,
            "decisionId": decision_id,
            "tenantId": self.tenant_id,
            "goal": (goal or "")[:2000],
            "context": context or {},
            "evidence": evidence or [],
            "options": options
            or [
                {"id": "recommend", "label": "Proceed with recommendation"},
                {"id": "defer", "label": "Gather more evidence"},
                {"id": "reject", "label": "Do not act"},
            ],
            "chosen": chosen or "recommend",
            "rationale": (rationale or "")[:4000],
            "adqa": {
                "dqs": (adqa or {}).get("dqs"),
                "guardian": (adqa or {}).get("guardian"),
                "confidence": (adqa or {}).get("confidence"),
                "attributes": (adqa or {}).get("attributes"),
            }
            if adqa
            else {},
            "toolsUsed": [
                {"tool": t.get("tool"), "ok": (t.get("result") or {}).get("ok")}
                for t in (tools_used or [])[:40]
            ],
            "modelsUsed": list(models_used or [])[:20],
            "action": action,
            "answerPreview": (answer or "")[:1500],
            "sessionId": session_id,
            "channel": channel,
            "outcome": None,
            "lesson": None,
            "replayOf": None,
            "createdAt": _now(),
            "updatedAt": _now(),
            "standard": "NGS-0030-trace",
        }
        self._path(tid).write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        idx = self._read_index()
        traces = list(idx.get("traces") or [])
        traces.append(
            {
                "traceId": tid,
                "decisionId": decision_id,
                "goal": row["goal"][:120],
                "dqs": row["adqa"].get("dqs"),
                "createdAt": row["createdAt"],
            }
        )
        idx["traces"] = traces[-2000:]
        self._write_index(idx)
        return row

    def get(self, trace_id: str) -> dict[str, Any] | None:
        path = self._path(trace_id)
        if not path.exists():
            # allow lookup by decisionId
            for meta in self._read_index().get("traces") or []:
                if meta.get("decisionId") == trace_id or meta.get("traceId") == trace_id:
                    path = self._path(str(meta["traceId"]))
                    break
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def get_by_decision(self, decision_id: str) -> dict[str, Any] | None:
        for meta in reversed(self._read_index().get("traces") or []):
            if meta.get("decisionId") == decision_id:
                return self.get(str(meta["traceId"]))
        return None

    def list_traces(self, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = list(reversed(self._read_index().get("traces") or []))
        return rows[: max(1, min(limit, 100))]

    def attach_outcome(
        self,
        trace_id: str,
        *,
        status: str,
        detail: str | None = None,
        lesson: str | None = None,
        success_score: float | None = None,
    ) -> dict[str, Any]:
        row = self.get(trace_id)
        if not row:
            raise KeyError(trace_id)
        score = success_score
        if score is None:
            score = 1.0 if status in {"success", "ok", "prevented_harm"} else 0.3
        row["outcome"] = {
            "status": status,
            "detail": detail,
            "successScore": float(score),
            "recordedAt": _now(),
        }
        if lesson:
            row["lesson"] = lesson
        row["updatedAt"] = _now()
        self._path(str(row["traceId"])).write_text(
            json.dumps(row, indent=2) + "\n", encoding="utf-8"
        )
        return row

    def save(self, row: dict[str, Any]) -> dict[str, Any]:
        tid = str(row.get("traceId") or "")
        if not tid:
            raise ValueError("traceId required")
        row["updatedAt"] = _now()
        self._path(tid).write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        return row
