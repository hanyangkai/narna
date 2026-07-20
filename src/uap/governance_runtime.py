"""Constitution Runtime — Load → Execute → Verify → Audit → Version → Switch.

Reference implementation of specs/constitution-runtime/SPEC.md.
Not an agent/model executor — governance enforcement above host frameworks.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .fleet import load_fleet, member_role, role_denies
from .hashing import sha256_obj
from .verify import verify_proof_bundle

REPO_PACKAGES = Path(__file__).resolve().parents[2] / "specs" / "examples" / "packages"
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "specs" / "schemas" / "governance-package.schema.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _binding_path(workspace: Path) -> Path:
    return workspace / ".uap" / "runtime" / "active-governance.json"


def _validate_package(doc: dict[str, Any]) -> None:
    if doc.get("kind") not in {"GovernancePackage", "Constitution"}:
        raise ValueError("document must be kind GovernancePackage or Constitution")
    if doc.get("kind") == "GovernancePackage" and SCHEMA_PATH.exists():
        try:
            import jsonschema

            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
            jsonschema.validate(doc, schema)
        except ImportError:
            pass


def package_hash(doc: dict[str, Any]) -> str:
    return sha256_obj(doc)


def load_package_file(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("package must be a mapping")
    _validate_package(raw)
    return raw


def resolve_provider_package(
    provider: str,
    version: str | None = None,
    *,
    workspace: Path | None = None,
) -> Path:
    """Resolve provider@version from local cache, workspace, or repo examples."""
    candidates: list[Path] = []
    ws = workspace or Path.cwd()
    cache = ws / ".uap" / "packages"
    if cache.exists():
        for p in cache.glob("*.yaml"):
            candidates.append(p)
    # workspace packages/
    for root in (ws / "packages", ws / "specs" / "examples" / "packages", REPO_PACKAGES):
        if root.exists():
            candidates.extend(sorted(root.glob("*.yaml")))
    # also match by filename slug
    slug_hits = [
        REPO_PACKAGES / f"{provider}.yaml",
        REPO_PACKAGES / f"{provider}-constitution.yaml",
        cache / f"{provider}.yaml",
    ]
    for hit in slug_hits:
        if hit.exists() and hit not in candidates:
            candidates.insert(0, hit)

    for path in candidates:
        try:
            doc = load_package_file(path)
        except Exception:
            continue
        meta = doc.get("metadata") or {}
        if str(meta.get("provider", "")).lower() != provider.lower():
            # filename fallback
            if provider.lower() not in path.stem.lower():
                continue
        if version and str(meta.get("version")) != str(version):
            # allow major match (2.0.0 vs 2.0) and provider-latest when major differs
            meta_v = str(meta.get("version") or "")
            req_v = str(version)
            if meta_v.split(".")[0] == req_v.split(".")[0]:
                return path
            # Prefer exact provider match even if version drifted (DX); caller can pin path
            if provider.lower() in path.stem.lower() or str(meta.get("provider", "")).lower() == provider.lower():
                # keep scanning for exact; fall through to last matching provider
                continue
            continue
        return path
    # Fallback: any package for provider (ignore version pin) — last resort for scaffold DX
    if version:
        for path in candidates:
            try:
                doc = load_package_file(path)
            except Exception:
                continue
            meta = doc.get("metadata") or {}
            if str(meta.get("provider", "")).lower() == provider.lower() or provider.lower() in path.stem.lower():
                return path
    raise FileNotFoundError(f"governance package not found: provider={provider} version={version}")


def extract_rules(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect enforceable rules from GovernancePackage or Constitution."""
    rules: list[dict[str, Any]] = []
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind == "GovernancePackage":
        rules.extend(spec.get("rules") or [])
        embedded = spec.get("constitution") or {}
        if isinstance(embedded, dict):
            pol = embedded.get("policy") or {}
            rules.extend(pol.get("rules") or [])
    elif kind == "Constitution":
        pol = spec.get("policy") or {}
        rules.extend(pol.get("rules") or [])
    return rules


def match_rule(rules: list[dict[str, Any]], action: str) -> dict[str, Any] | None:
    """Find most specific matching rule; prefer deny > ask/require > allow."""
    action_l = action.lower()
    matched: list[dict[str, Any]] = []
    for r in rules:
        target = (r.get("action") or r.get("permission") or "").lower()
        if not target:
            continue
        if target == action_l or action_l.startswith(target) or target in action_l:
            matched.append(r)
    if not matched:
        return None
    order = {"deny": 0, "require": 1, "ask": 2, "allow": 3}
    matched.sort(key=lambda r: order.get(str(r.get("effect", "")).lower(), 9))
    return matched[0]


class ConstitutionRuntime:
    """Reference Constitution Runtime (Governance Runtime core loop)."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def load(
        self,
        *,
        path: str | Path | None = None,
        provider: str | None = None,
        version: str | None = None,
        ref: str | None = None,
        constitution_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Load a Governance Package or Constitution and set active binding."""
        source = "path"
        resolved: Path | None = None
        doc: dict[str, Any]

        if ref:
            if ref.startswith("registry://"):
                # local pull cache by last path segment
                name = ref.rstrip("/").split("/")[-1].split("@")[0]
                provider = provider or name
                source = "registry"
            else:
                resolved = Path(ref)
                source = "path"

        if path:
            resolved = Path(path)
            source = "path"
        elif constitution_path:
            resolved = Path(constitution_path)
            source = "constitution"
        elif provider:
            resolved = resolve_provider_package(provider, version, workspace=self.workspace)
            source = "provider"

        if resolved is None:
            # default: local constitution.yaml
            cand = self.workspace / "constitution.yaml"
            if cand.exists():
                resolved = cand
                source = "constitution"
            else:
                raise FileNotFoundError("no package path/provider/constitution to load")

        doc = load_package_file(resolved)
        meta = doc.get("metadata") or {}
        binding = {
            "packageId": meta.get("id") or resolved.stem,
            "provider": meta.get("provider") or provider or "local",
            "version": meta.get("version") or version or "0.0.0",
            "packageHash": package_hash(doc),
            "source": source,
            "path": str(resolved.resolve()),
            "packageKind": meta.get("packageKind") or doc.get("kind"),
            "switchedAt": _now(),
            "supports": (doc.get("spec") or {}).get("supports") or [],
        }
        bp = _binding_path(self.workspace)
        bp.parent.mkdir(parents=True, exist_ok=True)
        bp.write_text(json.dumps(binding, indent=2), encoding="utf-8")
        # cache copy
        cache = self.workspace / ".uap" / "packages"
        cache.mkdir(parents=True, exist_ok=True)
        cache_file = cache / f"{binding['provider']}.yaml"
        cache_file.write_text(resolved.read_text(encoding="utf-8"), encoding="utf-8")
        return {"ok": True, "binding": binding, "document": doc}

    def active(self) -> dict[str, Any] | None:
        bp = _binding_path(self.workspace)
        if not bp.exists():
            return None
        return json.loads(bp.read_text(encoding="utf-8"))

    def active_document(self) -> dict[str, Any] | None:
        binding = self.active()
        if not binding or not binding.get("path"):
            return None
        path = Path(binding["path"])
        if not path.exists():
            return None
        return load_package_file(path)

    def switch(
        self,
        *,
        path: str | Path | None = None,
        provider: str | None = None,
        version: str | None = None,
    ) -> dict[str, Any]:
        """Switch active Governance Package (Version + Switch)."""
        prev = self.active()
        result = self.load(path=path, provider=provider, version=version)
        result["previous"] = prev
        return result

    def execute(
        self,
        *,
        action: str,
        agent_id: str | None = None,
        fleet_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Authorize action against active package rules + fleet denies."""
        binding = self.active()
        doc = self.active_document()
        reasons: list[str] = []
        decision = "allow"

        if doc is not None:
            rules = extract_rules(doc)
            rule = match_rule(rules, action)
            if rule is not None:
                effect = str(rule.get("effect", "deny")).lower()
                if effect == "deny":
                    decision = "deny"
                    reasons.append(f"package rule {rule.get('id')}: deny")
                elif effect in {"ask", "require"}:
                    decision = "ask"
                    reasons.append(f"package rule {rule.get('id')}: {effect}")
                else:
                    decision = "allow"
                    reasons.append(f"package rule {rule.get('id')}: allow")

        # Fleet denies
        fleet_file = Path(fleet_path) if fleet_path else self.workspace / "fleet.yaml"
        if fleet_file.exists() and agent_id:
            try:
                fleet = load_fleet(fleet_file)
                role = member_role(fleet, agent_id)
                denied = role_denies(fleet, role)
                for d in denied:
                    if d == action or action.startswith(d) or d in action:
                        decision = "deny"
                        reasons.append(f"fleet role {role} denies {d}")
                        break
            except Exception as e:
                reasons.append(f"fleet skip: {e}")

        if not reasons:
            reasons.append("no matching package rule — defer to PolicyEngine")

        return {
            "decision": decision,
            "action": action,
            "reasons": reasons,
            "packageId": (binding or {}).get("packageId"),
            "packageHash": (binding or {}).get("packageHash"),
            "provider": (binding or {}).get("provider"),
            "version": (binding or {}).get("version"),
        }

    def verify(self, bundle: dict[str, Any]) -> dict[str, Any]:
        binding = self.active() or {}
        ok, problems = verify_proof_bundle(bundle)
        return {
            "ok": ok,
            "problems": problems,
            "packageId": binding.get("packageId"),
            "packageHash": binding.get("packageHash"),
            "provider": binding.get("provider"),
            "version": binding.get("version"),
        }

    def audit(self, run_record: dict[str, Any] | None = None) -> dict[str, Any]:
        binding = self.active() or {}
        return {
            "packageId": binding.get("packageId"),
            "provider": binding.get("provider"),
            "version": binding.get("version"),
            "packageHash": binding.get("packageHash"),
            "run": run_record,
            "auditedAt": _now(),
        }

    def list_local(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for root in (
            self.workspace / ".uap" / "packages",
            self.workspace / "packages",
            REPO_PACKAGES,
        ):
            if not root.exists():
                continue
            for p in sorted(root.glob("*.yaml")):
                try:
                    doc = load_package_file(p)
                    meta = doc.get("metadata") or {}
                    rows.append(
                        {
                            "path": str(p),
                            "packageId": meta.get("id"),
                            "provider": meta.get("provider"),
                            "version": meta.get("version"),
                            "packageKind": meta.get("packageKind"),
                            "supports": (doc.get("spec") or {}).get("supports") or [],
                        }
                    )
                except Exception:
                    continue
        return rows


# Alias for strategy naming
GovernanceRuntime = ConstitutionRuntime
