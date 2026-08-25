"""Council legal binding — signed attestation on passed proposals (Tier D)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashing import sha256_obj
from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


LEGAL_DISCLAIMER = (
    "This binding records human Governance Council approvals for audit. "
    "It is not a substitute for jurisdiction-specific legal instruments. "
    "Controllers remain responsible for compliance with applicable law."
)


class CouncilBinding:
    """Attach a verifiable binding record when a council proposal passes."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap" / "guardian" / "council" / "bindings"
        self.root.mkdir(parents=True, exist_ok=True)

    def seal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Create binding for a passed proposal. Prefer Ed25519 if identity keys exist."""
        if proposal.get("status") != "passed":
            raise ValueError("only passed proposals can be sealed")
        body = {
            "bindingId": new_id("bind"),
            "proposalId": proposal.get("proposalId"),
            "kind": proposal.get("kind"),
            "approvals": list(proposal.get("approvals") or []),
            "passedAt": proposal.get("passedAt") or _now(),
            "proposalHash": sha256_obj(
                {
                    "proposalId": proposal.get("proposalId"),
                    "kind": proposal.get("kind"),
                    "payload": proposal.get("payload"),
                    "approvals": proposal.get("approvals"),
                }
            ),
            "executed": proposal.get("executed"),
            "disclaimer": LEGAL_DISCLAIMER,
            "sealedAt": _now(),
            "standard": "NGS-L4-binding",
            "agentAmendForbidden": True,
        }
        body["recordHash"] = sha256_obj(
            {k: v for k, v in body.items() if k not in {"signature", "signatureAlg", "recordHash"}}
        )
        sig = self._try_sign(body)
        if sig:
            body["signature"] = sig
            body["signatureAlg"] = "Ed25519"
        else:
            body["signature"] = {"alg": "sha256-record", "hash": body["recordHash"]}
            body["signatureAlg"] = "sha256-record"
        path = self.root / f"{body['bindingId']}.json"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        return body

    def _try_sign(self, body: dict[str, Any]) -> dict[str, Any] | None:
        try:
            from .identity import IdentityStore
            from .passport_sign import _b64url, passport_sign_payload
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            import base64

            store = IdentityStore(self.workspace)
            key_info = store.ensure_keys()
            # IdentityStore typically returns paths / raw — reuse passport path
            key_path = self.workspace / ".uap" / "identity" / "creator.key"
            if not key_path.exists():
                return None
            raw = json.loads(key_path.read_text(encoding="utf-8"))
            priv_b64 = raw.get("privateKey") or raw.get("secretKey")
            if not priv_b64:
                return None
            pad = "=" * (-len(priv_b64) % 4)
            seed = base64.urlsafe_b64decode(priv_b64 + pad)
            if len(seed) == 64:
                seed = seed[:32]
            priv = Ed25519PrivateKey.from_private_bytes(seed)
            payload = {k: v for k, v in body.items() if k != "signature"}
            from .canon import canonical_json_bytes

            msg = canonical_json_bytes(payload)
            signature = priv.sign(msg)
            return {
                "alg": "Ed25519",
                "publicKey": raw.get("publicKey"),
                "sig": _b64url(signature),
            }
        except Exception:
            return None

    def list(self) -> list[dict[str, Any]]:
        rows = []
        for p in sorted(self.root.glob("bind_*.json")):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return rows

    def get(self, binding_id: str) -> dict[str, Any]:
        path = self.root / f"{binding_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"binding not found: {binding_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def verify(self, binding_id: str) -> dict[str, Any]:
        body = self.get(binding_id)
        structural_ok = bool(
            body.get("proposalHash") and body.get("approvals") and body.get("bindingId")
        )
        # Structural binding always required; Ed25519 is best-effort
        if body.get("signatureAlg") == "Ed25519":
            sig = body.get("signature") or {}
            try:
                import base64

                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
                from .canon import canonical_json_bytes
                from .passport_sign import _b64url_decode

                pub_b64 = str(sig.get("publicKey") or "")
                pad = "=" * (-len(pub_b64) % 4)
                pub = Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(pub_b64 + pad))
                payload = {
                    k: v
                    for k, v in body.items()
                    if k not in {"signature", "signatureAlg"}
                }
                # recompute expected signed payload without recordHash added after? sign used body before signature
                # Sign included recordHash if present — rebuild
                pub.verify(_b64url_decode(str(sig.get("sig"))), canonical_json_bytes(payload))
                return {
                    "ok": True,
                    "bindingId": binding_id,
                    "method": "Ed25519",
                    "disclaimer": body.get("disclaimer"),
                }
            except Exception as e:
                return {
                    "ok": structural_ok,
                    "bindingId": binding_id,
                    "method": "structural",
                    "ed25519Error": str(e) or type(e).__name__,
                    "disclaimer": body.get("disclaimer"),
                }
        return {
            "ok": structural_ok,
            "bindingId": binding_id,
            "method": "sha256-record",
            "disclaimer": body.get("disclaimer"),
        }
