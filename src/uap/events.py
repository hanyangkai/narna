from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .hashing import ZERO_HASH, sha256_obj


@dataclass(frozen=True)
class Event:
    event: dict[str, Any]
    event_hash: str


def make_event(
    *,
    event_id: str,
    event_type: str,
    agent_id: str,
    run_id: str,
    ts: str,
    sequence: int,
    payload: dict[str, Any],
    hash_prev: str,
    api_version: str = "uap.dev/v1alpha1",
    schema_ref: str | None = None,
) -> dict[str, Any]:
    evt: dict[str, Any] = {
        "eventId": event_id,
        "eventType": event_type,
        "apiVersion": api_version,
        "agentId": agent_id,
        "runId": run_id,
        "ts": ts,
        "sequence": sequence,
        "hashPrev": hash_prev,
        "payload": payload,
    }
    if schema_ref is not None:
        evt["schemaRef"] = schema_ref
    return evt


def hash_event(evt: dict[str, Any]) -> str:
    return sha256_obj(evt)


def genesis_prev_hash() -> str:
    return ZERO_HASH

