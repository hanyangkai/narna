from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from .canon import canonical_json_bytes
from .hashing import sha256_obj
from .ids import new_id
from .schemas import validator_for
from .spec import AgentSpec

ENTITY_KINDS = (
    "Agent",
    "Tool",
    "McpServer",
    "Workflow",
    "Prompt",
    "Dataset",
    "Plugin",
    "Memory",
    "ModelBinding",
)


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def spec_hash(spec: AgentSpec) -> str:
    return sha256_obj(spec.raw)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


class IdentityStore:
    """Issues Agent identity (legacy) and Universal AI Identity (C1)."""

    def __init__(self, workspace: Path) -> None:
        self.root = workspace / ".uap" / "identity"
        self.key_path = self.root / "creator.key"
        self.identity_path = self.root / "identity.json"
        self.entities_dir = self.root / "entities"

    def ensure_keys(self) -> Ed25519PrivateKey:
        self.root.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            raw = json.loads(self.key_path.read_text(encoding="utf-8"))
            return Ed25519PrivateKey.from_private_bytes(
                base64.urlsafe_b64decode(raw["privateKey"] + "==")
            )
        key = Ed25519PrivateKey.generate()
        self.key_path.write_text(
            json.dumps(
                {
                    "alg": "ed25519",
                    "privateKey": _b64url(key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())),
                    "publicKey": _b64url(
                        key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
                    ),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return key

    def issue(self, spec: AgentSpec, *, creator: str | None = None) -> dict[str, Any]:
        """Legacy Agent identity + Universal Identity dual-write."""
        key = self.ensure_keys()
        creator_id = creator or str(spec.raw["metadata"]["creator"])
        content = spec_hash(spec)
        payload = {
            "agentId": spec.agent_id,
            "creator": creator_id,
            "createdAt": str(spec.raw["metadata"]["createdAt"]),
            "version": spec.version,
            "specHash": content,
        }
        sig = key.sign(canonical_json_bytes(payload))
        identity = {
            **payload,
            "signature": {
                "alg": "ed25519",
                "keyId": f"creator:{creator_id}",
                "value": _b64url(sig),
            },
        }
        self.identity_path.write_text(json.dumps(identity, indent=2), encoding="utf-8")

        # C1: also issue universal form
        self.issue_entity(
            kind="Agent",
            entity_id=spec.agent_id,
            owner=creator_id,
            version=spec.version,
            content_hash=content,
            created_at=str(spec.raw["metadata"]["createdAt"]),
            origin=None,
            license=None,
            constitution_id=None,
            dual_write_agent=False,  # already wrote identity.json
        )
        return identity

    def issue_entity(
        self,
        *,
        kind: str,
        entity_id: str,
        owner: str,
        version: str,
        content_hash: str,
        created_at: str | None = None,
        origin: str | None = None,
        license: str | None = None,
        constitution_id: str | None = None,
        labels: dict[str, str] | None = None,
        supersedes: str | None = None,
        validate: bool = True,
        dual_write_agent: bool = True,
    ) -> dict[str, Any]:
        """Issue Universal AI Identity for any entity kind (C1)."""
        if kind not in ENTITY_KINDS:
            raise ValueError(f"unsupported entity kind: {kind}")
        if not content_hash.startswith("sha256:"):
            raise ValueError("content_hash must be sha256:<hex>")

        key = self.ensure_keys()
        created = created_at or _now_rfc3339()
        identity_id = new_id("idnt")

        sign_payload = {
            "identityId": identity_id,
            "entityId": entity_id,
            "kind": kind,
            "owner": owner,
            "version": version,
            "createdAt": created,
            "contentHash": content_hash,
        }
        if constitution_id:
            sign_payload["constitutionId"] = constitution_id
        if origin:
            sign_payload["origin"] = origin
        if license:
            sign_payload["license"] = license
        if supersedes:
            sign_payload["supersedes"] = supersedes

        sig = key.sign(canonical_json_bytes(sign_payload))
        identity: dict[str, Any] = {
            **sign_payload,
            "signature": {
                "alg": "ed25519",
                "keyId": f"creator:{owner}",
                "value": _b64url(sig),
            },
        }
        if labels:
            identity["labels"] = labels

        # Dual-write legacy Agent fields for passport / older readers
        if kind == "Agent":
            identity["agentId"] = entity_id
            identity["creator"] = owner
            identity["specHash"] = content_hash
            if dual_write_agent:
                legacy = {
                    "agentId": entity_id,
                    "creator": owner,
                    "createdAt": created,
                    "version": version,
                    "specHash": content_hash,
                    "signature": identity["signature"],
                }
                self.identity_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")

        if validate:
            validator_for("universal-identity.schema.json").validate(identity)

        self.entities_dir.mkdir(parents=True, exist_ok=True)
        out = self.entities_dir / f"{entity_id}.json"
        out.write_text(json.dumps(identity, indent=2), encoding="utf-8")
        return identity

    def load(self) -> dict[str, Any] | None:
        if not self.identity_path.exists():
            return None
        return json.loads(self.identity_path.read_text(encoding="utf-8"))

    def load_entity(self, entity_id: str) -> dict[str, Any] | None:
        path = self.entities_dir / f"{entity_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        # fall back to agent identity.json
        legacy = self.load()
        if legacy and legacy.get("agentId") == entity_id:
            return legacy
        return None

    def list_entities(self) -> list[dict[str, Any]]:
        if not self.entities_dir.exists():
            return []
        rows: list[dict[str, Any]] = []
        for p in sorted(self.entities_dir.glob("*.json")):
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        return rows
