"""NARNA SDK — The Constitution Layer for Autonomous AI.

Strategy: docs/STRATEGY.md · Spec: specs/constitution/SPEC.md

Phase 1 (reference client, offline)::

    from narna import Agent
    agent = Agent()
    agent.run()

Phase 2 (trust on every action)::

    agent.enable_vap()
    result = agent.run("btc price")
    print(result.trust_score)

Phase 3 (Registry)::

    agent.publish()

Phase 4 (Certification levels)::

    cert = agent.certify(level="L3")
    print(cert["level"], cert["badge"])  # L3 Enterprise Ready

Constitution::

    from narna import load_constitution
    c = load_constitution("constitution.yaml")

UAP is the protocol (Understand · Act · Prove).
VAP is the trust engine (Verify · Audit · Prove).
"""

from __future__ import annotations

from uap.agent import Agent
from uap.constitution import load_constitution, write_constitution
from uap.evidence import EvidenceStore
from uap.identity import ENTITY_KINDS, IdentityStore
from uap.policy import PolicyEngine

from .wrap import wrap

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "wrap",
    "load_constitution",
    "write_constitution",
    "IdentityStore",
    "ENTITY_KINDS",
    "PolicyEngine",
    "EvidenceStore",
    "__version__",
]
