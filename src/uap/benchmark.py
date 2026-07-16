from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class BenchmarkStore:
    """Storage layer: trust/execution benchmarks across runs."""

    def __init__(self, workspace: Path) -> None:
        self.path = workspace / ".uap" / "benchmark" / "scores.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, *, agent_id: str, run_id: str, trust_score: dict[str, Any]) -> None:
        row = {
            "recordId": new_id("bench"),
            "agentId": agent_id,
            "runId": run_id,
            "score": trust_score.get("score"),
            "breakdown": trust_score.get("breakdown"),
            "algorithm": trust_score.get("algorithm"),
            "recordedAt": _now_rfc3339(),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def list(self, *, agent_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if agent_id and row.get("agentId") != agent_id:
                continue
            rows.append(row)
        return rows[-limit:]

    def average_score(self, *, agent_id: str) -> float | None:
        rows = self.list(agent_id=agent_id)
        if not rows:
            return None
        return sum(float(r["score"]) for r in rows if r.get("score") is not None) / len(rows)
