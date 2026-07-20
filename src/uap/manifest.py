"""narna.yaml Manifest — developer metadata that compiles to Constitution."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .constitution import load_constitution, write_constitution
from .ids import new_id
from .schemas import validator_for

POLICY_ALIASES: dict[str, dict[str, Any]] = {
    "human_approval": {
        "id": "human_for_irreversible",
        "effect": "ask",
        "when": "irreversible == true",
        "description": "Require human approval for irreversible actions",
    },
    "no_money_transfer": {
        "id": "no_money_transfer",
        "effect": "deny",
        "action": "wallet.transfer",
        "description": "Never transfer funds",
    },
    "no_delete_data": {
        "id": "no_delete_data",
        "effect": "deny",
        "action": "filesystem.delete",
        "description": "Never delete data",
    },
    "log_every_action": {
        "id": "log_every_action",
        "effect": "require",
        "evidence": "action_log",
        "description": "Log every action",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def discover_manifest(workspace: Path | None = None) -> Path | None:
    """Find narna.yaml / constitution.yaml in workspace."""
    root = Path(workspace) if workspace else Path.cwd()
    for rel in (
        "narna.yaml",
        "narna.yml",
        ".narna/narna.yaml",
        "constitution.yaml",
        "constitution.yml",
    ):
        p = root / rel
        if p.exists():
            return p
    return None


def load_manifest(path: str | Path, *, validate: bool = True) -> dict[str, Any]:
    p = Path(path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("manifest must be a mapping")
    kind = raw.get("kind")
    if kind == "Constitution":
        if validate:
            validator_for("constitution.schema.json").validate(raw)
        return raw
    if kind != "Manifest":
        # allow bare short forms missing kind by treating as Manifest if identity present
        if "identity" in raw and "kind" not in raw:
            raw = {**raw, "apiVersion": raw.get("apiVersion", "narna.ai/v1alpha1"), "kind": "Manifest"}
        else:
            raise ValueError(f"unsupported kind: {kind}")
    if validate:
        validator_for("manifest.schema.json").validate(raw)
    return raw


def compile_manifest_to_constitution(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compile short-form Manifest → full Constitution."""
    if manifest.get("kind") == "Constitution":
        return manifest

    meta = manifest.get("metadata") or {}
    ident = manifest.get("identity") or {}
    entity_id = str(ident.get("id") or new_id("agent"))
    # normalize entity id
    if not entity_id.startswith(("agent_", "tool_", "mcp_", "wf_")):
        entity_id = f"agent_{entity_id}".replace("-", "_")
    name = str(meta.get("name") or entity_id)
    owner = str(meta.get("owner") or "local")
    version = str(ident.get("version") or "0.1.0")
    caps = list(manifest.get("capabilities") or ["general"])
    # normalize capability tokens for constitution schema (lowercase snake)
    supports = [str(c).lower().replace(".", "_").replace("-", "_") for c in caps]

    grants: list[dict[str, Any]] = []
    for p in manifest.get("permissions") or []:
        if isinstance(p, str):
            grants.append({"name": p, "mode": "allow"})
        elif isinstance(p, dict) and p.get("name"):
            grants.append(
                {
                    "name": str(p["name"]),
                    "mode": str(p.get("mode") or "allow"),
                    **{k: v for k, v in p.items() if k in {"paths", "hosts"}},
                }
            )
    if not grants:
        grants = [{"name": "network", "mode": "allow"}]

    rules: list[dict[str, Any]] = []
    for alias in manifest.get("policies") or ["log_every_action", "human_approval"]:
        key = str(alias).lower()
        if key in POLICY_ALIASES:
            rules.append(dict(POLICY_ALIASES[key]))
        else:
            rules.append({"id": key, "effect": "require", "evidence": "action_log"})
    if not rules:
        rules.append(dict(POLICY_ALIASES["log_every_action"]))

    trust = manifest.get("trust") or {}
    min_score = float(trust.get("minimum_score", 0.7))

    compat_raw = manifest.get("compatibility") or []
    if isinstance(compat_raw, dict):
        compat_list = list(compat_raw.get("supports") or [])
    else:
        compat_list = list(compat_raw)
    compatibility: dict[str, bool] = {}
    for item in compat_list:
        compatibility[str(item).lower().replace("-", "")] = True

    return {
        "apiVersion": "narna.ai/v1alpha1",
        "kind": "Constitution",
        "metadata": {
            "id": new_id("const"),
            "name": f"{name} Constitution",
            "version": version,
            "entityKind": "Agent",
            "entityId": entity_id,
            "owner": owner,
            "createdAt": _now(),
            "license": "MIT",
            "labels": meta.get("labels") or {"source": "narna.yaml"},
        },
        "spec": {
            "identity": {
                "id": entity_id,
                "owner": owner,
                "version": version,
                "trustProfile": "vap-trust-v0",
            },
            "capability": {"supports": supports or ["general"]},
            "permission": {"grants": grants},
            "policy": {
                "ref": "narna.ai/policy/default@0.1.0",
                "rules": rules,
            },
            "humanReview": {
                "requiredFor": ["irreversible"],
                "timeoutSeconds": 3600,
                "onTimeout": "deny",
            },
            "evidence": {
                "mustLog": ["every_tool_call", "every_policy_decision"],
                "mustProve": ["side_effects"],
                "retentionDays": 90,
                "hashAlg": "sha256",
            },
            "trust": {
                "algorithm": "vap-trust-v0",
                "minScore": min_score,
                "inputs": ["evidence", "policy", "execution", "feedback"],
            },
            "governance": {
                "orgId": f"org_{owner}",
                "fleetId": "fleet_default",
                "roles": ["operator", "auditor"],
            },
            "compatibility": compatibility
            or {
                "opentelemetry": True,
                "mcp": True,
                "openaiAgents": True,
                "langgraph": True,
            },
        },
    }


def bind_governance_from_manifest(manifest: dict[str, Any], workspace: Path) -> dict[str, Any] | None:
    """Load Governance Package from manifest.governance or manifest.constitution binding."""
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(workspace)

    gov = manifest.get("governance")
    if isinstance(gov, dict):
        if gov.get("path"):
            return rt.load(path=gov["path"])
        if gov.get("ref"):
            return rt.load(ref=str(gov["ref"]))
        pkg = gov.get("package") or gov.get("provider")
        if pkg:
            pkg_s = str(pkg)
            if "@" in pkg_s:
                provider, version = pkg_s.split("@", 1)
            else:
                provider, version = pkg_s, gov.get("version")
            return rt.load(provider=provider, version=version)

    binding = manifest.get("constitution")
    if not isinstance(binding, dict):
        return None
    if binding.get("path"):
        return rt.load(path=binding["path"])
    if binding.get("ref"):
        return rt.load(ref=str(binding["ref"]))
    provider = binding.get("provider")
    if provider:
        return rt.load(provider=str(provider), version=binding.get("version"))
    return None


def load_or_compile_constitution(
    path: str | Path | None = None,
    *,
    workspace: Path | None = None,
    write_constitution_out: bool = True,
    bind_governance: bool = True,
) -> dict[str, Any]:
    """Discover narna.yaml, compile to Constitution, optionally write constitution.yaml."""
    p = Path(path) if path else discover_manifest(workspace)
    if p is None:
        raise FileNotFoundError("narna.yaml / constitution.yaml not found")
    root = Path(workspace) if workspace else p.parent
    doc = load_manifest(p)
    if doc.get("kind") == "Constitution":
        return doc
    if bind_governance and doc.get("kind") == "Manifest":
        try:
            bind_governance_from_manifest(doc, root)
        except Exception:
            pass
    constitution = compile_manifest_to_constitution(doc)
    validator_for("constitution.schema.json").validate(constitution)
    if write_constitution_out:
        write_constitution(root / "constitution.yaml", constitution)
    return constitution


def ensure_workspace_manifest(workspace: Path, *, agent_name: str = "Agent") -> Path:
    """Ensure narna.yaml exists (scaffold) for Borrow-the-Wave DX."""
    existing = discover_manifest(workspace)
    if existing and existing.name.startswith("narna"):
        return existing
    path = workspace / "narna.yaml"
    if path.exists():
        return path
    scaffold = {
        "apiVersion": "narna.ai/v1alpha1",
        "kind": "Manifest",
        "metadata": {"name": agent_name, "owner": "local"},
        "identity": {"id": agent_name.lower().replace(" ", "-"), "version": "0.1.0"},
        "capabilities": ["general", "reasoning"],
        "permissions": [{"name": "network", "mode": "allow"}],
        "policies": ["log_every_action", "human_approval"],
        "governance": {"package": "eu-ai-act@2.0.0"},
        "runtime": {"narna": True},
        "passport": {"enabled": True, "publish": False},
        "trust": {"enabled": True, "minimum_score": 0.7},
        "compatibility": ["openai", "mcp", "langgraph", "opentelemetry"],
    }
    path.write_text(yaml.safe_dump(scaffold, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path
