"""Shared social webhook handler for Cloud API routes."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session


SendFn = Callable[[str, str], None]
FormatFn = Callable[[dict[str, Any]], str]


async def handle_social_ask(
    *,
    db: Session,
    channel: str,
    external_id: str,
    text: str,
    send_fn: SendFn,
    format_fn: FormatFn,
    org_for_device_key,
    enforce_plan_limit,
    tenant_workspace,
    tenant_id_for_org,
    router_for_org,
    bump_agent_turns,
    use_pairing: bool = True,
) -> dict[str, Any]:
    from uap.gateway_pairing import gate_inbound
    from uap.narna_agent import NarnaAgent

    if use_pairing:
        pair_ws = Path(os.environ.get("UAP_TENANT_ROOT") or "/data/tenants") / "_gateway"
        blocked = gate_inbound(
            channel=channel,
            external_id=str(external_id),
            text=text,
            workspace=pair_ws,
        )
        if blocked:
            try:
                send_fn(str(external_id), str(blocked.get("answer") or "pairing required"))
            except Exception:
                pass
            return {"ok": True, "pairing": True, "paired": blocked.get("paired")}

    resolved = org_for_device_key(db, f"{channel}:{external_id}")
    try:
        enforce_plan_limit(org=resolved, projected_agent_turns=1)
    except HTTPException as e:
        if e.status_code == 402:
            try:
                send_fn(
                    str(external_id),
                    "Free Ask quota reached. Upgrade at https://narna.org/billing",
                )
            except Exception:
                pass
            return {"ok": True, "quota": True}
        raise

    agent = NarnaAgent(
        workspace=tenant_workspace(resolved.id),
        tenant_id=tenant_id_for_org(resolved.id),
        router=router_for_org(resolved),
    )
    try:
        out = agent.ask(text, channel=channel, external_id=str(external_id), use_tools=True)
    except Exception as e:
        try:
            send_fn(str(external_id), f"NARNA error: {e}")
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=str(e)) from e

    bump_agent_turns(org=resolved, db=db)
    try:
        send_fn(str(external_id), format_fn(out))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"{channel} send failed: {e}") from e
    return {"ok": True, "decisionId": out.get("decisionId"), "sessionId": out.get("sessionId")}
