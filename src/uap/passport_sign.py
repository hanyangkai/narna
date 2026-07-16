"""Passport Ed25519 signing and offline verification."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .canon import canonical_json_bytes


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def passport_sign_payload(passport: dict[str, Any]) -> dict[str, Any]:
    """Canonical unsigned passport body for signing."""
    return {k: v for k, v in passport.items() if k != "signature"}


def load_public_key_b64(workspace: Path) -> str | None:
    key_path = workspace / ".uap" / "identity" / "creator.key"
    if not key_path.exists():
        return None
    raw = json.loads(key_path.read_text(encoding="utf-8"))
    return str(raw.get("publicKey") or "")


def sign_passport(passport: dict[str, Any], workspace: Path) -> dict[str, Any]:
    """Attach Ed25519 signature using workspace creator key."""
    from .identity import IdentityStore

    store = IdentityStore(workspace)
    key = store.ensure_keys()
    owner = (
        passport.get("identity", {}).get("creator")
        or passport.get("identity", {}).get("owner")
        or "local"
    )
    payload = passport_sign_payload(passport)
    sig = key.sign(canonical_json_bytes(payload))
    pubkey = load_public_key_b64(workspace) or _b64url(
        key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    )
    signed = {
        **passport,
        "signature": {
            "alg": "ed25519",
            "keyId": f"creator:{owner}",
            "value": _b64url(sig),
            "publicKey": pubkey,
        },
    }
    return signed


def verify_passport_signature(
    passport: dict[str, Any],
    *,
    workspace: Path | None = None,
    public_key_b64: str | None = None,
) -> tuple[bool, list[str]]:
    """Verify passport Ed25519 signature offline."""
    sig_block = passport.get("signature")
    if not isinstance(sig_block, dict):
        return False, ["missing signature"]

    pubkey_b64 = public_key_b64 or sig_block.get("publicKey")
    if not pubkey_b64 and workspace is not None:
        pubkey_b64 = load_public_key_b64(workspace)
    if not pubkey_b64:
        return False, ["missing publicKey for verification"]

    try:
        pub = Ed25519PublicKey.from_public_bytes(_b64url_decode(str(pubkey_b64)))
        payload = passport_sign_payload(passport)
        pub.verify(_b64url_decode(str(sig_block.get("value") or "")), canonical_json_bytes(payload))
        return True, []
    except InvalidSignature:
        return False, ["invalid signature"]
    except Exception as e:
        return False, [f"verify error: {e}"]
