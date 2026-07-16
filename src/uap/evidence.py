from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .canon import canonical_json_bytes
from .hashing import sha256_hex
from .ids import new_id
from .schemas import validator_for


def _now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class EvidenceStore:
    def __init__(self, workspace: Path) -> None:
        self.root = workspace / ".uap" / "evidence"
        self.root.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        *,
        evidence_type: str,
        content: dict[str, Any] | bytes,
        source: dict[str, Any],
        provenance: dict[str, Any],
        verifiers: list[str] | None = None,
        media_type: str = "application/json",
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        evidence_id = new_id("ev")
        if isinstance(content, dict):
            content_bytes = canonical_json_bytes(content)
            media_type = "application/json"
        else:
            content_bytes = content

        content_hash = "sha256:" + sha256_hex(content_bytes)
        blob_path = self.root / f"{evidence_id}.bin"
        blob_path.write_bytes(content_bytes)

        evidence = {
            "evidenceId": evidence_id,
            "type": evidence_type,
            "source": source,
            "capturedAt": _now_rfc3339(),
            "contentHash": content_hash,
            "contentUri": str(blob_path.as_uri()),
            "mediaType": media_type,
            "sizeBytes": len(content_bytes),
            "verifiers": verifiers or ["hash_match", "freshness"],
            "provenance": provenance,
        }
        if expires_at:
            evidence["expiresAt"] = expires_at

        validator_for("evidence.schema.json").validate(evidence)
        meta_path = self.root / f"{evidence_id}.json"
        meta_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        return evidence

    def load(self, evidence_id: str) -> tuple[dict[str, Any], bytes]:
        meta_path = self.root / f"{evidence_id}.json"
        if not meta_path.exists():
            raise FileNotFoundError(evidence_id)
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        blob = (self.root / f"{evidence_id}.bin").read_bytes()
        return meta, blob
