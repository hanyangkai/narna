from __future__ import annotations

import fnmatch
from typing import Any


def _as_float(value: Any) -> float | None:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def check_constraints(
    constraints: dict[str, Any] | None,
    parameters: dict[str, Any],
) -> tuple[bool, list[str]]:
    if not constraints:
        return True, []
    reasons: list[str] = []

    if "maxAmount" in constraints:
        amount = _as_float(parameters.get("amount"))
        max_amount = _as_float(constraints["maxAmount"])
        if amount is None or max_amount is None or amount > max_amount:
            reasons.append(f"amount exceeds maxAmount {constraints['maxAmount']}")

    if "currency" in constraints:
        if str(parameters.get("currency", "")).upper() != str(constraints["currency"]).upper():
            reasons.append(f"currency must be {constraints['currency']}")

    if "domainsAllowlist" in constraints:
        url = str(parameters.get("url", parameters.get("domain", "")))
        patterns = constraints["domainsAllowlist"]
        if not any(fnmatch.fnmatch(url, p) for p in patterns):
            reasons.append("domain not in allowlist")

    if "recipientsAllowlist" in constraints:
        recipient = str(parameters.get("recipient", ""))
        if recipient not in constraints["recipientsAllowlist"]:
            reasons.append("recipient not in allowlist")

    if "pathPrefix" in constraints:
        path = str(parameters.get("path", ""))
        prefix = str(constraints["pathPrefix"])
        if not path.startswith(prefix):
            reasons.append(f"path must start with {prefix}")

    return len(reasons) == 0, reasons


def find_grant(permissions: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for p in permissions:
        if p.get("name") == name:
            return p
    return None
