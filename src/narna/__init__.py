"""NARNA SDK — The Constitution Layer for Autonomous AI.

Strategy: docs/STRATEGY.md · docs/BORROW-THE-WAVE.md
Never Replace. Always Extend.

    from narna import wrap, track
    agent = wrap(my_openai_agent, vap=True)

    @track
    def research(q: str) -> str: ...
"""

from __future__ import annotations

from uap.agent import Agent
from uap.constitution import load_constitution, write_constitution
from uap.evidence import EvidenceStore
from uap.identity import ENTITY_KINDS, IdentityStore
from uap.manifest import (
    compile_manifest_to_constitution,
    discover_manifest,
    load_manifest,
    load_or_compile_constitution,
)
from uap.policy import PolicyEngine

from narna.adapters import ADAPTER_CATALOG
from narna.wrap import track, wrap

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "wrap",
    "track",
    "ADAPTER_CATALOG",
    "load_constitution",
    "write_constitution",
    "load_manifest",
    "load_or_compile_constitution",
    "compile_manifest_to_constitution",
    "discover_manifest",
    "IdentityStore",
    "ENTITY_KINDS",
    "PolicyEngine",
    "EvidenceStore",
    "__version__",
]
