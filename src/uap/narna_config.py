"""NARNA local config — ~/.narna/config.json and config.yaml (Hermes-like lite)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


KNOWN_KEYS = (
    "provider",
    "apiKey",
    "baseUrl",
    "model",
    "shellBackend",
    "browserEnabled",
)


def default_home() -> Path:
    env = (os.environ.get("NARNA_HOME") or os.environ.get("UAP_HOME") or "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".narna"


def _json_path(home: Path) -> Path:
    return home / "config.json"


def _yaml_path(home: Path) -> Path:
    return home / "config.yaml"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_narna_config(home: Path | None = None) -> dict[str, Any]:
    """Merge YAML over JSON (YAML wins on key conflicts)."""
    root = Path(home) if home else default_home()
    cfg = _read_json(_json_path(root))
    yml = _read_yaml(_yaml_path(root))
    if yml:
        cfg = {**cfg, **yml}
    return cfg


def save_narna_config(data: dict[str, Any], home: Path | None = None, *, as_yaml: bool = False) -> Path:
    root = Path(home) if home else default_home()
    root.mkdir(parents=True, exist_ok=True)
    clean = {k: data[k] for k in KNOWN_KEYS if k in data and data[k] is not None}
    # preserve unknown keys from previous load
    prev = load_narna_config(root)
    merged = {**prev, **clean}
    if as_yaml or _yaml_path(root).exists():
        path = _yaml_path(root)
        try:
            import yaml  # type: ignore

            path.write_text(
                yaml.safe_dump(merged, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
        except Exception:
            path = _json_path(root)
            path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path
    path = _json_path(root)
    path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def config_set(key: str, value: str, home: Path | None = None) -> dict[str, Any]:
    aliases = {
        "apikey": "apiKey",
        "api_key": "apiKey",
        "baseurl": "baseUrl",
        "base_url": "baseUrl",
        "shellbackend": "shellBackend",
        "shell_backend": "shellBackend",
        "browserenabled": "browserEnabled",
        "browser_enabled": "browserEnabled",
    }
    k = aliases.get(key.strip().lower(), key.strip())
    if k not in KNOWN_KEYS:
        raise ValueError(f"unknown key: {key} (allowed: {', '.join(KNOWN_KEYS)})")
    cfg = load_narna_config(home)
    if k == "browserEnabled":
        cfg[k] = value.strip().lower() in {"1", "true", "yes", "on"}
    else:
        cfg[k] = value
    path = save_narna_config(cfg, home)
    # Apply shell/browser to process env for this session
    if k == "shellBackend":
        os.environ["UAP_SHELL_BACKEND"] = str(value)
    if k == "browserEnabled":
        os.environ["UAP_BROWSER_ENABLED"] = "1" if cfg[k] else "0"
    return {"ok": True, "key": k, "path": str(path), "config": {**cfg, "apiKey": _mask(cfg.get("apiKey"))}}


def config_show(home: Path | None = None) -> dict[str, Any]:
    cfg = load_narna_config(home)
    root = Path(home) if home else default_home()
    return {
        "ok": True,
        "home": str(root),
        "json": str(_json_path(root)),
        "yaml": str(_yaml_path(root)),
        "config": {**cfg, "apiKey": _mask(cfg.get("apiKey"))},
    }


def _mask(key: Any) -> str | None:
    if not key:
        return None
    s = str(key)
    if len(s) <= 8:
        return "***"
    return s[:4] + "…" + s[-4:]


def apply_config_to_env(home: Path | None = None) -> dict[str, Any]:
    cfg = load_narna_config(home)
    if cfg.get("shellBackend"):
        os.environ.setdefault("UAP_SHELL_BACKEND", str(cfg["shellBackend"]))
    if "browserEnabled" in cfg:
        os.environ.setdefault(
            "UAP_BROWSER_ENABLED",
            "1" if cfg.get("browserEnabled") else "0",
        )
    return cfg
