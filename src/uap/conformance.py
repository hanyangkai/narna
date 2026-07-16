from __future__ import annotations

from pathlib import Path

from .identity import IdentityStore, spec_hash
from .policy import PolicyEngine, load_policy_pack, resolve_policy_ref
from .schemas import validator_for
from .spec import load_agent_spec
from .tools import DEFAULT_TOOLS, TOOL_ADAPTERS


def run_conformance_checks(workspace: Path, spec_path: Path) -> list[str]:
    problems: list[str] = []
    ws = workspace

    if not (ws / ".uap").exists():
        problems.append("missing .uap workspace")

    if not spec_path.exists():
        problems.append(f"missing AgentSpec: {spec_path}")
        return problems

    try:
        spec = load_agent_spec(spec_path)
        validator_for("agent-spec.schema.json").validate(spec.raw)
    except Exception as e:
        problems.append(f"AgentSpec invalid: {e}")
        return problems

    if not IdentityStore(ws).load():
        problems.append("identity not issued")

    policy_ref = spec.raw.get("spec", {}).get("policy", {}).get("ref")
    if policy_ref:
        try:
            resolve_policy_ref(policy_ref, ws)
            load_policy_pack(policy_ref, ws)
        except Exception as e:
            problems.append(f"policy pack: {e}")

    declared_tools = [t.get("name") for t in spec.raw.get("spec", {}).get("tools", [])]
    for tool_name in declared_tools:
        if tool_name and tool_name not in TOOL_ADAPTERS:
            problems.append(f"tool not registered: {tool_name}")

    engine = PolicyEngine(ws)
    decision = engine.evaluate(
        policy_ref=policy_ref or "policies/local-default@0.0.0",
        agent_permissions=spec.raw.get("spec", {}).get("permissions", []),
        permission="market.read",
        parameters={},
    )
    if decision["decision"] not in {"allow", "deny", "ask"}:
        problems.append("policy engine returned invalid decision")

    if not spec_hash(spec).startswith("sha256:"):
        problems.append("specHash format invalid")

    if not DEFAULT_TOOLS:
        problems.append("no default tool definitions")

    return problems
