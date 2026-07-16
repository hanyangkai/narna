from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent import Agent
from .benchmark import BenchmarkStore
from .conformance import run_conformance_checks
from .identity import IdentityStore
from .marketplace import Marketplace
from .orchestrator import MultiAgentOrchestrator
from .registry import AgentRegistry
from .spec import load_agent_spec
from .tools import TOOL_ADAPTERS
from .verify import verify_proof_bundle


def _print_json(obj: object) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_init(args: argparse.Namespace) -> int:
    from .manifest import ensure_workspace_manifest, load_or_compile_constitution

    ws = Path.cwd()
    agent = Agent(workspace=ws, name=getattr(args, "name", None) or "Agent")
    agent.runtime.init()
    manifest_path = ensure_workspace_manifest(ws, agent_name=agent.spec.name)
    try:
        load_or_compile_constitution(manifest_path, workspace=ws)
        print(f"Compiled {manifest_path} → constitution.yaml")
    except Exception as e:
        print(f"Warning: manifest compile: {e}")

    spec_dst = Path("agent.yaml")
    if not spec_dst.exists():
        import yaml

        spec_dst.write_text(
            yaml.safe_dump(agent.spec.raw, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"Created {spec_dst} from manifest identity.")

    spec = load_agent_spec(spec_dst)
    identity = IdentityStore(ws).issue(spec)
    AgentRegistry(ws).register(spec_dst, workspace=ws)
    Marketplace(ws).index()
    print(f"Issued identity for {spec.agent_id}")
    _print_json(
        {
            "agentId": identity["agentId"],
            "specHash": identity["specHash"],
            "manifest": str(manifest_path),
        }
    )
    print("Initialized .uap workspace (narna.yaml first).")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Umbrella validation: manifest, constitution, identity, optional AgentSpec."""
    from .manifest import discover_manifest, load_manifest, load_or_compile_constitution

    ws = Path.cwd()
    problems: list[str] = []
    checked: list[str] = []

    manifest_path = Path(args.manifest) if args.manifest else discover_manifest(ws)
    if manifest_path and manifest_path.exists():
        try:
            doc = load_manifest(manifest_path)
            checked.append(f"manifest:{manifest_path.name}")
            if args.compile:
                load_or_compile_constitution(manifest_path, workspace=ws)
                checked.append("constitution:compiled")
        except Exception as e:
            problems.append(f"manifest invalid: {e}")
    elif not args.skip_manifest:
        problems.append("narna.yaml not found (run: narna init)")

    const_path = ws / "constitution.yaml"
    if const_path.exists() and not args.compile:
        try:
            load_or_compile_constitution(const_path, workspace=ws, write_constitution_out=False)
            checked.append("constitution.yaml")
        except Exception as e:
            problems.append(f"constitution invalid: {e}")

    spec_path = Path(args.spec)
    if spec_path.exists():
        try:
            load_agent_spec(spec_path)
            checked.append(f"agentspec:{spec_path.name}")
        except Exception as e:
            problems.append(f"AgentSpec invalid: {e}")

    if not IdentityStore(ws).load():
        problems.append("identity not issued (run: narna init)")

    gov_path = ws / ".uap" / "runtime" / "active-governance.json"
    if gov_path.exists():
        checked.append("governance:active")
    elif manifest_path and manifest_path.exists():
        try:
            doc = load_manifest(manifest_path, validate=False)
            if doc.get("governance") or doc.get("constitution"):
                problems.append("governance binding declared but not loaded (run: narna governance load)")
        except Exception:
            pass

    if args.full:
        problems.extend(run_conformance_checks(ws, spec_path if spec_path.exists() else Path("agent.yaml")))
        checked.append("conformance:full")

    if problems:
        print("narna validate: FAIL")
        for p in problems:
            print(f"- {p}")
        return 1
    print("narna validate: OK")
    for c in checked:
        print(f"  ✓ {c}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    from .narna_score import compute_narna_score

    _print_json(compute_narna_score(Path.cwd()))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    problems: list[str] = []
    ws = Path.cwd()
    if not (ws / ".uap").exists():
        problems.append(".uap workspace missing (run: uap init)")
    spec_path = Path(args.spec)
    if args.full:
        problems.extend(run_conformance_checks(ws, spec_path))
    else:
        if spec_path.exists():
            try:
                load_agent_spec(spec_path)
            except Exception as e:
                problems.append(f"AgentSpec invalid: {e}")
        else:
            problems.append(f"AgentSpec not found: {spec_path}")
        if not IdentityStore(ws).load():
            problems.append("identity not issued (run: uap init)")

    if problems:
        print("uap doctor: FAIL")
        for p in problems:
            print(f"- {p}")
        return 1
    label = "OK (full conformance)" if args.full else "OK"
    print(f"uap doctor: {label}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    if getattr(args, "narna_score", False):
        from .narna_score import compute_narna_score

        _print_json(compute_narna_score(Path.cwd()))
        return 0
    if getattr(args, "governance", False):
        from .governance_benchmark import leaderboard, write_leaderboard

        board = leaderboard(workspace=Path.cwd())
        write_leaderboard(Path.cwd())
        _print_json(board)
        return 0
    store = BenchmarkStore(Path.cwd())
    if args.avg:
        agent = Agent.from_spec(args.spec)
        avg = store.average_score(agent_id=agent.spec.agent_id)
        _print_json({"agentId": agent.spec.agent_id, "averageScore": avg})
        return 0
    rows = store.list(limit=args.limit)
    _print_json({"records": rows})
    return 0


def cmd_fleet(args: argparse.Namespace) -> int:
    from .fleet import load_fleet, meets_min_certification, member_role, role_can

    path = Path(args.path)
    if not path.exists():
        print(f"fleet not found: {path}")
        return 1
    fleet = load_fleet(path)
    out: dict = {
        "ok": True,
        "fleetId": fleet.get("metadata", {}).get("id"),
        "orgId": fleet.get("metadata", {}).get("orgId"),
        "members": len(fleet.get("spec", {}).get("members") or []),
    }
    if args.entity:
        role = member_role(fleet, args.entity)
        out["entityId"] = args.entity
        out["role"] = role
        if role and args.action:
            out["allowed"] = role_can(fleet, role, args.action)
    if args.level:
        out["meetsMinCertification"] = meets_min_certification(fleet, args.level)
    _print_json(out)
    return 0


def cmd_governance_list(args: argparse.Namespace) -> int:
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(Path.cwd())
    _print_json({"active": rt.active(), "packages": rt.list_local()})
    return 0


def cmd_governance_load(args: argparse.Namespace) -> int:
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(Path.cwd())
    result = rt.load(
        path=args.path,
        provider=args.provider,
        version=args.version,
        ref=args.ref,
        constitution_path=args.constitution,
    )
    out = {"ok": True, "binding": result["binding"]}
    _print_json(out)
    return 0


def cmd_governance_switch(args: argparse.Namespace) -> int:
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(Path.cwd())
    result = rt.switch(path=args.path, provider=args.provider, version=args.version)
    _print_json({"ok": True, "binding": result["binding"], "previous": result.get("previous")})
    return 0


def cmd_governance_execute(args: argparse.Namespace) -> int:
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(Path.cwd())
    decision = rt.execute(action=args.action, agent_id=args.entity, fleet_path=args.fleet)
    _print_json(decision)
    return 0 if decision["decision"] != "deny" else 2


def cmd_governance_verify(args: argparse.Namespace) -> int:
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(Path.cwd())
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    _print_json(rt.verify(bundle))
    return 0


def cmd_governance_audit(args: argparse.Namespace) -> int:
    from .governance_runtime import ConstitutionRuntime

    rt = ConstitutionRuntime(Path.cwd())
    run_record = None
    if args.run:
        p = Path(".uap") / "runs" / args.run / "run.json"
        if p.exists():
            run_record = json.loads(p.read_text(encoding="utf-8"))
    _print_json(rt.audit(run_record))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if getattr(args, "spec", None) and Path(args.spec).exists():
        agent = Agent.from_spec(args.spec)
    else:
        agent = Agent()
    if getattr(args, "vap", False):
        agent.enable_vap()
    result = agent.run(input=args.input, auto_approve_ask=args.yes)
    out: dict = {
        "runId": result.run_id,
        "state": result.state,
        "tipHash": result.tip_hash,
        "eventsPath": str(result.events_path),
        "pendingAsk": result.pending_ask,
        "vap": result.vap_enabled,
    }
    if result.vap_enabled:
        out["trustScore"] = result.trust_score
        out["auditId"] = result.audit_id
        out["proofPath"] = str(result.proof_path) if result.proof_path else None
        out["verificationCount"] = len(result.verifications)
    _print_json(out)
    return 0 if result.state != "Failed" else 1


def cmd_prove(args: argparse.Namespace) -> int:
    agent = Agent.from_spec(args.spec)
    bundle = agent.prove(args.run)
    _print_json(
        {"bundleId": bundle["bundleId"], "bundleHash": bundle["bundleHash"], "tipHash": bundle["tipHash"]}
    )
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    ok, problems = verify_proof_bundle(bundle)
    if ok:
        print("uap verify: OK")
        return 0
    print("uap verify: FAIL")
    for p in problems:
        print(f"- {p}")
    return 1


def cmd_audit(args: argparse.Namespace) -> int:
    agent = Agent.from_spec(args.spec)
    record = agent.audit(args.run)
    _print_json(record)
    return 0


def cmd_passport(args: argparse.Namespace) -> int:
    if getattr(args, "verify", False):
        path = Path(args.file) if args.file else None
        if path and path.exists():
            doc = json.loads(path.read_text(encoding="utf-8"))
        else:
            agent = Agent.from_spec(args.spec)
            doc = agent.passport(run_id=args.run, refresh=args.refresh)
        from .passport_sign import verify_passport_signature

        ok, problems = verify_passport_signature(doc, workspace=Path.cwd())
        if ok:
            print("narna passport verify: OK")
            _print_json({"verified": True, "passportId": doc.get("passportId")})
            return 0
        print("narna passport verify: FAIL")
        for p in problems:
            print(f"- {p}")
        return 1

    agent = Agent.from_spec(args.spec)
    doc = agent.passport(run_id=args.run, refresh=args.refresh)
    _print_json(doc)
    return 0


def cmd_otel_export(args: argparse.Namespace) -> int:
    from narna.adapters.otel_export import export_run_to_otlp

    ws = Path.cwd()
    run_id = args.run
    bundle_path = ws / ".uap" / "runs" / run_id / "proof-bundle.json"
    summary: dict = {"agentId": args.agent, "runId": run_id}
    if bundle_path.exists():
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        summary.update(
            {
                "agentId": bundle.get("agentId") or args.agent,
                "trustScore": (bundle.get("trustScore") or {}).get("score"),
                "passportId": bundle.get("passportId"),
                "constitutionId": (bundle.get("constitution") or {}).get("constitutionId"),
            }
        )
    result = export_run_to_otlp(summary, endpoint=args.endpoint, service_name=args.service)
    _print_json(result)
    return 0 if result.get("ok") else 1


def cmd_tools_list(_: argparse.Namespace) -> int:
    _print_json({"tools": sorted(TOOL_ADAPTERS.keys())})
    return 0


def cmd_resolve_ask(args: argparse.Namespace) -> int:
    agent = Agent.from_spec(args.spec)
    result = agent.resolve_ask(args.run, approved=args.approve)
    _print_json({"runId": result.run_id, "state": result.state, "tipHash": result.tip_hash})
    return 0 if result.state == "Completed" else 1


def cmd_register(args: argparse.Namespace) -> int:
    agent = Agent.from_spec(args.spec) if Path(args.spec).exists() else Agent()
    entry = agent.publish(remote=False)
    _print_json(entry)
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    if Path(args.spec).exists():
        agent = Agent.from_spec(args.spec)
    else:
        agent = Agent()
    if getattr(args, "vap", False):
        agent.enable_vap()
    entry = agent.publish(
        remote=not args.local,
        category=args.category,
        registry_url=args.registry_url,
        api_key=args.registry_key,
    )
    _print_json(entry)
    return 0


def cmd_certify(args: argparse.Namespace) -> int:
    if Path(args.spec).exists():
        agent = Agent.from_spec(args.spec)
    else:
        agent = Agent()
    if getattr(args, "vap", False):
        agent.enable_vap()
        if not agent.runtime.list_runs():
            agent.run(input=args.input or "certification probe")
    cert = agent.certify(
        level=args.level,
        remote=not args.local,
        min_trust=args.min_trust,
        registry_url=args.registry_url,
        api_key=args.registry_key,
    )
    _print_json(cert)
    return 0 if cert.get("status") == "passed" else 1


def cmd_constitution(args: argparse.Namespace) -> int:
    from .constitution import load_constitution
    from .manifest import discover_manifest, load_or_compile_constitution

    path = Path(args.path)
    if not path.exists():
        found = discover_manifest(Path.cwd())
        if found and found.name.startswith("narna"):
            doc = load_or_compile_constitution(found, workspace=Path.cwd())
            _print_json(
                {
                    "ok": True,
                    "source": str(found),
                    "kind": "Constitution",
                    "constitutionId": doc.get("metadata", {}).get("id"),
                    "entityId": doc.get("metadata", {}).get("entityId"),
                }
            )
            return 0
        if Path(args.spec).exists():
            agent = Agent.from_spec(args.spec)
        else:
            agent = Agent()
        doc = agent.constitution(refresh=True)
        _print_json(doc)
        return 0
    if path.name.startswith("narna"):
        doc = load_or_compile_constitution(path, workspace=Path.cwd())
        _print_json(
            {
                "ok": True,
                "source": str(path),
                "compiled": True,
                "constitutionId": doc.get("metadata", {}).get("id"),
                "entityId": doc.get("metadata", {}).get("entityId"),
                "supports": doc.get("spec", {}).get("capability", {}).get("supports"),
            }
        )
        return 0
    doc = load_constitution(path, validate=not args.no_validate)
    _print_json(
        {
            "ok": True,
            "path": str(path),
            "constitutionId": doc.get("metadata", {}).get("id"),
            "entityId": doc.get("metadata", {}).get("entityId"),
            "entityKind": doc.get("metadata", {}).get("entityKind"),
            "supports": doc.get("spec", {}).get("capability", {}).get("supports"),
        }
    )
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    from .manifest import discover_manifest, load_manifest, load_or_compile_constitution

    path = Path(args.path) if args.path else discover_manifest(Path.cwd())
    if path is None:
        print("narna.yaml not found — create one from specs/examples/narna.yaml")
        return 1
    doc = load_manifest(path, validate=not args.no_validate)
    if args.compile:
        constitution = load_or_compile_constitution(path, workspace=Path.cwd())
        _print_json(
            {
                "ok": True,
                "manifest": str(path),
                "constitutionId": constitution.get("metadata", {}).get("id"),
                "entityId": constitution.get("metadata", {}).get("entityId"),
                "wrote": "constitution.yaml",
            }
        )
        return 0
    _print_json({"ok": True, "path": str(path), "kind": doc.get("kind"), "identity": doc.get("identity")})
    return 0


def cmd_plugin_list(args: argparse.Namespace) -> int:
    from .plugins import discover_plugins, list_local_plugins

    discovered = discover_plugins(Path(args.root) if args.root else Path.cwd() / "plugins")
    registered = list_local_plugins(Path.cwd())
    _print_json({"discovered": discovered, "registered": registered})
    return 0


def cmd_plugin_publish(args: argparse.Namespace) -> int:
    import os

    from .plugins import register_plugin_local

    plugin_dir = Path(args.path)
    entry = register_plugin_local(Path.cwd(), plugin_dir)
    out: dict = {**entry, "status": "local"}
    if not args.local:
        base = (
            args.registry_url
            or os.environ.get("NARNA_REGISTRY_URL")
            or os.environ.get("UAP_CLOUD_URL")
            or ""
        ).rstrip("/")
        key = (
            args.registry_key
            or os.environ.get("NARNA_REGISTRY_KEY")
            or os.environ.get("UAP_CLOUD_KEY")
            or "uap_live_dev_local_key_change_in_prod"
        )
        if base:
            try:
                from uap_cloud.exporter import publish_plugin

                remote = publish_plugin(listing=entry, api_key=key, base_url=base)
                out["remote"] = remote
                out["status"] = "published"
                out["message"] = "Plugin published to local + remote registry."
            except Exception as e:
                out["remoteError"] = str(e)
                out["message"] = f"Published locally. Remote unavailable ({e})."
        else:
            out["message"] = "Published locally. Set NARNA_REGISTRY_URL to sync."
    else:
        out["message"] = "Published to local plugin registry."
    _print_json(out)
    return 0


def cmd_plugin_attach(args: argparse.Namespace) -> int:
    from .plugins import attach_plugin

    agent = Agent.from_spec(args.spec) if Path(args.spec).exists() else Agent()
    result = attach_plugin(agent, Path(args.path))
    _print_json({"ok": True, "agentId": agent.spec.agent_id, "plugin": result})
    return 0


def cmd_package_search(args: argparse.Namespace) -> int:
    from .packages import search_packages

    rows = search_packages(Path.cwd(), args.q)
    _print_json({"packages": rows})
    return 0


def cmd_package_publish(args: argparse.Namespace) -> int:
    import os

    from .packages import register_package_local

    entry = register_package_local(Path.cwd(), Path(args.path))
    out: dict = {**entry, "status": "local"}
    if not args.local:
        base = (
            args.registry_url
            or os.environ.get("NARNA_REGISTRY_URL")
            or os.environ.get("UAP_CLOUD_URL")
            or ""
        ).rstrip("/")
        key = (
            args.registry_key
            or os.environ.get("NARNA_REGISTRY_KEY")
            or os.environ.get("UAP_CLOUD_KEY")
            or "uap_live_dev_local_key_change_in_prod"
        )
        if base:
            try:
                from uap_cloud.exporter import publish_governance_package

                remote = publish_governance_package(listing=entry, api_key=key, base_url=base)
                out["remote"] = remote
                out["status"] = "published"
            except Exception as e:
                out["remoteError"] = str(e)
                out["message"] = f"Published locally. Remote unavailable ({e})."
        else:
            out["message"] = "Published locally. Set NARNA_REGISTRY_URL to sync."
    else:
        out["message"] = "Published to local package registry."
    _print_json(out)
    return 0


def cmd_package_pull(args: argparse.Namespace) -> int:
    from .packages import pull_package

    entry = pull_package(Path.cwd(), args.provider, args.version)
    _print_json({"ok": True, "package": entry})
    return 0


def cmd_marketplace_search(args: argparse.Namespace) -> int:
    mp = Marketplace(Path.cwd())
    _print_json({"capability": args.capability, "agents": mp.search(args.capability)})
    return 0


def cmd_registry_list(args: argparse.Namespace) -> int:
    from .registry import AgentRegistry

    hits = AgentRegistry(Path.cwd()).search(capability=args.capability, q=args.q)
    _print_json(hits)
    return 0


def cmd_registry_trending(args: argparse.Namespace) -> int:
    hits = Marketplace(Path.cwd()).trending(category=args.category, limit=args.limit)
    _print_json(hits)
    return 0


def cmd_registry_get(args: argparse.Namespace) -> int:
    from .registry import AgentRegistry

    entry = AgentRegistry(Path.cwd()).get(args.agent_id)
    if entry is None:
        print(f"not found: {args.agent_id}")
        return 1
    _print_json(entry)
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    from uap_cloud import push_run
    import os

    cloud_url = args.cloud_url or os.environ.get("UAP_CLOUD_URL", "http://localhost:8000")
    cloud_key = args.cloud_key or os.environ.get("UAP_CLOUD_KEY", "")
    agent = Agent.from_spec(args.spec)
    if not cloud_key:
        print("Set UAP_CLOUD_KEY or --cloud-key")
        return 1
    if not (Path.cwd() / ".uap" / "runs" / args.run / "proof-bundle.json").exists():
        agent.prove(args.run)
    result = push_run(
        workspace=Path.cwd(),
        run_id=args.run,
        api_key=cloud_key,
        base_url=cloud_url,
        agent_id=agent.spec.agent_id,
        agent_name=agent.spec.name,
    )
    _print_json(result)
    return 0


def cmd_orchestrate(args: argparse.Namespace) -> int:
    orch = MultiAgentOrchestrator(Path.cwd())
    result = orch.run_pipeline(
        coordinator_spec=args.coordinator,
        child_specs=args.child,
        input_text=args.input,
    )
    _print_json(
        {"coordinatorRunId": result.coordinator_run_id, "children": result.child_results}
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="narna",
        description="NARNA CLI — Universal AI Governance Runtime (UAP protocol)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="Initialize workspace with narna.yaml + identity")
    init.add_argument("--name", default=None, help="Agent display name")
    init.set_defaults(func=cmd_init)

    validate = sub.add_parser("validate", help="Validate manifest, constitution, identity")
    validate.add_argument("--manifest", default=None, help="Path to narna.yaml")
    validate.add_argument("--spec", default="agent.yaml")
    validate.add_argument("--compile", action="store_true", help="Compile manifest to constitution")
    validate.add_argument("--skip-manifest", action="store_true")
    validate.add_argument("--full", action="store_true", help="Include conformance checks")
    validate.set_defaults(func=cmd_validate)

    score = sub.add_parser("score", help="Compute NARNA Score (0-100) for workspace")
    score.set_defaults(func=cmd_score)

    doctor = sub.add_parser("doctor", help="Validate workspace + AgentSpec + identity")
    doctor.add_argument("--spec", default="agent.yaml")
    doctor.add_argument("--full", action="store_true", help="Full spec conformance checks")
    doctor.set_defaults(func=cmd_doctor)

    bench = sub.add_parser("benchmark", help="Trust / governance benchmarks")
    bench.add_argument("--spec", default="agent.yaml")
    bench.add_argument("--avg", action="store_true", help="Average trust score for agent")
    bench.add_argument("--governance", action="store_true", help="Governance leaderboard")
    bench.add_argument("--narna-score", action="store_true", dest="narna_score", help="NARNA Score (0-100)")
    bench.add_argument("--limit", type=int, default=20)
    bench.set_defaults(func=cmd_benchmark)

    fleet = sub.add_parser("fleet", help="Fleet governance (C4)")
    fleet.add_argument("--path", default="fleet.yaml")
    fleet.add_argument("--entity", default=None)
    fleet.add_argument("--action", default=None)
    fleet.add_argument("--level", default=None, help="Check minCertification vs level")
    fleet.set_defaults(func=cmd_fleet)

    gov = sub.add_parser("governance", help="Constitution Runtime (Load/Execute/Switch/…)")
    gov_sub = gov.add_subparsers(dest="gov_cmd", required=True)
    g_list = gov_sub.add_parser("list", help="List local packages + active binding")
    g_list.set_defaults(func=cmd_governance_list)
    g_load = gov_sub.add_parser("load", help="Load package and set active binding")
    g_load.add_argument("--path", default=None)
    g_load.add_argument("--provider", default=None)
    g_load.add_argument("--version", default=None)
    g_load.add_argument("--ref", default=None)
    g_load.add_argument("--constitution", default=None)
    g_load.set_defaults(func=cmd_governance_load)
    g_sw = gov_sub.add_parser("switch", help="Switch active Governance Package")
    g_sw.add_argument("--path", default=None)
    g_sw.add_argument("--provider", default=None)
    g_sw.add_argument("--version", default=None)
    g_sw.set_defaults(func=cmd_governance_switch)
    g_ex = gov_sub.add_parser("execute", help="Authorize an action via active package")
    g_ex.add_argument("--action", required=True)
    g_ex.add_argument("--entity", default=None)
    g_ex.add_argument("--fleet", default=None)
    g_ex.set_defaults(func=cmd_governance_execute)
    g_ver = gov_sub.add_parser("verify", help="Verify ProofBundle with package citation")
    g_ver.add_argument("--bundle", required=True)
    g_ver.set_defaults(func=cmd_governance_verify)
    g_aud = gov_sub.add_parser("audit", help="Audit with package citation")
    g_aud.add_argument("--run", default=None)
    g_aud.set_defaults(func=cmd_governance_audit)

    run = sub.add_parser("run", help="Run agent")
    run.add_argument("--spec", default="agent.yaml")
    run.add_argument("--input", default=None)
    run.add_argument("-y", "--yes", action="store_true", help="Auto-approve policy ask")
    run.add_argument(
        "--vap",
        action="store_true",
        help="Enable VAP (Verify → Audit → Prove) for this run",
    )
    run.set_defaults(func=cmd_run)

    prove = sub.add_parser("prove", help="Build/load ProofBundle for a run")
    prove.add_argument("--spec", default="agent.yaml")
    prove.add_argument("--run", required=True)
    prove.set_defaults(func=cmd_prove)

    push = sub.add_parser("push", help="Push local run to UAP Cloud")
    push.add_argument("--spec", default="agent.yaml")
    push.add_argument("--run", required=True)
    push.add_argument("--cloud-url", default=None, help="default: UAP_CLOUD_URL env")
    push.add_argument("--cloud-key", default=None, help="default: UAP_CLOUD_KEY env")
    push.set_defaults(func=cmd_push)

    verify = sub.add_parser("verify", help="Verify a ProofBundle offline")
    verify.add_argument("--bundle", required=True)
    verify.set_defaults(func=cmd_verify)

    audit = sub.add_parser("audit", help="Audit a run")
    audit.add_argument("--spec", default="agent.yaml")
    audit.add_argument("--run", required=True)
    audit.set_defaults(func=cmd_audit)

    passport = sub.add_parser("passport", help="Show, refresh, or verify signed passport")
    passport.add_argument("--spec", default="agent.yaml")
    passport.add_argument("--run", default=None)
    passport.add_argument("--refresh", action="store_true")
    passport.add_argument("--verify", action="store_true", help="Verify Ed25519 signature")
    passport.add_argument("--file", default=None, help="Verify passport JSON file")
    passport.set_defaults(func=cmd_passport)

    otel = sub.add_parser("otel", help="OpenTelemetry bridge")
    otel_sub = otel.add_subparsers(dest="otel_cmd", required=True)
    otel_ex = otel_sub.add_parser("export", help="Export run summary to OTLP")
    otel_ex.add_argument("--run", required=True)
    otel_ex.add_argument("--agent", default="local")
    otel_ex.add_argument("--endpoint", default=None)
    otel_ex.add_argument("--service", default="narna-agent")
    otel_ex.set_defaults(func=cmd_otel_export)

    tools = sub.add_parser("tools", help="Tool commands")
    tools_sub = tools.add_subparsers(dest="tools_cmd", required=True)
    tools_list = tools_sub.add_parser("list", help="List registered tools")
    tools_list.set_defaults(func=cmd_tools_list)

    resolve = sub.add_parser("resolve-ask", help="Resolve pending policy ask")
    resolve.add_argument("--spec", default="agent.yaml")
    resolve.add_argument("--run", required=True)
    resolve.add_argument("--approve", action="store_true")
    resolve.add_argument("--deny", action="store_true")
    resolve.set_defaults(func=cmd_resolve_ask)

    reg = sub.add_parser("register", help="Register agent in local registry")
    reg.add_argument("--spec", default="agent.yaml")
    reg.set_defaults(func=cmd_register)

    pub = sub.add_parser("publish", help="Publish agent to NARNA Registry (Phase 3)")
    pub.add_argument("--spec", default="agent.yaml")
    pub.add_argument("--category", default=None)
    pub.add_argument("--local", action="store_true", help="Local registry only")
    pub.add_argument("--vap", action="store_true", help="Enable VAP before publishing passport")
    pub.add_argument("--registry-url", default=None)
    pub.add_argument("--registry-key", default=None)
    pub.set_defaults(func=cmd_publish)

    cert = sub.add_parser(
        "certify",
        help="Certification levels: L1 / L2 / L3 Enterprise Ready",
    )
    cert.add_argument("--spec", default="agent.yaml")
    cert.add_argument("--level", default="L2", help="Target level: L1, L2, or L3")
    cert.add_argument("--local", action="store_true", help="Local certificate only")
    cert.add_argument("--vap", action="store_true", help="Enable VAP + probe run if needed")
    cert.add_argument("--input", default=None, help="Input for probe run with --vap")
    cert.add_argument("--min-trust", type=float, default=None)
    cert.add_argument("--registry-url", default=None)
    cert.add_argument("--registry-key", default=None)
    cert.set_defaults(func=cmd_certify)

    constitution = sub.add_parser(
        "constitution",
        help="Validate / show constitution.yaml (Governance Runtime / UGS)",
    )
    constitution.add_argument("--path", default="constitution.yaml")
    constitution.add_argument("--spec", default="agent.yaml")
    constitution.add_argument("--no-validate", action="store_true")
    constitution.set_defaults(func=cmd_constitution)

    manifest = sub.add_parser(
        "manifest",
        help="Validate / compile narna.yaml (default metadata)",
    )
    manifest.add_argument("--path", default=None, help="default: discover narna.yaml")
    manifest.add_argument("--compile", action="store_true", help="Compile to constitution.yaml")
    manifest.add_argument("--no-validate", action="store_true")
    manifest.set_defaults(func=cmd_manifest)

    plugin = sub.add_parser("plugin", help="Plugin economy (list / publish / attach)")
    plugin_sub = plugin.add_subparsers(dest="plugin_cmd", required=True)
    pl_list = plugin_sub.add_parser("list", help="List discovered + registered plugins")
    pl_list.add_argument("--root", default=None, help="plugins directory")
    pl_list.set_defaults(func=cmd_plugin_list)
    pl_pub = plugin_sub.add_parser("publish", help="Publish plugin to registry")
    pl_pub.add_argument("path", help="plugin directory (contains narna-plugin.yaml)")
    pl_pub.add_argument("--local", action="store_true")
    pl_pub.add_argument("--registry-url", default=None)
    pl_pub.add_argument("--registry-key", default=None)
    pl_pub.set_defaults(func=cmd_plugin_publish)
    pl_att = plugin_sub.add_parser("attach", help="Attach plugin to agent")
    pl_att.add_argument("path", help="plugin directory")
    pl_att.add_argument("--spec", default="agent.yaml")
    pl_att.set_defaults(func=cmd_plugin_attach)

    pkg = sub.add_parser("package", help="Governance Package marketplace")
    pkg_sub = pkg.add_subparsers(dest="pkg_cmd", required=True)
    pk_search = pkg_sub.add_parser("search", help="Search local packages")
    pk_search.add_argument("q", nargs="?", default=None)
    pk_search.set_defaults(func=cmd_package_search)
    pk_pub = pkg_sub.add_parser("publish", help="Publish package to local/remote registry")
    pk_pub.add_argument("path", help="path to package YAML")
    pk_pub.add_argument("--local", action="store_true")
    pk_pub.add_argument("--registry-url", default=None)
    pk_pub.add_argument("--registry-key", default=None)
    pk_pub.set_defaults(func=cmd_package_publish)
    pk_pull = pkg_sub.add_parser("pull", help="Pull provider@version and activate")
    pk_pull.add_argument("provider")
    pk_pull.add_argument("--version", default=None)
    pk_pull.set_defaults(func=cmd_package_pull)

    mp = sub.add_parser("marketplace", help="Marketplace commands")
    mp_sub = mp.add_subparsers(dest="mp_cmd", required=True)
    mp_search = mp_sub.add_parser("search", help="Search agents by capability")
    mp_search.add_argument("capability")
    mp_search.set_defaults(func=cmd_marketplace_search)

    registry = sub.add_parser("registry", help="Agent Registry commands")
    reg_sub = registry.add_subparsers(dest="registry_cmd", required=True)
    reg_list = reg_sub.add_parser("list", help="List/search local registry")
    reg_list.add_argument("--capability", default=None)
    reg_list.add_argument("--q", default=None)
    reg_list.set_defaults(func=cmd_registry_list)
    reg_trend = reg_sub.add_parser("trending", help="Trending agents")
    reg_trend.add_argument("--category", default=None)
    reg_trend.add_argument("--limit", type=int, default=20)
    reg_trend.set_defaults(func=cmd_registry_trending)
    reg_get = reg_sub.add_parser("get", help="Get agent listing")
    reg_get.add_argument("agent_id")
    reg_get.set_defaults(func=cmd_registry_get)

    orch = sub.add_parser("orchestrate", help="Multi-agent pipeline (V6)")
    orch.add_argument("--coordinator", default="agent.yaml")
    orch.add_argument("--child", action="append", default=[])
    orch.add_argument("--input", required=True)
    orch.set_defaults(func=cmd_orchestrate)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "resolve-ask":
        if args.approve == args.deny:
            print("specify exactly one of --approve or --deny")
            raise SystemExit(2)
        if args.deny:
            args.approve = False
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main(sys.argv[1:])
