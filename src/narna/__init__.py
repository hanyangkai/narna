"""NARNA SDK — Governance Infrastructure for Agentic AI.

    from narna import wrap, track, agent, policy, audit, ConstitutionRuntime
    agent = wrap(my_langgraph_app, vap=True)
"""

from __future__ import annotations

from uap.agent import Agent
from uap.constitution import load_constitution, write_constitution
from uap.evidence import EvidenceStore
from uap.governance_runtime import ConstitutionRuntime, GovernanceRuntime
from uap.identity import ENTITY_KINDS, IdentityStore
from uap.manifest import (
    compile_manifest_to_constitution,
    discover_manifest,
    load_manifest,
    load_or_compile_constitution,
)
from uap.narna_score import compute_narna_score
from uap.policy import PolicyEngine

from narna.adapters import ADAPTER_CATALOG
from narna.decorators import agent, audit, policy
from narna.wrap import track, wrap

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "wrap",
    "track",
    "agent",
    "policy",
    "audit",
    "compute_narna_score",
    "ADAPTER_CATALOG",
    "ConstitutionRuntime",
    "GovernanceRuntime",
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
