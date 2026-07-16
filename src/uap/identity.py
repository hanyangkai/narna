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
from .spec import AgentSpec


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def spec_hash(spec: AgentSpec) -> str:
    return sha256_obj(spec.raw)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


class IdentityStore:
    def __init__(self, workspace: Path) -> None:
        self.root = workspace / ".uap" / "identity"
        self.key_path = self.root / "creator.key"
        self.identity_path = self.root / "identity.json"

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
        key = self.ensure_keys()
        creator_id = creator or str(spec.raw["metadata"]["creator"])
        payload = {
            "agentId": spec.agent_id,
            "creator": creator_id,
            "createdAt": str(spec.raw["metadata"]["createdAt"]),
            "version": spec.version,
            "specHash": spec_hash(spec),
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
        return identity

    def load(self) -> dict[str, Any] | None:
        if not self.identity_path.exists():
            return None
        return json.loads(self.identity_path.read_text(encoding="utf-8"))
