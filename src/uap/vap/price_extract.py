from __future__ import annotations

import json
from typing import Any


def extract_price(evidence: dict[str, Any], content: bytes) -> float | None:
    try:
        data = json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if isinstance(data.get("data"), dict) and "amount" in data["data"]:
        return float(data["data"]["amount"])
    if "price" in data:
        return float(data["price"])
    if "amount" in data:
        return float(data["amount"])
    return None
