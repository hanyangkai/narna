"""Load and validate NARNA Constitution documents (spec-first)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .schemas import validator_for


def load_constitution(path: str | Path, *, validate: bool = True) -> dict[str, Any]:
    """Load ``constitution.yaml`` / ``.json`` and optionally schema-validate.

    Spec: ``specs/constitution/SPEC.md``
    """
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        import json

        doc = json.loads(raw)
    else:
        doc = yaml.safe_load(raw)
    if not isinstance(doc, dict):
        raise ValueError("constitution must be a mapping")
    if validate:
        validator_for("constitution.schema.json").validate(doc)
    return doc


def default_constitution_for_agent(
    *,
    agent_id: str,
    name: str,
    owner: str = "local",
    supports: list[str] | None = None,
) -> dict[str, Any]:
    """Minimal Constitution document for an Agent entity (offline scaffold)."""
    from datetime import datetime, timezone

    from .ids import new_id

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    caps = supports or ["general"]
    return {
        "apiVersion": "narna.ai/v1alpha1",
        "kind": "Constitution",
        "metadata": {
            "id": new_id("const"),
            "name": f"{name} Constitution",
            "version": "0.1.0",
            "entityKind": "Agent",
            "entityId": agent_id,
            "owner": owner,
            "createdAt": now,
            "license": "MIT",
        },
        "spec": {
            "identity": {
                "id": agent_id,
                "owner": owner,
                "version": "0.1.0",
                "trustProfile": "vap-trust-v0",
            },
            "capability": {"supports": caps},
            "permission": {
                "grants": [{"name": "network", "mode": "allow"}],
            },
            "policy": {
                "ref": "narna.ai/policy/default@0.1.0",
                "rules": [
                    {
                        "id": "log_every_action",
                        "effect": "require",
                        "evidence": "action_log",
                    },
                    {
                        "id": "human_for_irreversible",
                        "effect": "ask",
                        "when": "irreversible == true",
                    },
                ],
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
                "minScore": 0.7,
                "inputs": ["evidence", "policy", "execution", "feedback"],
            },
            "governance": {
                "orgId": f"org_{owner}",
                "fleetId": "fleet_default",
                "roles": ["operator", "auditor"],
            },
            "compatibility": {
                "opentelemetry": True,
                "mcp": True,
                "openaiAgents": True,
                "langgraph": True,
                "crewai": True,
            },
        },
    }


def write_constitution(path: str | Path, doc: dict[str, Any], *, validate: bool = True) -> Path:
    p = Path(path)
    if validate:
        validator_for("constitution.schema.json").validate(doc)
    p.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return p
