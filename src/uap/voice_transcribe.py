"""Voice memo transcription stub (Hermes voice parity v0)."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any


def transcribe_audio_file(path: str | Path, *, language: str | None = None) -> dict[str, Any]:
    """Transcribe via OpenAI Whisper-compatible API when BYOK key is present."""
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "error": "audio file not found"}
    key = (
        os.environ.get("UAP_OPENAI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("UAP_OPENROUTER_API_KEY")
        or ""
    ).strip()
    if not key:
        return {
            "ok": False,
            "needsKey": True,
            "error": "BYOK OpenAI/OpenRouter key required for voice transcription",
        }
    # OpenAI audio transcriptions multipart is awkward without requests;
    # for v0 return stub guidance if file large protocol needed.
    base = os.environ.get("UAP_WHISPER_BASE_URL") or "https://api.openai.com/v1"
    # Prefer JSON stub when no multipart helper — try whisper via openrouter chat not available.
    # Minimal: read tiny files only as placeholder text note.
    size = p.stat().st_size
    if size > 25_000_000:
        return {"ok": False, "error": "audio too large"}
    boundary = "----narnaVoiceBoundary"
    filename = p.name
    raw = p.read_bytes()
    parts = []
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"whisper-1\r\n".encode()
    )
    if language:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="language"\r\n\r\n'
            f"{language}\r\n".encode()
        )
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n".encode()
        + raw
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        f"{base.rstrip('/')}/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "narna-voice/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "text": str(data.get("text") or ""), "model": "whisper-1"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
