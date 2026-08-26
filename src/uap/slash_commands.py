"""Hermes-like slash command helpers (shared by CLI chat + docs)."""

from __future__ import annotations

from typing import Any


SLASH_HELP = """NARNA slash commands (Hermes-style):
  /help              Show this help
  /new | /reset      New session
  /clear             Clear on-screen history (keep session)
  /skills            List / open skills
  /tools             List agent tools
  /model [name]      Show or set model override
  /provider [name]   openrouter|openai|ollama|mock
  /memory [query]    Search Decision Memory / FTS
  /jobs              List scheduled jobs
  /cron <nl>         Schedule: e.g. /cron every day remind me to review risk
  /quit | /exit      Leave chat REPL
"""


def parse_slash(line: str) -> dict[str, Any] | None:
    """Return {cmd, args} if line is a slash command, else None."""
    text = (line or "").strip()
    if not text.startswith("/"):
        return None
    parts = text.split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    return {"cmd": cmd, "args": arg}
