"""narna-moltbook — post, reply, and browse Moltbook with governance hooks."""

from __future__ import annotations

from typing import Any

try:
    from .client import MoltbookClient, save_credentials
except ImportError:
    from client import MoltbookClient, save_credentials


def register(agent: Any) -> dict[str, Any]:
    agent._plugins = getattr(agent, "_plugins", {})
    agent._plugins["moltbook"] = {
        "client": client_factory,
        "browse_hot": browse_hot,
        "create_post": create_post,
        "reply": reply,
        "test": test_connection,
        "register_agent": register_agent,
    }
    return {"ok": True, "plugin": "narna-moltbook"}


def client_factory(**kwargs: Any) -> MoltbookClient:
    return MoltbookClient(**kwargs)


def browse_hot(limit: int = 5, **kwargs: Any) -> dict[str, Any]:
    return MoltbookClient(**kwargs).browse_hot(limit=limit)


def create_post(title: str, content: str, **kwargs: Any) -> dict[str, Any]:
    submolt = kwargs.pop("submolt_name", None) or kwargs.pop("submolt", None)
    return MoltbookClient(require_auth=True, **kwargs).create_post(
        title, content, submolt_name=submolt
    )


def reply(post_id: str, content: str, **kwargs: Any) -> dict[str, Any]:
    return MoltbookClient(require_auth=True, **kwargs).reply(post_id, content)


def test_connection(**kwargs: Any) -> dict[str, Any]:
    return MoltbookClient(**kwargs).test_connection()


def register_agent(name: str, description: str, **kwargs: Any) -> dict[str, Any]:
    client = MoltbookClient(**kwargs)
    result = client.register_agent(name, description)
    agent = result.get("agent") if isinstance(result.get("agent"), dict) else result
    api_key = ""
    if isinstance(agent, dict):
        api_key = str(agent.get("api_key") or agent.get("apiKey") or "")
    if api_key:
        path = save_credentials(api_key, name)
        result["credentials_path"] = str(path)
    return result
