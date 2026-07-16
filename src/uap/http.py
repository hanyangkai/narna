from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def is_live_mode() -> bool:
    return os.environ.get("UAP_TOOL_MODE", "mock").lower() == "live"


def http_get_json(url: str, *, timeout: float = 10.0) -> tuple[dict[str, Any], bytes, int]:
    req = urllib.request.Request(url, headers={"User-Agent": "uap-sdk/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        status = getattr(resp, "status", 200)
        return json.loads(raw.decode("utf-8")), raw, int(status)
