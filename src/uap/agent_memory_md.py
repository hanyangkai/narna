"""Hermes-like MEMORY.md / USER.md persistent notes (Honcho-lite)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class AgentMemoryMd:
    """Markdown memory files under .uap/ — injected into Ask context."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.root = self.workspace / ".uap"
        self.root.mkdir(parents=True, exist_ok=True)
        self.memory_path = self.root / "MEMORY.md"
        self.user_path = self.root / "USER.md"
        self.project_path = self.root / "PROJECT.md"
        self._ensure()

    def _ensure(self) -> None:
        if not self.memory_path.exists():
            self.memory_path.write_text(
                "# MEMORY\n\nLessons from decisions (auto-appended when DQS is high).\n\n",
                encoding="utf-8",
            )
        if not self.user_path.exists():
            self.user_path.write_text(
                "# USER\n\n## Preferences\n\n## Avoid\n\n## Notes\n\n",
                encoding="utf-8",
            )
        if not self.project_path.exists():
            self.project_path.write_text(
                "# PROJECT\n\n## Active\n\n## Entities\n\n## Notes\n\n",
                encoding="utf-8",
            )

    def read_memory(self, *, max_chars: int = 2000) -> str:
        text = self.memory_path.read_text(encoding="utf-8", errors="replace")
        return text[-max_chars:] if len(text) > max_chars else text

    def read_user(self, *, max_chars: int = 2000) -> str:
        text = self.user_path.read_text(encoding="utf-8", errors="replace")
        return text[-max_chars:] if len(text) > max_chars else text

    def read_project(self, *, max_chars: int = 1500) -> str:
        text = self.project_path.read_text(encoding="utf-8", errors="replace")
        return text[-max_chars:] if len(text) > max_chars else text

    def append_lesson(self, lesson: str, *, dqs: int | None = None) -> None:
        line = (lesson or "").strip().replace("\n", " ")[:400]
        if not line:
            return
        badge = f" (DQS {dqs})" if dqs is not None else ""
        with self.memory_path.open("a", encoding="utf-8") as f:
            f.write(f"- {_now()}{badge}: {line}\n")

    def note_project(self, note: str, *, section: str = "Notes") -> None:
        note = (note or "").strip().replace("\n", " ")[:300]
        if not note:
            return
        text = self.project_path.read_text(encoding="utf-8", errors="replace")
        marker = f"## {section}"
        if marker not in text:
            text = text.rstrip() + f"\n\n{marker}\n\n"
        parts = text.split(marker, 1)
        if len(parts) != 2:
            with self.project_path.open("a", encoding="utf-8") as f:
                f.write(f"\n- {_now()}: {note}\n")
            return
        head, rest = parts
        rest_lines = rest.splitlines(keepends=True)
        insert = f"\n- {_now()}: {note}\n"
        if rest_lines and rest_lines[0].strip() == "":
            new_rest = rest_lines[0] + insert + "".join(rest_lines[1:])
        else:
            new_rest = insert + rest
        self.project_path.write_text(head + marker + new_rest, encoding="utf-8")

    def note_preference(self, note: str, *, section: str = "Preferences") -> None:
        note = (note or "").strip().replace("\n", " ")[:300]
        if not note:
            return
        text = self.user_path.read_text(encoding="utf-8", errors="replace")
        marker = f"## {section}"
        if marker not in text:
            text = text.rstrip() + f"\n\n{marker}\n\n"
        # Append under section
        parts = text.split(marker, 1)
        if len(parts) != 2:
            with self.user_path.open("a", encoding="utf-8") as f:
                f.write(f"\n- {_now()}: {note}\n")
            return
        head, rest = parts
        # Insert after section header line
        rest_lines = rest.splitlines(keepends=True)
        insert = f"\n- {_now()}: {note}\n"
        new_rest = ""
        if rest_lines and rest_lines[0].strip() == "":
            new_rest = rest_lines[0] + insert + "".join(rest_lines[1:])
        else:
            new_rest = insert + rest
        self.user_path.write_text(head + marker + new_rest, encoding="utf-8")

    def observe_user_message(self, message: str) -> None:
        low = (message or "").lower()
        if any(k in low for k in ("prefer", "always", "i like", "please remember")):
            self.note_preference(message[:300], section="Preferences")
        if any(k in low for k in ("don't", "do not", "avoid", "never")):
            self.note_preference(message[:300], section="Avoid")
        if any(k in low for k in ("project", "repo", "working on", "building", "đang làm")):
            self.note_project(message[:300], section="Active")
