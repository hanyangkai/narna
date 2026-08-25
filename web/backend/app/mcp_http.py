"""Drop-in MCP HTTP endpoint — CMEM-style private link for ADQA.

Clients (Cursor, Claude Code, Codex, OpenClaw) point MCP at:

  https://api.narna.org/mcp
  Authorization: Bearer uap_live_…

JSON-RPC methods: initialize, tools/list, tools/call, ping
Also: GET /mcp (discovery), GET /mcp/sse (event stream handshake)
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from .auth import get_org_from_api_key, resolve_api_key
from .database import get_db
from .models import Organization
from .quota import bump_adqa_usage, enforce_plan_limit
from .tenants import tenant_workspace

router = APIRouter(tags=["MCP"])


def _tools(org: Organization):
    from narna.mcp_tools import NarnaMcpTools

    return NarnaMcpTools(tenant_workspace(org.id))


def _rpc_result(id_: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _rpc_error(id_: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def handle_mcp_rpc(
    payload: dict[str, Any],
    *,
    org: Organization,
    meter_adqa: Any = None,
) -> dict[str, Any]:
    method = str(payload.get("method") or "")
    id_ = payload.get("id")
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}

    if method in {"initialize", "notifications/initialized"}:
        return _rpc_result(
            id_,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "narna-adqa", "version": "0.2.0"},
            },
        )
    if method == "ping":
        return _rpc_result(id_, {})
    if method == "tools/list":
        tools = _tools(org).list_tools()
        return _rpc_result(id_, {"tools": tools})
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if name == "narna_adqa_check" and callable(meter_adqa):
            meter_adqa()
        out = _tools(org).call_tool(name, arguments)
        text = json.dumps(out, ensure_ascii=False)
        return _rpc_result(
            id_,
            {
                "content": [{"type": "text", "text": text}],
                "isError": not bool(out.get("ok", True)),
            },
        )
    if method.startswith("notifications/"):
        return _rpc_result(id_, {})
    return _rpc_error(id_, -32601, f"method not found: {method}")


@router.get("/mcp")
@router.get("/v1/mcp")
def mcp_discovery() -> dict[str, Any]:
    return {
        "ok": True,
        "name": "narna-adqa",
        "transport": ["http-jsonrpc", "sse"],
        "endpoints": {
            "rpc": "/mcp",
            "sse": "/mcp/sse",
            "toolsRest": "/v1/mcp/tools",
            "callRest": "/v1/mcp/call",
        },
        "auth": "Authorization: Bearer uap_live_…  (or ?api_key=)",
        "docs": "https://narna.org/docs/drop-in-saas",
        "split": {
            "cmem": "memory continuity",
            "narna": "decision quality (ADQA)",
        },
    }


@router.post("/mcp")
@router.post("/v1/mcp")
async def mcp_rpc(
    request: Request,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid JSON") from e
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON-RPC object required")

    def meter() -> None:
        enforce_plan_limit(org=org, projected_events=0, projected_gu=0, projected_adqa=1)
        bump_adqa_usage(org=org, db=db)

    result = handle_mcp_rpc(payload, org=org, meter_adqa=meter)
    return JSONResponse(result)


@router.get("/mcp/sse")
@router.get("/v1/mcp/sse")
async def mcp_sse(
    request: Request,
    api_key: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Minimal SSE handshake so MCP clients can open a long-lived link."""
    key = api_key
    if not key and authorization and authorization.lower().startswith("bearer "):
        key = authorization.split(" ", 1)[1].strip()
    org = resolve_api_key(key, db)
    if org is None:
        raise HTTPException(status_code=401, detail="missing or invalid API key")

    endpoint = str(request.base_url).rstrip("/") + "/mcp"

    async def gen():
        yield f"event: endpoint\ndata: {endpoint}\n\n"
        yield ": narna-adqa ready\n\n"
        from narna.mcp_tools import TOOL_DEFS

        yield f"event: message\ndata: {json.dumps({'tools': len(TOOL_DEFS), 'org': org.id})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
