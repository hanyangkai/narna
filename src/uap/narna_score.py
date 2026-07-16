"""NARNA Score — multi-dimensional governance rating (0–100).

Like CVSS for security or Lighthouse for web — a branded composite score
for Agentic AI governance posture.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


DIMENSIONS = (
    "identity",
    "capability",
    "evidence",
    "governance",
    "compliance",
    "operational",
)


def compute_narna_score(workspace: Path) -> dict[str, Any]:
    """Compute NARNA Score (0–100) from local workspace signals."""
    ws = Path(workspace)
    breakdown: dict[str, float] = {d: 0.0 for d in DIMENSIONS}
    notes: list[str] = []

    # Identity
    id_dir = ws / ".uap" / "identity"
    if id_dir.exists():
        breakdown["identity"] = 0.85
        if (id_dir / "entities").exists() and any((id_dir / "entities").glob("*.json")):
            breakdown["identity"] = 1.0
    else:
        notes.append("no identity")

    # Capability (manifest richness)
    manifest_path = ws / "narna.yaml"
    const_path = ws / "constitution.yaml"
    caps_count = 0
    if manifest_path.exists() or const_path.exists():
        try:
            from .manifest import load_manifest, load_or_compile_constitution

            if manifest_path.exists():
                doc = load_manifest(manifest_path, validate=False)
                caps_count = len(doc.get("capabilities") or [])
            else:
                doc = load_or_compile_constitution(const_path, workspace=ws, write_constitution_out=False)
                caps_count = len(doc.get("spec", {}).get("capability", {}).get("supports") or [])
            breakdown["capability"] = min(1.0, 0.4 + 0.1 * caps_count)
        except Exception as e:
            notes.append(f"capability: {e}")
            breakdown["capability"] = 0.3
    else:
        notes.append("no manifest")

    # Evidence (VAP proof bundles)
    runs = ws / ".uap" / "runs"
    if runs.exists():
        bundles = list(runs.glob("*/proof-bundle.json"))
        if bundles:
            breakdown["evidence"] = min(1.0, 0.5 + 0.1 * len(bundles))
        elif any(runs.iterdir()):
            breakdown["evidence"] = 0.4
            notes.append("runs without proof")
    else:
        notes.append("no runs")

    # Governance (active package + constitution)
    gov_binding = ws / ".uap" / "runtime" / "active-governance.json"
    if gov_binding.exists():
        breakdown["governance"] = 0.9
        try:
            binding = json.loads(gov_binding.read_text(encoding="utf-8"))
            if binding.get("packageHash"):
                breakdown["governance"] = 1.0
        except Exception:
            pass
    elif const_path.exists() or manifest_path.exists():
        breakdown["governance"] = 0.5
        notes.append("no active governance package")
    else:
        notes.append("no governance")

    # Compliance (certification)
    cert_dir = ws / ".uap" / "certification"
    if cert_dir.exists():
        for p in cert_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                lvl = data.get("level")
                if lvl == "L3":
                    breakdown["compliance"] = 1.0
                    break
                if lvl == "L2":
                    breakdown["compliance"] = max(breakdown["compliance"], 0.85)
                elif lvl == "L1":
                    breakdown["compliance"] = max(breakdown["compliance"], 0.65)
            except Exception:
                pass
    if breakdown["compliance"] == 0.0:
        notes.append("not certified")

    # Operational (run success rate)
    if runs.exists():
        summaries = []
        for run_dir in runs.iterdir():
            events_path = run_dir / "events.jsonl"
            if not events_path.exists():
                continue
            terminal = None
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                evt = json.loads(line)
                if evt.get("eventType") in {"Completed", "Failed"}:
                    terminal = evt.get("eventType")
            if terminal:
                summaries.append(terminal == "Completed")
        if summaries:
            rate = sum(summaries) / len(summaries)
            breakdown["operational"] = round(rate, 4)
        else:
            breakdown["operational"] = 0.3
            notes.append("no completed runs")

    score_0_1 = sum(breakdown[d] for d in DIMENSIONS) / len(DIMENSIONS)
    score_100 = int(round(score_0_1 * 100))

    return {
        "narnaScore": score_100,
        "score": round(score_0_1, 4),
        "breakdown": {k: round(v, 4) for k, v in breakdown.items()},
        "dimensions": list(DIMENSIONS),
        "algorithm": "narna-score-v0",
        "computedAt": _now(),
        "workspace": str(ws.resolve()),
        "notes": "; ".join(notes) if notes else "ok",
    }
