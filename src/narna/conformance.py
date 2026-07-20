"""UGS conformance checks — badge eligibility for Agent Passport / CI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_openapi_present() -> tuple[bool, str]:
    path = _repo_root() / "specs" / "governance-api" / "openapi.yaml"
    if not path.exists():
        return False, f"missing {path}"
    return True, str(path)


def check_schemas_present() -> tuple[bool, list[str]]:
    schema_dir = _repo_root() / "specs" / "schemas"
    required = [
        "passport.schema.json",
        "governance-package.schema.json",
        "manifest.schema.json",
    ]
    missing = [n for n in required if not (schema_dir / n).exists()]
    return len(missing) == 0, missing


def check_manifest(workspace: Path | None = None) -> tuple[bool, str]:
    ws = workspace or Path.cwd()
    from uap.manifest import discover_manifest

    found = discover_manifest(ws)
    if found is None:
        return False, "narna.yaml not found"
    return True, str(found)


def run_conformance(*, workspace: Path | None = None) -> dict[str, Any]:
    ws = workspace or Path.cwd()
    checks: list[dict[str, Any]] = []

    ok, detail = check_openapi_present()
    checks.append({"id": "openapi", "ok": ok, "detail": detail})

    ok, missing = check_schemas_present()
    checks.append({"id": "schemas", "ok": ok, "detail": missing or "ok"})

    ok, detail = check_manifest(ws)
    checks.append({"id": "manifest", "ok": ok, "detail": detail})

    try:
        from uap.agent import Agent

        agent = Agent(name="conformance-probe", workspace=ws, auto_init=True)
        checks.append({"id": "runtime", "ok": True, "detail": agent.spec.agent_id})
    except Exception as e:
        checks.append({"id": "runtime", "ok": False, "detail": str(e)})

    passed = all(c["ok"] for c in checks)
    return {
        "conformant": passed,
        "standard": "UGS",
        "version": "0.1.0",
        "badge": "UGS Conformant" if passed else None,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(prog="narna conformance")
    p.add_argument("--workspace", default=".", help="Workspace with narna.yaml")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    report = run_conformance(workspace=Path(args.workspace))
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "PASS" if report["conformant"] else "FAIL"
        print(f"UGS conformance: {status}")
        for c in report["checks"]:
            mark = "ok" if c["ok"] else "FAIL"
            print(f"  [{mark}] {c['id']}: {c['detail']}")
    return 0 if report["conformant"] else 1
