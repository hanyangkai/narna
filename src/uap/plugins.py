"""Plugin economy — load, list, publish community plugins."""

from __future__ import annotations

import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_plugin_manifest(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if p.is_dir():
        for name in ("narna-plugin.yaml", "narna-plugin.yml", "plugin.yaml"):
            cand = p / name
            if cand.exists():
                p = cand
                break
    doc = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("kind") != "Plugin":
        raise ValueError("plugin manifest must have kind: Plugin")
    return doc


def discover_plugins(root: Path | None = None) -> list[dict[str, Any]]:
    """Scan plugins/ directory for manifests."""
    base = root or Path.cwd() / "plugins"
    if not base.exists():
        return []
    out: list[dict[str, Any]] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name in {"TEMPLATE"}:
            continue
        try:
            manifest = load_plugin_manifest(child)
            meta = manifest.get("metadata") or {}
            out.append(
                {
                    "id": meta.get("id") or child.name,
                    "name": meta.get("name") or child.name,
                    "version": meta.get("version") or "0.1.0",
                    "path": str(child),
                    "manifestPath": str(child / "narna-plugin.yaml"),
                    "spec": manifest.get("spec") or {},
                }
            )
        except Exception:
            continue
    return out


def register_plugin_local(
    workspace: Path,
    plugin_dir: Path,
    *,
    stars: int = 0,
    downloads: int = 0,
) -> dict[str, Any]:
    """Register plugin into local .uap/plugins registry."""
    manifest = load_plugin_manifest(plugin_dir)
    meta = manifest.get("metadata") or {}
    plugin_id = str(meta.get("id") or plugin_dir.name)
    root = workspace / ".uap" / "plugins"
    root.mkdir(parents=True, exist_ok=True)
    entry = {
        "pluginId": plugin_id,
        "name": meta.get("name") or plugin_id,
        "version": meta.get("version") or "0.1.0",
        "license": meta.get("license") or "MIT",
        "spec": manifest.get("spec") or {},
        "path": str(plugin_dir.resolve()),
        "stars": stars,
        "downloads": downloads,
        "publishedAt": _now(),
        "kind": "Plugin",
        "status": "published",
    }
    existing = root / f"{plugin_id}.json"
    if existing.exists():
        prev = json.loads(existing.read_text(encoding="utf-8"))
        entry["stars"] = max(int(prev.get("stars") or 0), stars)
        entry["downloads"] = max(int(prev.get("downloads") or 0), downloads)
    existing.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    # copy manifest for offline browse
    shutil.copy(plugin_dir / "narna-plugin.yaml", root / f"{plugin_id}.yaml")
    return entry


def list_local_plugins(workspace: Path) -> list[dict[str, Any]]:
    root = workspace / ".uap" / "plugins"
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for p in sorted(root.glob("*.json")):
        rows.append(json.loads(p.read_text(encoding="utf-8")))
    return rows


def load_plugin_module(plugin_dir: Path) -> Any:
    """Import plugin entrypoint module (best-effort)."""
    manifest = load_plugin_manifest(plugin_dir)
    entry = (manifest.get("spec") or {}).get("entrypoint") or "src/plugin.py"
    path = plugin_dir / entry
    if not path.exists():
        raise FileNotFoundError(f"entrypoint not found: {path}")
    spec = importlib.util.spec_from_file_location(f"narna_plugin_{plugin_dir.name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load plugin: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def attach_plugin(agent: Any, plugin_dir: Path) -> dict[str, Any]:
    mod = load_plugin_module(plugin_dir)
    if hasattr(mod, "register"):
        return mod.register(agent)
    return {"ok": True, "plugin": plugin_dir.name, "message": "loaded (no register())"}
