"""Outcome Learning Engine — Decision → Outcome → Memory → future ADQA priors."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .decision_memory import DecisionMemory


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class OutcomeLearningEngine:
    """Aggregate outcomes into action-level priors and policy hints."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.memory = DecisionMemory(self.workspace)
        self.path = self.workspace / ".uap" / "learning" / "priors.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"actions": {}, "updatedAt": None}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        data["updatedAt"] = _now()
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def evaluate(
        self,
        decision_id: str,
        *,
        status: str,
        detail: str | None = None,
        success_score: float | None = None,
        lesson: str | None = None,
        predictedSuccess: float | None = None,
    ) -> dict[str, Any]:
        """Attach outcome and refresh action priors."""
        row = self.memory.attach_outcome(
            decision_id,
            status=status,
            detail=detail,
            success_score=success_score,
            lesson=lesson,
        )
        prior = self._update_prior(row)
        # v0 heuristic prediction for next similar action
        pred = prior.get("avgSuccess")
        if predictedSuccess is not None:
            pred = predictedSuccess
        return {
            "ok": True,
            "decision": row,
            "prior": prior,
            "predictedSuccess": pred,
            "standard": "NGS-0026",
            "loop": [
                "decision",
                "action",
                "outcome",
                "evaluation",
                "memory_update",
                "policy_hint",
                "future_decision",
            ],
        }

    def _update_prior(self, row: dict[str, Any]) -> dict[str, Any]:
        action = str(row.get("action") or "unknown")
        data = self._read()
        bucket = data.setdefault("actions", {}).setdefault(
            action,
            {
                "action": action,
                "n": 0,
                "successSum": 0.0,
                "dqsSum": 0.0,
                "lessons": [],
                "hint": None,
            },
        )
        score = float((row.get("outcome") or {}).get("successScore") or 0.0)
        bucket["n"] = int(bucket["n"]) + 1
        bucket["successSum"] = float(bucket["successSum"]) + score
        if row.get("dqs") is not None:
            bucket["dqsSum"] = float(bucket["dqsSum"]) + float(row["dqs"])
        if row.get("lesson"):
            lessons = list(bucket.get("lessons") or [])
            lessons.insert(0, row["lesson"])
            bucket["lessons"] = lessons[:20]
        avg_success = bucket["successSum"] / max(1, bucket["n"])
        avg_dqs = bucket["dqsSum"] / max(1, bucket["n"]) if bucket["n"] else 0
        # Policy hint for future ADQA
        if avg_success < 0.4 and bucket["n"] >= 2:
            bucket["hint"] = "escalate"
        elif avg_success >= 0.8 and avg_dqs >= 70:
            bucket["hint"] = "favor_approve"
        else:
            bucket["hint"] = "neutral"
        bucket["avgSuccess"] = round(avg_success, 4)
        bucket["avgDqs"] = round(avg_dqs, 2)
        data["actions"][action] = bucket
        self._write(data)
        return bucket

    def prior_for(self, action: str) -> dict[str, Any] | None:
        return (self._read().get("actions") or {}).get(action)

    def enrich_adqa_context(self, action: str) -> dict[str, Any]:
        """Feed lessons + prior into ADQA context."""
        prior = self.prior_for(action) or {}
        lessons = self.memory.lessons_for(action=action, limit=5)
        return {
            "decisionMemory": {
                "lessons": lessons,
                "prior": prior or None,
                "source": "NGS-0025",
            }
        }
