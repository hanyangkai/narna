"""Knowledge graph — Decision OS entities & relations (v0 file store)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import new_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class KnowledgeGraph:
    """Lightweight entity-relation store under .uap/knowledge/."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.path = self.workspace / ".uap" / "knowledge" / "graph.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"entities": {}, "relations": []}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def upsert_entity(
        self,
        *,
        kind: str,
        name: str,
        props: dict[str, Any] | None = None,
        entity_id: str | None = None,
    ) -> dict[str, Any]:
        data = self._read()
        eid = entity_id or new_id("ent")
        row = {
            "entityId": eid,
            "kind": kind,
            "name": name,
            "props": props or {},
            "updatedAt": _now(),
        }
        data.setdefault("entities", {})[eid] = row
        self._write(data)
        return row

    def relate(
        self,
        *,
        from_id: str,
        to_id: str,
        rel_type: str,
        props: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = self._read()
        if from_id not in (data.get("entities") or {}) or to_id not in (data.get("entities") or {}):
            raise KeyError("both entities must exist before relating")
        edge = {
            "relationId": new_id("rel"),
            "from": from_id,
            "to": to_id,
            "type": rel_type,
            "props": props or {},
            "createdAt": _now(),
        }
        data.setdefault("relations", []).append(edge)
        self._write(data)
        return edge

    def get(self, entity_id: str) -> dict[str, Any] | None:
        return (self._read().get("entities") or {}).get(entity_id)

    def query(
        self,
        *,
        kind: str | None = None,
        name_contains: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        data = self._read()
        rows = list((data.get("entities") or {}).values())
        if kind:
            rows = [r for r in rows if r.get("kind") == kind]
        if name_contains:
            needle = name_contains.lower()
            rows = [r for r in rows if needle in str(r.get("name") or "").lower()]
        return rows[:limit]

    def observe_message(self, message: str) -> list[dict[str, Any]]:
        """Keyword-lite entity extraction into the project knowledge graph."""
        import re

        msg = (message or "").strip()
        if not msg:
            return []
        created: list[dict[str, Any]] = []
        # "project X" / "working on X"
        for pat, kind in (
            (r"(?:working on|building)\s+(?:project\s+|repo\s+)?([A-Za-z0-9._/-]{2,40})", "project"),
            (r"(?:project|repo|đang làm)\s+([A-Za-z0-9._/-]{2,40})", "project"),
            (r"(?:customer|client|khách)\s+([A-Za-z0-9 ._-]{2,40})", "customer"),
        ):
            for m in re.finditer(pat, msg, flags=re.I):
                name = m.group(1).strip(" .,;:")
                if len(name) < 2 or name.lower() in {"project", "repo", "the", "a", "an"}:
                    continue
                # Avoid dupes by name+kind
                existing = self.query(kind=kind, name_contains=name, limit=5)
                if any(str(e.get("name") or "").lower() == name.lower() for e in existing):
                    continue
                created.append(self.upsert_entity(kind=kind, name=name, props={"source": "observe"}))
        return created[:5]

    def neighbors(self, entity_id: str) -> dict[str, Any]:
        data = self._read()
        edges = [
            e
            for e in (data.get("relations") or [])
            if e.get("from") == entity_id or e.get("to") == entity_id
        ]
        ids = set()
        for e in edges:
            ids.add(e["from"])
            ids.add(e["to"])
        ids.discard(entity_id)
        ents = {i: (data.get("entities") or {}).get(i) for i in ids}
        return {"entityId": entity_id, "relations": edges, "neighbors": ents}

    def context_for(self, hints: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build Decision context slice from hints (customer, contract, project…)."""
        hints = hints or {}
        found: list[dict[str, Any]] = []
        for key in ("customer", "contract", "project", "entity", "name"):
            val = hints.get(key)
            if not val:
                continue
            found.extend(self.query(name_contains=str(val), limit=10))
        # de-dupe
        seen = set()
        uniq = []
        for e in found:
            if e["entityId"] not in seen:
                seen.add(e["entityId"])
                uniq.append(e)
        return {"entities": uniq[:20], "module": "Knowledge", "count": len(uniq)}
