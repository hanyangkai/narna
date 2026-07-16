"""Governance Package marketplace — publish / pull / search local + cloud."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .governance_runtime import REPO_PACKAGES, load_package_file, package_hash


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def register_package_local(workspace: Path, package_path: Path) -> dict[str, Any]:
    """Register a Governance Package into local .uap/package-registry."""
    doc = load_package_file(package_path)
    meta = doc.get("metadata") or {}
    package_id = str(meta.get("id") or package_path.stem)
    root = workspace / ".uap" / "package-registry"
    root.mkdir(parents=True, exist_ok=True)
    entry = {
        "packageId": package_id,
        "name": meta.get("name") or package_id,
        "version": meta.get("version") or "0.1.0",
        "provider": meta.get("provider") or "local",
        "packageKind": meta.get("packageKind") or "Compliance",
        "license": meta.get("license") or "MIT",
        "disclaimer": meta.get("disclaimer") or "",
        "spec": doc.get("spec") or {},
        "packageHash": package_hash(doc),
        "path": str(package_path.resolve()),
        "publishedAt": _now(),
        "kind": "GovernancePackage",
        "status": "published",
        "stars": 0,
        "downloads": 0,
    }
    (root / f"{package_id}.json").write_text(json.dumps(entry, indent=2), encoding="utf-8")
    dest = root / f"{package_id}.yaml"
    shutil.copy(package_path, dest)
    # also cache for ConstitutionRuntime provider resolve
    cache = workspace / ".uap" / "packages"
    cache.mkdir(parents=True, exist_ok=True)
    provider = entry["provider"]
    shutil.copy(package_path, cache / f"{provider}.yaml")
    return entry


def list_local_packages(workspace: Path) -> list[dict[str, Any]]:
    root = workspace / ".uap" / "package-registry"
    if not root.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(root.glob("*.json"))]


def search_packages(workspace: Path, q: str | None = None) -> list[dict[str, Any]]:
    rows = list_local_packages(workspace)
    # seed from repo examples if empty
    if not rows and REPO_PACKAGES.exists():
        for p in sorted(REPO_PACKAGES.glob("*.yaml")):
            try:
                rows.append(register_package_local(workspace, p))
            except Exception:
                continue
    if not q:
        return rows
    needle = q.lower()
    return [
        r
        for r in rows
        if needle in f"{r.get('name')} {r.get('provider')} {r.get('packageId')}".lower()
    ]


def pull_package(workspace: Path, provider: str, version: str | None = None) -> dict[str, Any]:
    """Pull package into workspace cache and optionally activate via ConstitutionRuntime."""
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(workspace)
    result = rt.load(provider=provider, version=version)
    entry = register_package_local(workspace, Path(result["binding"]["path"]))
    entry["binding"] = result["binding"]
    return entry
