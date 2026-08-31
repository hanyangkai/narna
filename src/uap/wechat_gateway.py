"""WeChat Official Account / Work WeChat webhook stub (APAC)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def wechat_enabled() -> bool:
    return bool(
        os.environ.get("UAP_WECHAT_APP_ID", "").strip()
        and (
            os.environ.get("UAP_WECHAT_APP_SECRET", "").strip()
            or os.environ.get("UAP_WECHAT_ACCESS_TOKEN", "").strip()
        )
    )


def extract_wechat_message(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    # XML-parsed-as-dict or JSON relay
    frm = str(
        payload.get("FromUserName")
        or payload.get("from")
        or payload.get("touser")
        or ""
    ).strip()
    msg_type = str(payload.get("MsgType") or payload.get("msgtype") or "text").lower()
    text = str(payload.get("Content") or payload.get("text") or payload.get("content") or "").strip()
    if isinstance(payload.get("text"), dict):
        text = str(payload["text"].get("content") or text).strip()
    if frm and text and msg_type in {"text", ""}:
        return frm, text
    return None, None


def send_wechat_message(user_id: str, text: str) -> dict[str, Any]:
    token = (
        os.environ.get("UAP_WECHAT_ACCESS_TOKEN")
        or os.environ.get("WECHAT_ACCESS_TOKEN")
        or ""
    ).strip()
    relay = (os.environ.get("UAP_WECHAT_SEND_URL") or "").strip()
    if not token and not relay:
        raise RuntimeError("Set UAP_WECHAT_ACCESS_TOKEN or UAP_WECHAT_SEND_URL")
    url = relay or f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={token}"
    body = json.dumps(
        {
            "touser": user_id,
            "msgtype": "text",
            "text": {"content": text[:2000]},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "narna-agent/0.2"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        return {"ok": False, "error": f"WeChat HTTP {e.code}: {detail}", "to": user_id}
    except Exception as e:
        return {"ok": False, "error": str(e), "to": user_id}
    errcode = data.get("errcode")
    return {
        "ok": errcode in (None, 0),
        "to": user_id,
        "response": data,
        "backend": "wechat",
    }


def format_agent_reply(out: dict[str, Any]) -> str:
    answer = str(out.get("answer") or "").strip()
    return (f"{answer}\n\n— ADQA DQS {out.get('dqs')} · {out.get('guardian')}")[:2000]
