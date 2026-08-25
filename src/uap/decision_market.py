"""Decision Package marketplace catalog — list / install from seed packages."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .governance_runtime import REPO_PACKAGES, load_package_file, package_hash
from .packages import register_package_local


class DecisionMarketplace:
    """Catalog Decision Packages for install into a workspace."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()

    def list_packages(
        self,
        *,
        industry: str | None = None,
        decisions_only: bool = True,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if not REPO_PACKAGES.exists():
            return rows
        for path in sorted(REPO_PACKAGES.glob("*.yaml")):
            try:
                doc = load_package_file(path)
            except Exception:
                continue
            kind = doc.get("kind")
            meta = doc.get("metadata") or {}
            if decisions_only and kind != "DecisionPackage":
                continue
            if not decisions_only and kind not in {"DecisionPackage", "GovernancePackage"}:
                if "decision" not in (doc.get("spec") or {}):
                    continue
            ind = str(meta.get("industry") or (meta.get("labels") or {}).get("industry") or "")
            if industry and industry.lower() not in ind.lower():
                continue
            rows.append(
                {
                    "name": meta.get("name") or path.stem,
                    "provider": meta.get("provider") or path.stem,
                    "version": meta.get("version") or "0.1.0",
                    "kind": kind,
                    "packageKind": meta.get("packageKind") or kind,
                    "industry": ind or None,
                    "packageHash": package_hash(doc),
                    "path": str(path),
                    "actions": list(((doc.get("spec") or {}).get("decision") or {}).get("actions") or []),
                    "module": "Marketplace",
                }
            )
        return rows

    def install(self, provider: str) -> dict[str, Any]:
        """Copy seed package into workspace registry."""
        path = REPO_PACKAGES / f"{provider}.yaml"
        if not path.exists():
            matches = list(REPO_PACKAGES.glob(f"*{provider}*.yaml"))
            # prefer DecisionPackage matches
            preferred = []
            for m in matches:
                try:
                    if load_package_file(m).get("kind") == "DecisionPackage":
                        preferred.append(m)
                except Exception:
                    continue
            path = (preferred or matches)[0] if (preferred or matches) else path
            if not path.exists():
                raise FileNotFoundError(f"package not found: {provider}")
        entry = register_package_local(self.workspace, path)
        dest_dir = self.workspace / ".uap" / "decision-packages"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(path, dest_dir / path.name)
        return {"ok": True, "installed": entry, "module": "Marketplace"}
