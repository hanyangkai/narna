from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .canon import canonical_json_bytes
from .events import Event, genesis_prev_hash, hash_event, make_event
from .schemas import validator_for


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._events: list[Event] = []
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []
        self._seq = 0
        self._prev = genesis_prev_hash()
        if path.exists():
            self._load_existing()

    def _load_existing(self) -> None:
        for row in self.load_static(self.path):
            evt = {k: v for k, v in row.items() if k != "eventHash"}
            self._events.append(Event(event=evt, event_hash=row["eventHash"]))
        self._seq = len(self._events)
        if self._events:
            self._prev = self._events[-1].event_hash

    def subscribe(self, fn: Callable[[dict[str, Any]], None]) -> None:
        self._subscribers.append(fn)

    def append(
        self,
        *,
        event_id: str,
        event_type: str,
        agent_id: str,
        run_id: str,
        ts: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        evt = make_event(
            event_id=event_id,
            event_type=event_type,
            agent_id=agent_id,
            run_id=run_id,
            ts=ts,
            sequence=self._seq,
            hash_prev=self._prev,
            payload=payload,
        )
        validator_for("event.schema.json").validate(evt)
        h = hash_event(evt)
        self._events.append(Event(event=evt, event_hash=h))
        self._prev = h
        self._seq += 1
        stored = {**evt, "eventHash": h}
        for fn in self._subscribers:
            fn(stored)
        return stored

    def flush(self) -> None:
        with self.path.open("wb") as f:
            for e in self._events:
                line = canonical_json_bytes({**e.event, "eventHash": e.event_hash}) + b"\n"
                f.write(line)

    def export(self) -> list[dict[str, Any]]:
        return [{**e.event, "eventHash": e.event_hash} for e in self._events]

    @property
    def tip_hash(self) -> str:
        return self._prev

    @staticmethod
    def load_static(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
        return out
