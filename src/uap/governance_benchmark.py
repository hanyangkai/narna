"""Governance benchmark — rank vendors/stacks on compliance posture, not LLM MMLU."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class VendorScore:
    vendor: str
    score: float
    breakdown: dict[str, float]
    notes: str = ""


# Seed reference scores (informative baseline — updated as Compatibility Program grows)
REFERENCE_BOARD: list[dict[str, Any]] = [
    {
        "vendor": "Anthropic",
        "score": 0.98,
        "breakdown": {"identity": 0.95, "permission": 0.98, "evidence": 0.97, "policy": 0.99, "certification": 0.96},
        "notes": "Strong safety / policy culture; integrate via adapters.",
    },
    {
        "vendor": "OpenAI",
        "score": 0.96,
        "breakdown": {"identity": 0.94, "permission": 0.95, "evidence": 0.96, "policy": 0.95, "certification": 0.95},
        "notes": "Agents SDK + OTel; wrap with narna-openai.",
    },
    {
        "vendor": "Google",
        "score": 0.94,
        "breakdown": {"identity": 0.93, "permission": 0.94, "evidence": 0.94, "policy": 0.93, "certification": 0.93},
        "notes": "Gemini / ADK path; planned narna-google.",
    },
    {
        "vendor": "LangGraph",
        "score": 0.92,
        "breakdown": {"identity": 0.90, "permission": 0.91, "evidence": 0.93, "policy": 0.90, "certification": 0.91},
        "notes": "Workflow host; narna-langgraph available.",
    },
    {
        "vendor": "CrewAI",
        "score": 0.90,
        "breakdown": {"identity": 0.88, "permission": 0.89, "evidence": 0.90, "policy": 0.90, "certification": 0.89},
        "notes": "Multi-agent host; narna-crewai available.",
    },
]


def score_local_workspace(workspace: Path) -> dict[str, Any]:
    """Score a local NARNA workspace on governance dimensions (0–1)."""
    dims = {
        "identity": 0.0,
        "permission": 0.0,
        "evidence": 0.0,
        "policy": 0.0,
        "certification": 0.0,
    }
    notes: list[str] = []

    if (workspace / ".uap" / "identity").exists():
        dims["identity"] = 0.8
        if (workspace / ".uap" / "identity" / "entities").exists():
            dims["identity"] = 1.0
    else:
        notes.append("missing identity")

    const = workspace / "constitution.yaml"
    manifest = workspace / "narna.yaml"
    if const.exists() or manifest.exists():
        dims["permission"] = 0.7
        dims["policy"] = 0.7
        try:
            from .manifest import load_or_compile_constitution

            doc = load_or_compile_constitution(
                const if const.exists() else manifest,
                workspace=workspace,
                write_constitution_out=False,
            )
            grants = doc.get("spec", {}).get("permission", {}).get("grants") or []
            rules = doc.get("spec", {}).get("policy", {}).get("rules") or []
            dims["permission"] = min(1.0, 0.5 + 0.1 * len(grants))
            dims["policy"] = min(1.0, 0.5 + 0.1 * len(rules))
            if doc.get("spec", {}).get("governance", {}).get("orgId"):
                dims["policy"] = min(1.0, dims["policy"] + 0.1)
        except Exception as e:
            notes.append(f"constitution parse: {e}")
    else:
        notes.append("missing narna.yaml/constitution.yaml")

    runs = workspace / ".uap" / "runs"
    if runs.exists() and any(runs.glob("*/proof-bundle.json")):
        dims["evidence"] = 1.0
    elif runs.exists():
        dims["evidence"] = 0.5
        notes.append("runs without proof bundles")
    else:
        notes.append("no runs")

    cert = workspace / ".uap" / "certification"
    if cert.exists() and any(cert.glob("*.json")):
        dims["certification"] = 0.85
        try:
            for p in cert.glob("*.json"):
                data = json.loads(p.read_text(encoding="utf-8"))
                lvl = data.get("level")
                if lvl == "L3":
                    dims["certification"] = 1.0
                    break
                if lvl == "L2":
                    dims["certification"] = max(dims["certification"], 0.95)
        except Exception:
            pass
    else:
        notes.append("not certified")

    score = sum(dims.values()) / len(dims)
    return {
        "vendor": "local",
        "workspace": str(workspace),
        "score": round(score, 4),
        "breakdown": {k: round(v, 4) for k, v in dims.items()},
        "notes": "; ".join(notes) if notes else "ok",
        "computedAt": _now(),
    }


def leaderboard(*, workspace: Path | None = None) -> dict[str, Any]:
    rows = list(REFERENCE_BOARD)
    if workspace is not None:
        local = score_local_workspace(workspace)
        rows = rows + [local]
    rows = sorted(rows, key=lambda r: float(r.get("score") or 0), reverse=True)
    return {
        "algorithm": "narna-governance-bench-v0",
        "computedAt": _now(),
        "description": "Governance / compliance posture — not LLM capability MMLU.",
        "rows": rows,
    }


def write_leaderboard(workspace: Path) -> Path:
    out_dir = workspace / ".uap" / "benchmark"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "governance.json"
    path.write_text(json.dumps(leaderboard(workspace=workspace), indent=2), encoding="utf-8")
    return path
