"""Production Paddle checkout URL helpers."""

from __future__ import annotations

import os


def narna_public_url() -> str:
    return (
        os.environ.get("NARNA_PUBLIC_URL")
        or os.environ.get("UAP_PUBLIC_URL")
        or "https://narna.org"
    ).rstrip("/")


def paddle_success_url(kind: str = "billing") -> str:
    if kind == "package":
        explicit = os.environ.get("PADDLE_PACKAGE_SUCCESS_URL", "").strip()
        if explicit:
            return explicit
        return f"{narna_public_url()}/packages?paid=1"
    explicit = os.environ.get("PADDLE_SUCCESS_URL", "").strip()
    if explicit:
        return explicit
    return f"{narna_public_url()}/billing?paid=1"
