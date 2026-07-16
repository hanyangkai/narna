from __future__ import annotations

import json
from typing import Any


def canonical_json_bytes(obj: Any) -> bytes:
    """
    Canonical JSON for hashing (draft v0):
    - UTF-8
    - sorted keys
    - no insignificant whitespace
    - ensure_ascii=False
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )

