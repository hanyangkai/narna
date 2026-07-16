from __future__ import annotations

import hashlib
from typing import Any

from .canon import canonical_json_bytes


ZERO_HASH = "sha256:" + ("0" * 64)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_obj(obj: Any) -> str:
    return "sha256:" + sha256_hex(canonical_json_bytes(obj))

