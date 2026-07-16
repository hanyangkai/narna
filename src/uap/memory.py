from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalMemoryAdapter:
    def __init__(self, workspace: Path, agent_id: str) -> None:
        self.path = workspace / ".uap" / "memory" / f"{agent_id}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def read(self, keys: list[str] | None = None) -> dict[str, Any]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if keys is None:
            return data
        return {k: data[k] for k in keys if k in data}

    def write(self, records: dict[str, Any]) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data.update(records)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
