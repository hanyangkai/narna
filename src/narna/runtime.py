"""Vision alias: agent/runtime → NarnaAgent + ModelRouter (market plan B6)."""

from __future__ import annotations

from uap.model_router import ModelRouter, default_router_from_env
from uap.narna_agent import NarnaAgent

__all__ = ["NarnaAgent", "ModelRouter", "default_router_from_env"]
