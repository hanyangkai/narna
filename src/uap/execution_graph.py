"""Execution Graph — DAG of execution units within a session."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GraphNode:
    unit_id: str
    unit_kind: str
    logical_agent_id: str
    parent_unit_id: str | None = None
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "unitId": self.unit_id,
            "unitKind": self.unit_kind,
            "logicalAgentId": self.logical_agent_id,
            "parentUnitId": self.parent_unit_id,
            "children": self.children,
        }


class ExecutionGraph:
    def __init__(self, session_dir: Path) -> None:
        self.path = session_dir / "graph.json"
        self.nodes: dict[str, GraphNode] = {}
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        for row in data.get("nodes", []):
            node = GraphNode(
                unit_id=row["unitId"],
                unit_kind=row["unitKind"],
                logical_agent_id=row["logicalAgentId"],
                parent_unit_id=row.get("parentUnitId"),
                children=list(row.get("children") or []),
            )
            self.nodes[node.unit_id] = node

    def add_node(self, node: GraphNode) -> None:
        if node.parent_unit_id:
            parent = self.nodes.get(node.parent_unit_id)
            if parent and node.unit_id not in parent.children:
                parent.children.append(node.unit_id)
        self.nodes[node.unit_id] = node
        self.flush()

    def flush(self) -> None:
        payload = {"nodes": [n.to_dict() for n in self.nodes.values()]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def ancestry_kinds(self, unit_id: str) -> list[str]:
        kinds: list[str] = []
        current = self.nodes.get(unit_id)
        while current:
            kinds.append(current.unit_kind)
            if not current.parent_unit_id:
                break
            current = self.nodes.get(current.parent_unit_id)
        return kinds

    def would_create_cycle(self, parent_unit_id: str | None, child_logical_agent_id: str) -> bool:
        """Loop when delegating back to a logical agent already in ancestry (A→B→C→A)."""
        if not parent_unit_id:
            return False
        parent = self.nodes.get(parent_unit_id)
        if not parent or parent.logical_agent_id == child_logical_agent_id:
            return False
        current = parent
        while current:
            if current.logical_agent_id == child_logical_agent_id:
                return True
            if not current.parent_unit_id:
                break
            current = self.nodes.get(current.parent_unit_id)
        return False
