from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class CloudExporter:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("UAP_CLOUD_KEY", "")
        self.base_url = (base_url or os.environ.get("UAP_CLOUD_URL", "http://localhost:8000")).rstrip("/")

    def push_run(
        self,
        *,
        workspace: Path,
        run_id: str,
        agent_id: str = "",
        agent_name: str = "",
    ) -> dict[str, Any]:
        return push_run(
            workspace=workspace,
            run_id=run_id,
            api_key=self.api_key,
            base_url=self.base_url,
            agent_id=agent_id,
            agent_name=agent_name,
        )


def push_run(
    *,
    workspace: Path,
    run_id: str,
    api_key: str,
    base_url: str = "http://localhost:8000",
    agent_id: str = "",
    agent_name: str = "",
) -> dict[str, Any]:
    if not api_key:
        raise ValueError("UAP_CLOUD_KEY or api_key required")

    runs_dir = workspace / ".uap" / "runs" / run_id
    events_path = runs_dir / "events.jsonl"
    if not events_path.exists():
        raise FileNotFoundError(f"run not found: {run_id}")

    events: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))

    proof_bundle = None
    trust_score = None
    proof_path = runs_dir / "proof-bundle.json"
    if proof_path.exists():
        proof_bundle = json.loads(proof_path.read_text(encoding="utf-8"))
        trust_score = proof_bundle.get("trustScore")

    state = "Unknown"
    tip_hash = events[-1].get("eventHash", "") if events else ""
    for evt in reversed(events):
        if evt.get("eventType") in {"Completed", "Failed", "Aborted"}:
            state = evt.get("eventType", "Unknown")
            break

    payload = {
        "agentId": agent_id or events[0].get("agentId", "unknown"),
        "agentName": agent_name,
        "runId": run_id,
        "state": state,
        "tipHash": tip_hash,
        "events": events,
        "evidence": proof_bundle.get("evidence", []) if proof_bundle else [],
        "proofBundle": proof_bundle,
        "trustScore": trust_score,
    }

    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/ingest",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"cloud ingest failed ({e.code}): {body}") from e


def publish_agent(
    *,
    listing: dict[str, Any],
    passport: dict[str, Any] | None = None,
    api_key: str,
    base_url: str = "http://localhost:8000",
) -> dict[str, Any]:
    """Publish an agent listing + passport to NARNA Registry (cloud)."""
    payload = {
        "agentId": listing.get("agentId"),
        "name": listing.get("name"),
        "version": listing.get("version"),
        "creator": listing.get("creator", "local"),
        "capabilities": listing.get("capabilities", []),
        "category": listing.get("category", "general"),
        "trustScore": listing.get("trustScore"),
        "stars": listing.get("stars", 0),
        "downloads": listing.get("downloads", 0),
        "executions": listing.get("executions", 0),
        "passport": passport or listing.get("passport"),
        "identity": listing.get("identity"),
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/registry/publish",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"registry publish failed ({e.code}): {body}") from e
