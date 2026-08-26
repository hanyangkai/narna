"""NARNA Decision Benchmark — reproducible ACT/REVIEW/REJECT scoring (market plan B5)."""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DECISIONS_DIR = REPO_ROOT / "benchmark" / "decisions"


def default_scenarios_dir() -> Path:
    candidates = [
        Path.cwd() / "benchmark" / "decisions",
        DEFAULT_DECISIONS_DIR,
        Path(__file__).resolve().parents[3] / "benchmark" / "decisions",
    ]
    for c in candidates:
        if c.is_dir() and any(c.glob("*.json")):
            return c
    return DEFAULT_DECISIONS_DIR


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verdict_from_adqa(out: dict[str, Any]) -> str:
    """Map ADQA / DecisionEngine output → ACT | REVIEW | REJECT."""
    nested = out.get("adqa") if isinstance(out.get("adqa"), dict) else {}
    dqs = out.get("dqs")
    if dqs is None:
        dqs = nested.get("dqs")
    guardian = out.get("guardian") or nested.get("guardian")
    guardian_l = str(guardian or "").lower()
    decision = str(out.get("decision") or nested.get("decision") or "").lower()
    if guardian_l in {"reject", "block", "deny"} or decision == "deny":
        return "REJECT"
    if guardian_l in {"revise", "escalate", "ask", "review"} or (
        isinstance(dqs, (int, float)) and dqs < 70
    ):
        return "REVIEW"
    return "ACT"


def load_scenarios(
    directory: str | Path | None = None,
    *,
    category: str | None = None,
    limit: int | None = None,
    ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    root = Path(directory) if directory else default_scenarios_dir()
    if not root.is_dir():
        raise FileNotFoundError(f"benchmark directory not found: {root}")
    id_set = {str(x) for x in ids} if ids else None
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        if path.name.startswith("_"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    item.setdefault("_path", str(path))
                    rows.append(item)
        elif isinstance(data, dict):
            data.setdefault("_path", str(path))
            rows.append(data)
    if category:
        rows = [r for r in rows if str(r.get("category") or "") == category]
    if id_set is not None:
        rows = [r for r in rows if str(r.get("id") or "") in id_set]
    rows.sort(key=lambda r: str(r.get("id") or ""))
    if limit is not None:
        rows = rows[: max(0, int(limit))]
    return rows


def _propose_mock(scenario: dict[str, Any]) -> dict[str, Any]:
    proposed = dict(scenario.get("proposed") or {})
    return {
        "action": str(proposed.get("action") or scenario.get("action") or "").strip(),
        "evidence": list(proposed.get("evidence") or scenario.get("evidence") or []),
        "context": dict(proposed.get("context") or scenario.get("context") or {}),
        "provider": proposed.get("provider") or scenario.get("provider"),
        "question": scenario.get("question"),
    }


def _propose_strip(scenario: dict[str, Any]) -> dict[str, Any]:
    p = _propose_mock(scenario)
    p["evidence"] = []
    return p


AGENTS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "mock": _propose_mock,
    "strip": _propose_strip,
}


@dataclass
class ScenarioResult:
    id: str
    category: str
    expected: str
    got: str
    correct: bool
    dqs: float | None
    guardian: str | None
    decision: str | None
    action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "expectedVerdict": self.expected,
            "gotVerdict": self.got,
            "correct": self.correct,
            "dqs": self.dqs,
            "guardian": self.guardian,
            "decision": self.decision,
            "action": self.action,
        }


def run_scenario(
    scenario: dict[str, Any],
    *,
    agent: str = "mock",
    workspace: str | Path | None = None,
) -> ScenarioResult:
    from uap.adqa import ADQAEngine

    proposer = AGENTS.get(agent)
    if proposer is None:
        raise ValueError(f"unknown agent '{agent}' (choose: {', '.join(sorted(AGENTS))})")
    proposal = proposer(scenario)
    action = proposal["action"]
    if not action:
        raise ValueError(f"scenario {scenario.get('id')} missing action")

    out = ADQAEngine(workspace or Path.cwd()).check_proposed(
        action=action,
        provider=str(proposal["provider"]) if proposal.get("provider") else None,
        evidence_present=[str(x) for x in proposal["evidence"]],
        context=proposal["context"],
        question=str(proposal["question"]) if proposal.get("question") else None,
        persist=False,
    )
    adqa = out.get("adqa") if isinstance(out.get("adqa"), dict) else {}
    dr = out.get("decisionResult") if isinstance(out.get("decisionResult"), dict) else {}
    mapped = {
        "adqa": adqa,
        "dqs": adqa.get("dqs"),
        "guardian": adqa.get("guardian"),
        "decision": dr.get("decision") or adqa.get("decision"),
    }
    got = verdict_from_adqa(mapped)
    expected = str(scenario.get("expectedVerdict") or "").upper()
    dqs = adqa.get("dqs")
    return ScenarioResult(
        id=str(scenario.get("id") or "unknown"),
        category=str(scenario.get("category") or "uncategorized"),
        expected=expected,
        got=got,
        correct=got == expected,
        dqs=float(dqs) if isinstance(dqs, (int, float)) else None,
        guardian=str(adqa.get("guardian")) if adqa.get("guardian") is not None else None,
        decision=str(dr.get("decision")) if dr.get("decision") is not None else None,
        action=action,
    )


def run_benchmark(
    *,
    directory: str | Path | None = None,
    agent: str = "mock",
    category: str | None = None,
    limit: int | None = None,
    workspace: str | Path | None = None,
    ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    import tempfile

    scenarios = load_scenarios(directory, category=category, limit=limit, ids=ids)
    if not scenarios:
        raise ValueError("no scenarios loaded")

    own_tmp = workspace is None
    tmp: tempfile.TemporaryDirectory[str] | None = None
    ws = Path(workspace) if workspace else None
    if ws is None:
        tmp = tempfile.TemporaryDirectory()
        ws = Path(tmp.name)

    results: list[ScenarioResult] = []
    try:
        for sc in scenarios:
            results.append(run_scenario(sc, agent=agent, workspace=ws))
    finally:
        if tmp is not None:
            tmp.cleanup()

    correct = sum(1 for r in results if r.correct)
    dqs_vals = [r.dqs for r in results if r.dqs is not None]
    by_cat: dict[str, dict[str, Any]] = {}
    for r in results:
        bucket = by_cat.setdefault(r.category, {"n": 0, "correct": 0, "dqs": []})
        bucket["n"] += 1
        if r.correct:
            bucket["correct"] += 1
        if r.dqs is not None:
            bucket["dqs"].append(r.dqs)
    category_stats = {
        k: {
            "n": v["n"],
            "accuracy": round(v["correct"] / v["n"], 4) if v["n"] else 0.0,
            "avgDqs": round(statistics.mean(v["dqs"]), 2) if v["dqs"] else None,
        }
        for k, v in sorted(by_cat.items())
    }
    confusion: dict[str, dict[str, int]] = {}
    for r in results:
        row = confusion.setdefault(r.expected, {"ACT": 0, "REVIEW": 0, "REJECT": 0})
        if r.got in row:
            row[r.got] += 1
        else:
            row[r.got] = row.get(r.got, 0) + 1

    return {
        "ok": True,
        "benchmark": "narna-decision-v0",
        "agent": agent,
        "ranAt": _now(),
        "n": len(results),
        "correct": correct,
        "accuracy": round(correct / len(results), 4),
        "dqs": {
            "avg": round(statistics.mean(dqs_vals), 2) if dqs_vals else None,
            "min": min(dqs_vals) if dqs_vals else None,
            "max": max(dqs_vals) if dqs_vals else None,
        },
        "byCategory": category_stats,
        "confusion": confusion,
        "results": [r.as_dict() for r in results],
        "note": "No marketing leaderboard numbers — run locally and publish your own results.",
    }


def write_leaderboard_stub(path: str | Path, run: dict[str, Any] | None = None) -> Path:
    """Write leaderboard JSON without inventing competitor scores."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "benchmark": "narna-decision-v0",
        "updatedAt": _now(),
        "entries": [],
        "disclaimer": "Submit runs via PR. Do not invent accuracy numbers in marketing.",
    }
    if run:
        payload["entries"].append(
            {
                "agent": run.get("agent"),
                "accuracy": run.get("accuracy"),
                "n": run.get("n"),
                "avgDqs": (run.get("dqs") or {}).get("avg"),
                "ranAt": run.get("ranAt"),
                "source": "local",
            }
        )
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
