"""Decision Memory — NGS-0025 verified decisions + outcomes + lessons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DecisionMemory:
    """Store decision quality — not chat continuity.

    Multi-tenant Cloud: pass tenant_id so records never cross orgs.
    """

    def __init__(
        self,
        workspace: str | Path | None = None,
        *,
        tenant_id: str | None = None,
    ) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.tenant_id = tenant_id
        if tenant_id:
            self.root = self.workspace / ".uap" / "decision-memory" / "tenants" / tenant_id
        else:
            self.root = self.workspace / ".uap" / "decision-memory"
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = self.root / "index.json"

    def _read_index(self) -> dict[str, Any]:
        if not self.index.exists():
            return {"records": [], "tenantId": self.tenant_id}
        return json.loads(self.index.read_text(encoding="utf-8"))

    def _write_index(self, data: dict[str, Any]) -> None:
        data["tenantId"] = self.tenant_id
        self.index.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _path(self, decision_id: str) -> Path:
        return self.root / f"{decision_id}.json"

    def record(
        self,
        *,
        action: str,
        context: dict[str, Any] | None = None,
        reasoning: list[str] | None = None,
        guardian: str | None = None,
        dqs: int | None = None,
        confidence: float | None = None,
        provider: str | None = None,
        decision: str | None = None,
        adqa: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        tid = tenant_id or self.tenant_id
        did = new_id("dmem")
        row: dict[str, Any] = {
            "decisionId": did,
            "tenantId": tid,
            "action": action,
            "context": context or {},
            "reasoning": reasoning or [],
            "guardian": guardian,
            "dqs": dqs,
            "confidence": confidence,
            "provider": provider,
            "decision": decision,
            "outcome": None,
            "lesson": None,
            "createdAt": _now(),
            "standard": "NGS-0025",
        }
        if adqa:
            row["dqs"] = adqa.get("dqs", dqs)
            row["guardian"] = adqa.get("guardian", guardian)
            row["attributes"] = adqa.get("attributes")
        path = self._path(did)
        path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        idx = self._read_index()
        idx.setdefault("records", []).append(
            {
                "decisionId": did,
                "action": action,
                "tenantId": tid,
                "createdAt": row["createdAt"],
                "provider": provider,
            }
        )
        idx["records"] = idx["records"][-5000:]
        self._write_index(idx)
        return row

    def get(self, decision_id: str) -> dict[str, Any] | None:
        path = self._path(decision_id)
        if not path.exists():
            return None
        row = json.loads(path.read_text(encoding="utf-8"))
        if self.tenant_id and row.get("tenantId") and row.get("tenantId") != self.tenant_id:
            return None
        return row

    def attach_outcome(
        self,
        decision_id: str,
        *,
        status: str,
        detail: str | None = None,
        success_score: float | None = None,
        lesson: str | None = None,
    ) -> dict[str, Any]:
        row = self.get(decision_id)
        if not row:
            raise KeyError(f"unknown decisionId: {decision_id}")
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
        if row.get("confidence") is None and score is not None:
            row["confidence"] = float(score)
        self._path(decision_id).write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        return row

    def query(
        self,
        *,
        action: str | None = None,
        customer: str | None = None,
        tenant_id: str | None = None,
        limit: int = 20,
        with_outcome_only: bool = False,
    ) -> list[dict[str, Any]]:
        tid = tenant_id or self.tenant_id
        out: list[dict[str, Any]] = []
        for meta in reversed(self._read_index().get("records") or []):
            if tid and meta.get("tenantId") and meta.get("tenantId") != tid:
                continue
            row = self.get(str(meta.get("decisionId")))
            if not row:
                continue
            if tid and row.get("tenantId") and row.get("tenantId") != tid:
                continue
            if action and row.get("action") != action:
                continue
            ctx = row.get("context") or {}
            if customer and str(ctx.get("customer") or "") != customer:
                continue
            if with_outcome_only and not row.get("outcome"):
                continue
            out.append(row)
            if len(out) >= limit:
                break
        return out

    def lessons_for(self, *, action: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
        """Compact lessons for ADQA context enrichment."""
        rows = self.query(action=action, limit=limit * 3, with_outcome_only=True)
        lessons = []
        for r in rows:
            if not r.get("lesson") and not (r.get("outcome") or {}).get("detail"):
                continue
            lessons.append(
                {
                    "decisionId": r["decisionId"],
                    "action": r.get("action"),
                    "lesson": r.get("lesson") or (r.get("outcome") or {}).get("detail"),
                    "successScore": (r.get("outcome") or {}).get("successScore"),
                    "dqs": r.get("dqs"),
                    "guardian": r.get("guardian"),
                    "tenantId": r.get("tenantId"),
                }
            )
            if len(lessons) >= limit:
                break
        return lessons
