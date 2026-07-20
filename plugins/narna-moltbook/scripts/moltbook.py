#!/usr/bin/env python3
"""CLI for narna-moltbook — works standalone or from OpenClaw."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from client import MoltbookClient, save_credentials  # noqa: E402


def _print(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_test(_: argparse.Namespace) -> int:
    _print(MoltbookClient().test_connection())
    return 0


def cmd_hot(args: argparse.Namespace) -> int:
    _print(MoltbookClient().browse_hot(limit=args.limit))
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    client = MoltbookClient()
    result = client.register_agent(args.name, args.description)
    agent = result.get("agent") if isinstance(result.get("agent"), dict) else result
    api_key = ""
    if isinstance(agent, dict):
        api_key = str(agent.get("api_key") or agent.get("apiKey") or "")
    if api_key:
        path = save_credentials(api_key, args.name)
        result["credentials_saved"] = str(path)
    _print(result)
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    _print(
        MoltbookClient(require_auth=True).create_post(
            args.title, args.content, submolt_name=args.submolt
        )
    )
    return 0


def cmd_reply(args: argparse.Namespace) -> int:
    _print(MoltbookClient(require_auth=True).reply(args.post_id, args.content))
    return 0


def cmd_sync(_: argparse.Namespace) -> int:
    try:
        from credentials import sync_primary_credentials
    except ImportError:
        from credentials import sync_primary_credentials  # type: ignore[no-redef]

    path = sync_primary_credentials()
    _print({"ok": True, "synced_to": str(path)})
    return 0


def cmd_auto(args: argparse.Namespace) -> int:
    from auto import run_automation  # noqa: E402

    ws = Path(args.workspace) if args.workspace else None
    _print(run_automation(workspace=ws, dry_run=args.dry_run, rate_limit_sec=args.rate_limit))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="moltbook", description="narna-moltbook CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_test = sub.add_parser("test", help="Test public feed + auth")
    p_test.set_defaults(func=cmd_test)

    p_hot = sub.add_parser("hot", help="Browse hot posts")
    p_hot.add_argument("limit", nargs="?", type=int, default=5)
    p_hot.set_defaults(func=cmd_hot)

    p_reg = sub.add_parser("register", help="Register agent and save credentials")
    p_reg.add_argument("name")
    p_reg.add_argument("description")
    p_reg.set_defaults(func=cmd_register)

    p_create = sub.add_parser("create", help="Create a post (auth required)")
    p_create.add_argument("title")
    p_create.add_argument("content")
    p_create.add_argument("--submolt", default="agents", help="Submolt name (default: agents)")
    p_create.set_defaults(func=cmd_create)

    p_reply = sub.add_parser("reply", help="Reply to a post (auth required)")
    p_reply.add_argument("post_id")
    p_reply.add_argument("content")
    p_reply.set_defaults(func=cmd_reply)

    p_sync = sub.add_parser("sync", help="Sync claimed OpenClaw credentials to ~/.config/moltbook")
    p_sync.set_defaults(func=cmd_sync)

    p_auto = sub.add_parser("auto", help="Run automation: check home + post next queued item")
    p_auto.add_argument("--workspace", help="OpenClaw workspace path")
    p_auto.add_argument("--dry-run", action="store_true")
    p_auto.add_argument("--rate-limit", type=int, default=30 * 60, help="Seconds between posts")
    p_auto.set_defaults(func=cmd_auto)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
