"""Adapter base — Never Replace. Always Extend. Enforce-before in production."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class NarnaGovernanceDenied(PermissionError):
    """Raised when adapter enforce mode blocks a host framework call."""


@dataclass
class AdapterResult:
    framework: str
    package: str
    status: str = "available"
    hooks: list[str] = field(default_factory=list)
    message: str = ""


def adapter_mode(agent: Any) -> str:
    mode = getattr(agent, "_narna_adapter_mode", None)
    if mode:
        return str(mode).lower()
    return os.environ.get("NARNA_ADAPTER_MODE", "enforce").lower()


def _permission_for_call(adapter_id: str, method_name: str, kwargs: dict[str, Any]) -> str:
    if method_name in {"call_tool", "call"}:
        tool = kwargs.get("name") or kwargs.get("tool_name") or kwargs.get("tool")
        if tool:
            return f"tool.{tool}"
    return f"{adapter_id}.{method_name}"


def _enforce_before_call(agent: Any, permission: str, parameters: dict[str, Any]) -> None:
    from uap.capability_gov import CapabilityGovernor
    from uap.governance_runtime import ConstitutionRuntime
    from uap.guardian_map import capability_for_permission, guardian_enabled
    from uap.kill import KillStore
    from uap.policy import PolicyEngine

    spec = agent.spec
    agent_id = spec.agent_id
    policy_ref = spec.raw["spec"]["policy"]["ref"]
    permissions = spec.raw["spec"].get("permissions", [])
    ws = agent.workspace

    # Kill Token — local / domain / global (always checked)
    killed = KillStore(ws).is_agent_killed(agent_id)
    if killed:
        raise NarnaGovernanceDenied(
            f"agent killed tier={killed.get('tier')} ({killed.get('token')}): "
            f"{killed.get('reason')}"
        )

    ws_path = Path(ws)

    # Kill cascade freeze (even if token later revoked mid-flight)
    try:
        from uap.container import AgentContainer

        frozen = AgentContainer(ws_path).is_frozen(agent_id)
        if frozen and frozen.get("memoryFrozen"):
            raise NarnaGovernanceDenied(
                f"agent frozen by kill cascade ({frozen.get('killToken')})"
            )
    except NarnaGovernanceDenied:
        raise
    except Exception:
        pass

    # L4 Guardian Constitution — when Guardian profile on
    if guardian_enabled(agent, ws_path):
        try:
            from uap.council import GuardianConstitution

            const = GuardianConstitution(ws_path).evaluate(
                action=permission, agent_id=agent_id
            )
            if const.get("decision") == "deny":
                reasons = "; ".join(const.get("reasons") or [])
                raise NarnaGovernanceDenied(f"constitution denied: {reasons}")
        except NarnaGovernanceDenied:
            raise
        except FileNotFoundError:
            pass

        # NGS-0016 Agent Container contract
        try:
            from uap.container import AgentContainer

            is_net = any(
                x in permission.lower()
                for x in ("http", "mcp", "external", "api", "email", "web")
            )
            cont = AgentContainer(ws_path).check(
                agent_id=agent_id,
                action=permission,
                tool=permission,
                network=is_net,
            )
            if cont.get("decision") == "deny":
                reasons = "; ".join(cont.get("reasons") or [])
                raise NarnaGovernanceDenied(f"container denied: {reasons}")
        except NarnaGovernanceDenied:
            raise
        except FileNotFoundError:
            # install default lazily under guardian
            try:
                from uap.container import AgentContainer

                AgentContainer(ws_path).install_default()
            except Exception:
                pass

        cap = capability_for_permission(permission)
        if cap:
            gov_cap = CapabilityGovernor(ws_path).evaluate(
                capability=cap,
                agent_id=agent_id,
                profile="guardian",
                target=str(parameters.get("target") or parameters.get("url") or "") or None,
            )
            decision = gov_cap.get("decision")
            if decision in {"deny", "restricted"}:
                reasons = "; ".join(gov_cap.get("reasons") or [])
                raise NarnaGovernanceDenied(
                    f"capability {cap} denied ({decision}): {reasons}"
                )
            if decision in {"ask", "multisig"}:
                reasons = "; ".join(gov_cap.get("reasons") or [])
                raise NarnaGovernanceDenied(
                    f"capability {cap} requires approval ({decision}): {reasons}"
                )

    gov = ConstitutionRuntime(ws).execute(action=permission, agent_id=agent_id)
    if gov.get("decision") == "deny":
        reasons = "; ".join(gov.get("reasons") or [])
        raise NarnaGovernanceDenied(f"governance denied: {permission} ({reasons})")
    if gov.get("decision") == "ask":
        raise NarnaGovernanceDenied(f"governance requires approval: {permission}")

    engine = PolicyEngine(ws)
    # Generic adapter gate — governance packages deny specific actions above
    decision = engine.evaluate(
        policy_ref=policy_ref,
        agent_permissions=permissions,
        permission="external.invoke",
        parameters={**parameters, "action": permission},
        agent_id=agent_id,
    )
    if decision.get("decision") == "deny":
        raise NarnaGovernanceDenied(f"NARNA policy denied: {permission}")
    if decision.get("decision") == "ask":
        raise NarnaGovernanceDenied(f"NARNA policy requires approval: {permission}")


def _adqa_enabled(agent: Any) -> bool:
    flag = getattr(agent, "_narna_adqa", None)
    if flag is not None:
        return bool(flag)
    return os.environ.get("NARNA_ADQA", "").strip().lower() in {"1", "true", "yes", "on"}


def _adqa_strict(agent: Any) -> bool:
    flag = getattr(agent, "_narna_adqa_strict", None)
    if flag is not None:
        return bool(flag)
    return os.environ.get("NARNA_ADQA_STRICT", "").strip().lower() in {"1", "true", "yes", "on"}


def _adqa_before_call(agent: Any, permission: str, parameters: dict[str, Any]) -> dict[str, Any] | None:
    """Optional Decision Quality gate (NGS-0024) on adapter host calls."""
    if not _adqa_enabled(agent):
        return None
    from uap.adqa import ADQAEngine

    ws = getattr(agent, "workspace", None) or Path.cwd()
    agent_id = None
    try:
        agent_id = agent.spec.agent_id
    except Exception:
        pass
    evidence = parameters.get("evidencePresent") or parameters.get("evidence") or []
    if isinstance(evidence, str):
        evidence = [evidence]
    out = ADQAEngine(ws).check_proposed(
        action=permission,
        evidence_present=list(evidence) if isinstance(evidence, list) else [],
        agent_id=agent_id,
        context={"adapter": True, "parameters": parameters},
        persist=False,
    )
    adqa = out.get("adqa") or {}
    agent._adapter_last_adqa = adqa  # type: ignore[attr-defined]
    guardian = str(adqa.get("guardian") or "")
    if _adqa_strict(agent) and guardian in {"reject", "escalate"}:
        dqs = adqa.get("dqs")
        raise NarnaGovernanceDenied(
            f"ADQA {guardian} (dqs={dqs}) for {permission}"
        )
    return adqa


def _emit_execution_unit(agent: Any, *, unit_kind: str, label: str) -> None:
    """Best-effort EU mint via agent Governor (no-op if session not open)."""
    try:
        runtime = getattr(agent, "runtime", None)
        governor = getattr(runtime, "governor", None) if runtime is not None else None
        if governor is None:
            return
        session_id = None
        parent = None
        last = getattr(agent, "last_result", None)
        if last is not None:
            session_id = getattr(last, "session_id", None)
            parent = getattr(last, "root_execution_unit_id", None)
        logical = getattr(getattr(agent, "spec", None), "agent_id", None) or "adapter-agent"

        session = None
        if session_id:
            try:
                session = governor.sessions.load(session_id)
                if session.state != "open":
                    session = None
            except Exception:
                session = None
        if session is None:
            session = governor.open_session(logical)
            result = governor.begin_unit(
                session,
                logical_agent_id=logical,
                unit_kind=unit_kind,
                label=label,
            )
            agent._adapter_last_eu = result.unit.to_dict()  # type: ignore[attr-defined]
            governor.close_session(session.session_id)
            return
        result = governor.begin_unit(
            session,
            logical_agent_id=logical,
            unit_kind=unit_kind,
            parent_unit_id=parent,
            label=label,
        )
        agent._adapter_last_eu = result.unit.to_dict()  # type: ignore[attr-defined]
        if last is not None:
            last.root_execution_unit_id = result.unit.unit_id
    except Exception:
        pass


class BaseAdapter:
    id: str = "generic"
    package: str = "narna-generic"
    default_unit_kind: str = "workflow_step"

    def matches(self, obj: Any) -> bool:
        return False

    def attach(self, agent: Any, foreign: Any) -> AdapterResult:
        hooks = self._install_hooks(agent, foreign)
        mode = adapter_mode(agent)
        return AdapterResult(
            framework=self.id,
            package=self.package,
            status="available",
            hooks=hooks,
            message=f"Works with {self.id}. Mode: {mode}.",
        )

    def _install_hooks(self, agent: Any, foreign: Any) -> list[str]:
        return []

    def _wrap_method(self, foreign: Any, method_name: str, agent: Any) -> bool:
        """Wrap a method to enforce policy (optional) + record EU around the original call."""
        if foreign is None or not hasattr(foreign, method_name):
            return False
        original = getattr(foreign, method_name)
        if not callable(original):
            return False
        if getattr(original, "__narna_wrapped__", False):
            return True

        unit_kind = self.default_unit_kind
        adapter_id = self.id
        mode = adapter_mode(agent)

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            label = f"{adapter_id}.{method_name}"
            permission = _permission_for_call(adapter_id, method_name, kwargs)
            params = {k: v for k, v in kwargs.items() if isinstance(v, (str, int, float, bool))}

            if mode == "enforce":
                _enforce_before_call(agent, permission, params)

            _adqa_before_call(agent, permission, params)
            _emit_execution_unit(agent, unit_kind=unit_kind, label=label)
            result = original(*args, **kwargs)
            try:
                prompt = None
                if args and isinstance(args[0], str):
                    prompt = args[0]
                elif isinstance(kwargs.get("input"), str):
                    prompt = kwargs["input"]
                agent.run(prompt or label)
            except Exception:
                pass
            return result

        wrapped.__narna_wrapped__ = True  # type: ignore[attr-defined]
        wrapped.__wrapped__ = original  # type: ignore[attr-defined]
        try:
            setattr(foreign, method_name, wrapped)
            return True
        except Exception:
            return False
