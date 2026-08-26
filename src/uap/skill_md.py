"""agentskills.io-compatible SKILL.md export/import (Hermes interop v0)."""

from __future__ import annotations

import re
from typing import Any


def skill_to_markdown(skill: dict[str, Any]) -> str:
    name = str(skill.get("name") or "untitled")
    body = str(skill.get("body") or "")
    tags = skill.get("tags") or []
    tag_line = ", ".join(str(t) for t in tags)
    return (
        f"---\nname: {name}\ntags: [{tag_line}]\nstandard: agentskills.io\n---\n\n"
        f"# {name}\n\n{body.strip()}\n"
    )


def markdown_to_skill(md: str) -> dict[str, str | list[str]]:
    text = md or ""
    name = "imported-skill"
    tags: list[str] = []
    body = text
    m = re.match(r"(?s)^---\n(.*?)\n---\n(.*)$", text.strip())
    if m:
        front, rest = m.group(1), m.group(2)
        for line in front.splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            if line.startswith("tags:"):
                raw = line.split(":", 1)[1].strip().strip("[]")
                tags = [t.strip() for t in raw.split(",") if t.strip()]
        body = rest.strip()
        if body.startswith("#"):
            body = "\n".join(body.splitlines()[1:]).strip()
    return {"name": name, "body": body, "tags": tags}
