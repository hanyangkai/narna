"""Jurisdiction legal binding templates — enrich council seals (Tier D)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

TEMPLATES_DIR = Path(__file__).resolve().parent / "_packages" / "jurisdictions"


class JurisdictionTemplates:
    """Load jurisdiction-specific binding clauses (not legal advice)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.override = self.workspace / ".uap" / "guardian" / "jurisdictions"

    def list(self) -> list[dict[str, Any]]:
        rows = []
        for root in (TEMPLATES_DIR, self.override):
            if not root.exists():
                continue
            for p in sorted(root.glob("*.yaml")):
                try:
                    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if isinstance(doc, dict):
                    meta = doc.get("metadata") or {}
                    rows.append(
                        {
                            "id": meta.get("id") or p.stem,
                            "name": meta.get("name") or p.stem,
                            "jurisdiction": meta.get("jurisdiction"),
                            "path": str(p),
                        }
                    )
        return rows

    def load(self, jurisdiction_id: str) -> dict[str, Any]:
        for root in (self.override, TEMPLATES_DIR):
            if not root.exists():
                continue
            for p in root.glob("*.yaml"):
                doc = yaml.safe_load(p.read_text(encoding="utf-8"))
                if not isinstance(doc, dict):
                    continue
                meta = doc.get("metadata") or {}
                if meta.get("id") == jurisdiction_id or p.stem == jurisdiction_id:
                    return doc
                if str(meta.get("jurisdiction") or "").lower() == jurisdiction_id.lower():
                    return doc
        raise FileNotFoundError(f"jurisdiction template not found: {jurisdiction_id}")

    def apply_to_binding(
        self, binding: dict[str, Any], *, jurisdiction_id: str
    ) -> dict[str, Any]:
        """Attach jurisdiction clauses to an existing binding record."""
        doc = self.load(jurisdiction_id)
        meta = doc.get("metadata") or {}
        spec = doc.get("spec") or {}
        enriched = dict(binding)
        enriched["jurisdiction"] = {
            "id": meta.get("id"),
            "name": meta.get("name"),
            "region": meta.get("jurisdiction"),
            "clauses": list(spec.get("clauses") or []),
            "requiredRoles": list(spec.get("requiredRoles") or []),
            "retentionYears": spec.get("retentionYears"),
            "disclaimer": spec.get("disclaimer")
            or meta.get("disclaimer")
            or "Not legal advice. Controllers remain responsible.",
        }
        # persist next to binding if on disk
        bid = binding.get("bindingId")
        if bid:
            path = (
                self.workspace
                / ".uap"
                / "guardian"
                / "council"
                / "bindings"
                / f"{bid}.json"
            )
            if path.exists():
                path.write_text(json.dumps(enriched, indent=2) + "\n", encoding="utf-8")
        return enriched
