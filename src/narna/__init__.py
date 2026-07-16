"""NARNA SDK — The Open Runtime for Trusted AI Agents.

Phase 1 (offline, zero config)::

    pip install narna

    from narna import Agent
    agent = Agent()
    agent.run()

UAP is the protocol (Understand · Act · Prove).
VAP is the trust engine (Verify · Audit · Prove).
"""

from __future__ import annotations

from uap.agent import Agent
from uap.evidence import EvidenceStore
from uap.identity import IdentityStore
from uap.policy import PolicyEngine

from .wrap import wrap

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "wrap",
    "PolicyEngine",
    "IdentityStore",
    "EvidenceStore",
    "__version__",
]
