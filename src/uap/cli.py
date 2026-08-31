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
    if getattr(args, "bench_cmd", None) == "run" or getattr(args, "decision_run", False):
        return cmd_benchmark_run(args)
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


def cmd_benchmark_run(args: argparse.Namespace) -> int:
    from .decision_benchmark import run_benchmark, write_leaderboard_stub

    out = run_benchmark(
        directory=getattr(args, "dir", None) or None,
        agent=getattr(args, "agent", None) or "mock",
        category=getattr(args, "category", None) or None,
        limit=getattr(args, "run_limit", None),
    )
    if getattr(args, "write_leaderboard", False):
        path = Path(getattr(args, "leaderboard_path", None) or "benchmark/leaderboard.json")
        write_leaderboard_stub(path, out)
        out["leaderboardPath"] = str(path)
    # Compact default: drop per-scenario rows unless --verbose
    if not getattr(args, "verbose", False):
        out = {k: v for k, v in out.items() if k != "results"}
    _print_json(out)
    return 0 if float(out.get("accuracy") or 0) >= float(getattr(args, "min_accuracy", 1.0) or 0) else 2


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


def cmd_package_buy(args: argparse.Namespace) -> int:
    from .packages import record_local_purchase

    out = record_local_purchase(Path.cwd(), args.package_id)
    _print_json({"ok": True, **out})
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


def cmd_conformance(args: argparse.Namespace) -> int:
    from narna.conformance import run_conformance

    report = run_conformance(workspace=Path(args.workspace))
    if args.json:
        _print_json(report)
    else:
        status = "PASS" if report["conformant"] else "FAIL"
        print(f"UGS conformance: {status}")
        for c in report["checks"]:
            mark = "ok" if c["ok"] else "FAIL"
            print(f"  [{mark}] {c['id']}: {c['detail']}")
    return 0 if report["conformant"] else 1


def cmd_decision_evaluate(args: argparse.Namespace) -> int:
    from .decision import DecisionEngine

    engine = DecisionEngine(Path.cwd())
    evidence = [x.strip() for x in (args.evidence or "").split(",") if x.strip()]
    context = {}
    if getattr(args, "customer", None):
        context["customer"] = args.customer
    if getattr(args, "contract", None):
        context["contract"] = args.contract
    if getattr(args, "project", None):
        context["project"] = args.project
    out = engine.evaluate(
        action=args.action,
        question=args.question,
        provider=args.provider,
        version=args.version,
        path=args.path,
        evidence_present=evidence or None,
        session_id=args.session,
        context=context or None,
    )
    _print_json(out)
    if args.strict and out.get("decision") == "deny":
        return 2
    return 0


def cmd_adqa_check(args: argparse.Namespace) -> int:
    from .adqa import ADQAEngine

    evidence = [x.strip() for x in (args.evidence or "").split(",") if x.strip()]
    out = ADQAEngine(Path.cwd()).check_proposed(
        action=args.action,
        provider=args.provider,
        evidence_present=evidence or None,
        agent_id=args.agent,
        question=args.question,
        persist=not getattr(args, "no_persist", False),
    )
    _print_json(out)
    guardian = (out.get("adqa") or {}).get("guardian")
    if args.strict and guardian == "reject":
        return 2
    return 0


def cmd_reason(args: argparse.Namespace) -> int:
    from .model_router import ModelRouter

    router = ModelRouter(provider=getattr(args, "provider", None) or None)
    out = router.complete(
        messages=[{"role": "user", "content": args.message}],
        task=args.task,
    )
    _print_json(out.to_dict())
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    from .model_router import ModelRouter
    from .narna_agent import NarnaAgent

    msg = getattr(args, "message_opt", None) or args.message
    if not msg:
        print("message required", file=sys.stderr)
        return 2
    router = ModelRouter(provider=getattr(args, "provider", None) or None)
    out = NarnaAgent(Path.cwd(), router=router).ask(
        msg, challenge=bool(getattr(args, "challenge", False))
    )
    _print_json(out)
    return 0


def cmd_trace(args: argparse.Namespace) -> int:
    from .decision_trace import DecisionTraceStore

    store = DecisionTraceStore(Path.cwd())
    if args.trace_cmd == "list":
        rows = store.list_traces(limit=args.limit)
        _print_json({"traces": rows, "count": len(rows)})
        return 0
    row = store.get(args.trace_id)
    if not row:
        print("trace not found", file=sys.stderr)
        return 1
    _print_json(row)
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    from .model_router import ModelRouter
    from .narna_agent import NarnaAgent

    agent = NarnaAgent(Path.cwd(), router=ModelRouter(provider=getattr(args, "provider", None) or None))
    try:
        out = agent.replay(args.trace_id, extra_context=args.context)
    except KeyError as e:
        print(str(e), file=sys.stderr)
        return 1
    _print_json(out)
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    from narna.evaluate import evaluate

    evidence = [x.strip() for x in (args.evidence or "").split(",") if x.strip()]
    out = evaluate(action=args.action, evidence=evidence or None, question=args.question)
    _print_json(out)
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    """Hermes-like interactive REPL with slash commands."""
    from .model_router import ModelRouter
    from .narna_agent import NarnaAgent
    from .slash_commands import SLASH_HELP, parse_slash

    router = ModelRouter(provider=getattr(args, "provider", None) or None)
    agent = NarnaAgent(Path.cwd(), router=router)
    session_id: str | None = None
    print("NARNA chat — type /help · /quit to exit")
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        slash = parse_slash(line)
        if slash:
            cmd = slash["cmd"]
            arg = slash["args"]
            if cmd in {"/quit", "/exit"}:
                break
            if cmd == "/help":
                print(SLASH_HELP)
                continue
            if cmd in {"/new", "/reset"}:
                session_id = None
                print("(new session)")
                continue
            if cmd == "/tools":
                print(", ".join(t["name"] for t in agent.tools.specs()))
                continue
            if cmd == "/skills":
                for s in agent.skills.list_skills()[:20]:
                    print(f"- {s.get('skillId')}: {s.get('name')}")
                continue
            if cmd == "/jobs":
                for j in agent.jobs.list_jobs()[:20]:
                    print(f"- {j.get('jobId')}: {j.get('prompt')} every={j.get('everyMinutes')}")
                continue
            if cmd == "/memory":
                q = arg or "decision"
                hits = agent.fts.search(q, limit=5)
                _print_json({"hits": hits})
                continue
            if cmd == "/cron":
                from .nl_cron import parse_nl_schedule

                try:
                    parsed = parse_nl_schedule(arg or line)
                    row = agent.jobs.create(
                        prompt=str(parsed["prompt"]),
                        every_minutes=parsed.get("everyMinutes"),
                        run_at=parsed.get("runAt"),
                        channel=str(parsed.get("channel") or "job"),
                    )
                    _print_json({"ok": True, "job": row, "parsed": parsed})
                except Exception as e:
                    print(f"error: {e}", file=sys.stderr)
                continue
            if cmd == "/model":
                if arg:
                    router.models = {**(router.models or {}), "reason": arg}
                    print(f"model={arg}")
                else:
                    print(f"provider={router.provider} model={router.pick_model('reason')}")
                continue
            if cmd == "/provider":
                if arg:
                    router.provider = arg.lower()
                    print(f"provider={router.provider}")
                else:
                    print(f"provider={router.provider}")
                continue
            print(f"unknown slash: {cmd} — try /help")
            continue
        out = agent.ask(line, session_id=session_id, use_tools=True)
        session_id = str(out.get("sessionId") or session_id)
        print(f"narna> {out.get('answer')}")
        print(f"  [DQS {out.get('dqs')} · {out.get('guardian')}]")
    return 0


def cmd_tui(args: argparse.Namespace) -> int:
    """Fullscreen TUI (optional textual). Falls back message if not installed."""
    from .tui_app import run_tui

    return run_tui(
        provider=getattr(args, "provider", None) or None,
        workspace=Path.cwd(),
    )


def cmd_desktop(args: argparse.Namespace) -> int:
    """Run NARNA Desktop on this PC (local Ask UI or --tui)."""
    from .desktop_app import run_desktop
    from .narna_config import apply_config_to_env, default_home

    ws = getattr(args, "workspace", None) or str(default_home())
    apply_config_to_env(ws)

    return run_desktop(
        host=getattr(args, "host", None) or "127.0.0.1",
        port=getattr(args, "port", None),
        workspace=ws,
        open_browser=not getattr(args, "no_browser", False),
        tui=bool(getattr(args, "tui", False)),
        provider=getattr(args, "provider", None),
    )


def cmd_config(args: argparse.Namespace) -> int:
    """Show / set ~/.narna config (json or yaml)."""
    from .narna_config import config_set, config_show, default_home

    home = getattr(args, "home", None) or str(default_home())
    sub = getattr(args, "config_cmd", None)
    if sub == "show":
        _print_json(config_show(home))
        return 0
    if sub == "set":
        key = getattr(args, "key", None)
        value = getattr(args, "value", None)
        if not key or value is None:
            print("usage: narna config set KEY VALUE", file=sys.stderr)
            return 2
        try:
            _print_json(config_set(key, value, home))
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        return 0
    print("unknown config subcommand", file=sys.stderr)
    return 2


def cmd_skills(args: argparse.Namespace) -> int:
    from .skill_hub import SkillHub

    hub = SkillHub(Path.cwd())
    sub = getattr(args, "skills_cmd", None)
    if sub == "hub-list":
        _print_json({"skills": hub.list_public(), "n": len(hub.list_public())})
        return 0
    if sub == "export-zip":
        out = hub.export_zip(getattr(args, "out", None) or "skills-hub.zip")
        _print_json(out)
        return 0
    if sub == "import-zip":
        path = getattr(args, "path", None)
        if not path:
            print("path required", file=sys.stderr)
            return 2
        _print_json(hub.import_zip(path))
        return 0
    if sub == "hub-sync":
        out = hub.sync_from_url(getattr(args, "url", None) or None)
        _print_json(out)
        return 0 if out.get("ok") else 2
    print("unknown skills subcommand", file=sys.stderr)
    return 2


def cmd_gateway(args: argparse.Namespace) -> int:
    from .gateway_pairing import GatewayPairingStore
    from .gateway_runner import UnifiedGateway, config_from_env
    from .model_router import ModelRouter
    from .narna_agent import NarnaAgent

    if args.gateway_cmd == "status":
        gw = UnifiedGateway(ask_fn=lambda *_: {}, workspace=Path.cwd())
        out = gw.status()
        out["pairing"] = GatewayPairingStore(Path.cwd()).status()
        _print_json(out)
        return 0
    if args.gateway_cmd == "channels":
        from .channels.registry import channels_status

        _print_json(channels_status())
        return 0
    if args.gateway_cmd == "pair":
        store = GatewayPairingStore(Path.cwd())
        code = getattr(args, "code", None) or ""
        if code:
            _print_json(store.confirm(code))
            return 0
        channel = getattr(args, "channel", None) or "telegram"
        external = getattr(args, "external_id", None) or ""
        if not external:
            print("provide --code CODE or --external-id ID", file=sys.stderr)
            return 2
        _print_json(store.pair_direct(channel, external))
        return 0

    router = ModelRouter(provider=getattr(args, "provider", None) or None)
    agent = NarnaAgent(Path.cwd(), router=router)

    def ask_fn(message: str, channel: str, external_id: str | None) -> dict:
        return agent.ask(
            message,
            channel=channel,
            external_id=external_id,
            use_tools=True,
        )

    gw = UnifiedGateway(ask_fn=ask_fn, config=config_from_env(), workspace=Path.cwd())
    if args.gateway_cmd == "once":
        n = gw.poll_once()
        _print_json({"handled": n, **gw.status()})
        return 0
    # run
    print("gateway running (Ctrl+C to stop)…", file=sys.stderr)
    try:
        gw.run_forever(max_iterations=getattr(args, "max_iters", None))
    except KeyboardInterrupt:
        gw.stop()
    _print_json(gw.status())
    return 0


def cmd_cmem_status(args: argparse.Namespace) -> int:
    from .cmem_bridge import CmemBridge

    _print_json(CmemBridge(Path.cwd()).status())
    return 0


def cmd_cmem_search(args: argparse.Namespace) -> int:
    from .cmem_bridge import CmemBridge

    hits = CmemBridge(Path.cwd()).search(args.query, limit=args.limit)
    _print_json({"hits": hits, "count": len(hits)})
    return 0


def cmd_cmem_ingest(args: argparse.Namespace) -> int:
    from .cmem_bridge import CmemBridge

    _print_json(
        CmemBridge(Path.cwd()).ingest_local(
            {"summary": args.summary, "action": args.action, "tags": args.tags.split(",") if args.tags else []}
        )
    )
    return 0


def cmd_integrations(args: argparse.Namespace) -> int:
    from narna.integrations import integration_manifest

    _print_json(integration_manifest())
    return 0


def cmd_dqs_status(args: argparse.Namespace) -> int:
    from .dqs_network import DqsNetwork

    _print_json(DqsNetwork(Path.cwd()).status())
    return 0


def cmd_dqs_opt_in(args: argparse.Namespace) -> int:
    from .dqs_network import DqsNetwork

    _print_json(DqsNetwork(Path.cwd()).set_opt_in(not args.off))
    return 0


def cmd_dqs_export(args: argparse.Namespace) -> int:
    from .dqs_network import DqsNetwork

    _print_json(DqsNetwork(Path.cwd()).export_digest(min_count=args.min_count))
    return 0


def cmd_dqs_import(args: argparse.Namespace) -> int:
    import json

    from .dqs_network import DqsNetwork

    digest = json.loads(Path(args.path).read_text(encoding="utf-8"))
    _print_json(DqsNetwork(Path.cwd()).import_digest(digest))
    return 0


def cmd_dmemory_query(args: argparse.Namespace) -> int:
    from .decision_memory import DecisionMemory

    _print_json(
        {
            "records": DecisionMemory(Path.cwd()).query(
                action=args.action,
                customer=args.customer,
                limit=args.limit,
                with_outcome_only=args.with_outcome,
            )
        }
    )
    return 0


def cmd_dmemory_lessons(args: argparse.Namespace) -> int:
    from .decision_memory import DecisionMemory

    _print_json(
        {"lessons": DecisionMemory(Path.cwd()).lessons_for(action=args.action, limit=args.limit)}
    )
    return 0


def cmd_learning_outcome(args: argparse.Namespace) -> int:
    from .outcome_learning import OutcomeLearningEngine

    out = OutcomeLearningEngine(Path.cwd()).evaluate(
        args.decision_id,
        status=args.status,
        detail=args.detail,
        success_score=args.score,
        lesson=args.lesson,
    )
    _print_json(out)
    return 0


def cmd_connect_catalog(args: argparse.Namespace) -> int:
    from .connect import ConnectRegistry

    _print_json(ConnectRegistry(Path.cwd()).catalog())
    return 0


def cmd_connect_register(args: argparse.Namespace) -> int:
    from .connect import ConnectRegistry

    _print_json(
        ConnectRegistry(Path.cwd()).register(
            type=args.type, name=args.name, endpoint=args.endpoint
        )
    )
    return 0


def cmd_connect_probe(args: argparse.Namespace) -> int:
    from .connect import ConnectRegistry

    _print_json(ConnectRegistry(Path.cwd()).probe(args.connector))
    return 0


def cmd_knowledge_upsert(args: argparse.Namespace) -> int:
    import json

    from .knowledge import KnowledgeGraph

    props = json.loads(args.props) if args.props else {}
    _print_json(
        KnowledgeGraph(Path.cwd()).upsert_entity(
            kind=args.kind, name=args.name, props=props, entity_id=args.id
        )
    )
    return 0


def cmd_knowledge_query(args: argparse.Namespace) -> int:
    from .knowledge import KnowledgeGraph

    _print_json(
        {
            "entities": KnowledgeGraph(Path.cwd()).query(
                kind=args.kind, name_contains=args.q, limit=args.limit
            )
        }
    )
    return 0


def cmd_knowledge_relate(args: argparse.Namespace) -> int:
    from .knowledge import KnowledgeGraph

    _print_json(
        KnowledgeGraph(Path.cwd()).relate(
            from_id=args.frm, to_id=args.to, rel_type=args.type
        )
    )
    return 0


def cmd_memory_put(args: argparse.Namespace) -> int:
    import json

    from .durable_memory import DurableMemory

    records = json.loads(args.data)
    _print_json(
        DurableMemory(Path.cwd()).put(scope=args.scope, scope_id=args.id, records=records)
    )
    return 0


def cmd_memory_get(args: argparse.Namespace) -> int:
    from .durable_memory import DurableMemory

    keys = [k.strip() for k in (args.keys or "").split(",") if k.strip()] or None
    _print_json(
        DurableMemory(Path.cwd()).get(scope=args.scope, scope_id=args.id, keys=keys)
    )
    return 0


def cmd_automate_run(args: argparse.Namespace) -> int:
    from .automation import AutomationEngine

    _print_json(
        AutomationEngine(Path.cwd()).run(
            trigger=args.trigger,
            action=args.action,
            provider=args.provider,
            path=args.path,
            context={"customer": args.customer} if args.customer else None,
        )
    )
    return 0


def cmd_dmarket_list(args: argparse.Namespace) -> int:
    from .decision_market import DecisionMarketplace

    _print_json(
        {
            "packages": DecisionMarketplace(Path.cwd()).list_packages(
                industry=getattr(args, "industry", None),
                decisions_only=not getattr(args, "all", False),
            )
        }
    )
    return 0


def cmd_dmarket_install(args: argparse.Namespace) -> int:
    from .decision_market import DecisionMarketplace

    _print_json(DecisionMarketplace(Path.cwd()).install(args.provider))
    return 0


def cmd_capability_evaluate(args: argparse.Namespace) -> int:
    from .capability_gov import CapabilityGovernor

    gov = CapabilityGovernor(Path.cwd())
    out = gov.evaluate(
        capability=args.capability,
        agent_id=args.agent,
        path=args.path,
        target=args.target,
        profile=args.profile,
    )
    _print_json(out)
    if args.strict and out.get("decision") in {"deny", "restricted"}:
        return 2
    return 0


def cmd_kill_issue(args: argparse.Namespace) -> int:
    from .kill import KillStore

    store = KillStore(Path.cwd())
    tier = getattr(args, "tier", "local") or "local"
    if tier == "domain":
        out = store.issue_domain(
            domain_id=args.domain,
            reason=args.reason,
            issued_by=args.by,
        )
    elif tier == "global":
        _print_json(
            {
                "ok": False,
                "error": "global kill requires council quorum — use: narna council propose --kind global_kill",
            }
        )
        return 2
    else:
        out = store.issue_local(
            agent_id=args.agent,
            session_id=args.session,
            reason=args.reason,
            issued_by=args.by,
        )
    _print_json(out)
    return 0


def cmd_kill_status(args: argparse.Namespace) -> int:
    from .kill import KillStore

    _print_json(
        KillStore(Path.cwd()).status(
            agent_id=args.agent,
            session_id=args.session,
            domain_id=getattr(args, "domain", None),
        )
    )
    return 0


def cmd_kill_revoke(args: argparse.Namespace) -> int:
    from .kill import KillStore

    _print_json(KillStore(Path.cwd()).revoke(args.token))
    return 0


def cmd_threat_analyze(args: argparse.Namespace) -> int:
    from .threat import ThreatEngine

    engine = ThreatEngine(Path.cwd())
    if args.auto_kill:
        out = engine.analyze_and_maybe_kill(args.session, auto_kill=True)
    else:
        out = engine.analyze_session(args.session)
    _print_json(out)
    if args.strict and float(out.get("riskScore") or 0) >= 0.9:
        return 2
    return 0


def cmd_collective_opt_in(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    _print_json(CollectiveDefense(Path.cwd()).set_opt_in(not args.off))
    return 0


def cmd_collective_publish(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense
    from .threat import ThreatEngine

    report = ThreatEngine(Path.cwd()).analyze_session(args.session)
    if args.min_risk and float(report.get("riskScore") or 0) < float(args.min_risk):
        _print_json({"ok": False, "error": "risk below --min-risk", "report": report})
        return 2
    sig = CollectiveDefense(Path.cwd()).publish_from_threat(report, org_id=args.org)
    _print_json({"ok": True, "signature": sig})
    return 0


def cmd_collective_import(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    _print_json({"ok": True, "signature": CollectiveDefense(Path.cwd()).import_signature(args.path)})
    return 0


def cmd_collective_list(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    _print_json({"signatures": CollectiveDefense(Path.cwd()).list_signatures(source=args.source)})
    return 0


def cmd_collective_match(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    patterns = [p.strip() for p in (args.patterns or "").split(",") if p.strip()]
    hits = CollectiveDefense(Path.cwd()).match(patterns=patterns or None, risk_band=args.band)
    _print_json({"matches": hits})
    return 0


def cmd_collective_apply(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    out = CollectiveDefense(Path.cwd()).apply(
        args.signature,
        agent_id=args.agent,
        auto_kill=args.kill,
    )
    _print_json(out)
    return 0


def cmd_constitution_install(args: argparse.Namespace) -> int:
    from .council import GuardianConstitution

    _print_json(GuardianConstitution(Path.cwd()).install_default())
    return 0


def cmd_constitution_evaluate(args: argparse.Namespace) -> int:
    from .council import GuardianConstitution

    out = GuardianConstitution(Path.cwd()).evaluate(action=args.action, agent_id=args.agent)
    _print_json(out)
    if args.strict and out.get("decision") == "deny":
        return 2
    return 0


def cmd_constitution_show(args: argparse.Namespace) -> int:
    from .council import GuardianConstitution

    path = GuardianConstitution(Path.cwd()).resolve_path()
    _print_json({"path": str(path), "document": GuardianConstitution(Path.cwd()).load()})
    return 0


def cmd_council_install(args: argparse.Namespace) -> int:
    from .council import GovernanceCouncil

    _print_json(GovernanceCouncil(Path.cwd()).install_default())
    return 0


def cmd_council_propose(args: argparse.Namespace) -> int:
    from .council import GovernanceCouncil

    payload: dict = {}
    if args.kind == "amend_constitution":
        if not args.yaml:
            _print_json({"ok": False, "error": "--yaml path required for amend_constitution"})
            return 2
        payload["yaml"] = Path(args.yaml).read_text(encoding="utf-8")
    elif args.kind == "global_kill":
        payload["reason"] = args.reason or "council-global-kill"
    elif args.kind == "domain_kill":
        payload["domainId"] = args.domain
        payload["reason"] = args.reason or "council-domain-kill"
    else:
        _print_json({"ok": False, "error": f"unknown kind: {args.kind}"})
        return 2
    prop = GovernanceCouncil(Path.cwd()).propose(
        kind=args.kind, payload=payload, proposed_by=args.by
    )
    _print_json(prop)
    return 0


def cmd_council_approve(args: argparse.Namespace) -> int:
    from .council import GovernanceCouncil

    _print_json(GovernanceCouncil(Path.cwd()).approve(args.proposal, member_id=args.by))
    return 0


def cmd_reputation_get(args: argparse.Namespace) -> int:
    from .reputation import ReputationStore

    _print_json(ReputationStore(Path.cwd()).get(args.agent))
    return 0


def cmd_reputation_record(args: argparse.Namespace) -> int:
    from .reputation import ReputationStore

    _print_json(
        ReputationStore(Path.cwd()).record(
            args.agent,
            origin=args.origin,
            creator=args.creator,
            model=args.model,
            attested=args.attested,
            attestation_ref=args.attestation,
        )
    )
    return 0


def cmd_reputation_violate(args: argparse.Namespace) -> int:
    from .reputation import ReputationStore

    _print_json(
        ReputationStore(Path.cwd()).add_violation(
            args.agent, kind=args.kind, severity=args.severity, detail=args.detail or ""
        )
    )
    return 0


def cmd_reputation_feedback(args: argparse.Namespace) -> int:
    from .reputation import ReputationStore

    _print_json(
        ReputationStore(Path.cwd()).add_feedback(
            args.agent, score=args.score, by=args.by, note=args.note or ""
        )
    )
    return 0


def cmd_container_install(args: argparse.Namespace) -> int:
    from .container import AgentContainer

    _print_json(AgentContainer(Path.cwd()).install_default())
    return 0


def cmd_container_profile(args: argparse.Namespace) -> int:
    from .container import AgentContainer

    _print_json(AgentContainer(Path.cwd()).profile(args.agent))
    return 0


def cmd_container_check(args: argparse.Namespace) -> int:
    from .container import AgentContainer

    out = AgentContainer(Path.cwd()).check(
        agent_id=args.agent or "anonymous",
        action=args.action,
        tool=args.tool,
        network=args.network,
        spawn_depth=args.spawn_depth,
    )
    _print_json(out)
    if args.strict and out.get("decision") == "deny":
        return 2
    return 0


def cmd_container_docker(args: argparse.Namespace) -> int:
    from .container_runner import DockerContainerRunner

    out = DockerContainerRunner(Path.cwd()).run(
        dry_run=not args.execute,
        agent_id=args.agent or "agent",
        image=args.image,
        network=args.network,
    )
    _print_json(out)
    return 0 if out.get("ok") else 1


def cmd_collective_peers(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    cd = CollectiveDefense(Path.cwd())
    if args.set:
        urls = [u.strip() for u in args.set.split(",") if u.strip()]
        _print_json(cd.set_peers(urls))
    else:
        _print_json({"peers": cd.list_peers()})
    return 0


def cmd_collective_push(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    _print_json(CollectiveDefense(Path.cwd()).push_to_peers())
    return 0


def cmd_collective_pull(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    _print_json(CollectiveDefense(Path.cwd()).pull_from_peers())
    return 0


def cmd_collective_export(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense

    _print_json(CollectiveDefense(Path.cwd()).export_bundle())
    return 0


def cmd_collective_import_bundle(args: argparse.Namespace) -> int:
    import json

    from .collective import CollectiveDefense

    bundle = json.loads(Path(args.path).read_text(encoding="utf-8"))
    _print_json(CollectiveDefense(Path.cwd()).import_bundle(bundle))
    return 0


def cmd_cti_submit(args: argparse.Namespace) -> int:
    import json

    from .cti_hub import CTIHub

    sig = json.loads(Path(args.path).read_text(encoding="utf-8"))
    _print_json(CTIHub(Path.cwd()).submit(sig, org_id=args.org))
    return 0


def cmd_cti_feed(args: argparse.Namespace) -> int:
    from .cti_hub import CTIHub

    _print_json({"feed": CTIHub(Path.cwd()).feed_list(limit=args.limit)})
    return 0


def cmd_cti_pull(args: argparse.Namespace) -> int:
    from .cti_hub import CTIHub

    _print_json(CTIHub(Path.cwd()).pull_into_workspace(limit=args.limit))
    return 0


def cmd_cti_relay(args: argparse.Namespace) -> int:
    from .cti_hub import CTIHub

    _print_json(CTIHub(Path.cwd()).relay_from_local_outbox())
    return 0


def cmd_cti_hubs(args: argparse.Namespace) -> int:
    from .cti_mesh import CTIMesh

    mesh = CTIMesh(Path.cwd())
    if args.set:
        hubs = [u.strip() for u in args.set.split(",") if u.strip()]
        _print_json(mesh.set_hubs(hubs))
    else:
        _print_json({"hubs": mesh.list_hubs()})
    return 0


def cmd_cti_sync(args: argparse.Namespace) -> int:
    from .collective import CollectiveDefense
    from .cti_mesh import CTIMesh

    CollectiveDefense(Path.cwd()).set_opt_in(True)
    mesh = CTIMesh(Path.cwd())
    if args.hubs:
        mesh.set_hubs([u.strip() for u in args.hubs.split(",") if u.strip()])
    if args.pull_only:
        out = mesh.pull()
    elif args.push_only:
        out = mesh.push()
    else:
        out = mesh.sync()
    _print_json(out)
    return 0 if out.get("ok") else 1


def cmd_jurisdiction_list(args: argparse.Namespace) -> int:
    from .jurisdiction import JurisdictionTemplates

    _print_json({"jurisdictions": JurisdictionTemplates(Path.cwd()).list()})
    return 0


def cmd_jurisdiction_apply(args: argparse.Namespace) -> int:
    from .council_binding import CouncilBinding
    from .jurisdiction import JurisdictionTemplates

    binding = CouncilBinding(Path.cwd()).get(args.binding)
    out = JurisdictionTemplates(Path.cwd()).apply_to_binding(
        binding, jurisdiction_id=args.jurisdiction
    )
    _print_json(out)
    return 0


def cmd_isolation_list(args: argparse.Namespace) -> int:
    from .isolation_partner import IsolationRegistry

    _print_json({"partners": IsolationRegistry(Path.cwd()).list()})
    return 0


def cmd_isolation_plan(args: argparse.Namespace) -> int:
    from .isolation_partner import IsolationRegistry

    _print_json(
        IsolationRegistry(Path.cwd()).plan(args.partner, agent_id=args.agent or "agent")
    )
    return 0


def cmd_isolation_apply(args: argparse.Namespace) -> int:
    from .isolation_partner import IsolationRegistry

    _print_json(
        IsolationRegistry(Path.cwd()).apply(
            args.partner, agent_id=args.agent or "agent", dry_run=not args.execute
        )
    )
    return 0


def cmd_isolation_certify(args: argparse.Namespace) -> int:
    from .partner_cert import PartnerRuntimeCertifier

    _print_json(
        PartnerRuntimeCertifier(Path.cwd()).certify(
            args.partner,
            agent_id=args.agent or "cert-probe",
            attested=bool(args.attested),
            issuer=args.issuer or "narna-local",
        )
    )
    return 0


def cmd_isolation_certs(args: argparse.Namespace) -> int:
    from .partner_cert import PartnerRuntimeCertifier

    _print_json({"certificates": PartnerRuntimeCertifier(Path.cwd()).list()})
    return 0


def cmd_isolation_verify_cert(args: argparse.Namespace) -> int:
    from .partner_cert import PartnerRuntimeCertifier

    out = PartnerRuntimeCertifier(Path.cwd()).verify(args.partner)
    _print_json(out)
    return 0 if out.get("ok") else 2


def cmd_binding_list(args: argparse.Namespace) -> int:
    from .council_binding import CouncilBinding

    _print_json({"bindings": CouncilBinding(Path.cwd()).list()})
    return 0


def cmd_binding_verify(args: argparse.Namespace) -> int:
    from .council_binding import CouncilBinding

    _print_json(CouncilBinding(Path.cwd()).verify(args.binding))
    return 0


def cmd_reputation_export(args: argparse.Namespace) -> int:
    from .reputation import ReputationStore

    _print_json(ReputationStore(Path.cwd()).export_digest(args.agent))
    return 0


def cmd_reputation_import(args: argparse.Namespace) -> int:
    import json

    from .reputation import ReputationStore

    bundle = json.loads(Path(args.path).read_text(encoding="utf-8"))
    _print_json(
        ReputationStore(Path.cwd()).import_digest(bundle, map_to_agent=args.map_to)
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

    bench = sub.add_parser("benchmark", help="Trust / governance / Decision Benchmark")
    bench.add_argument("--spec", default="agent.yaml")
    bench.add_argument("--avg", action="store_true", help="Average trust score for agent")
    bench.add_argument("--governance", action="store_true", help="Governance leaderboard")
    bench.add_argument("--narna-score", action="store_true", dest="narna_score", help="NARNA Score (0-100)")
    bench.add_argument("--limit", type=int, default=20)
    bench.set_defaults(func=cmd_benchmark)
    bench_sub = bench.add_subparsers(dest="bench_cmd")
    b_run = bench_sub.add_parser("run", help="Run NARNA Decision Benchmark (ACT/REVIEW/REJECT)")
    b_run.add_argument("--agent", default="mock", choices=["mock", "strip"], help="Proposal agent")
    b_run.add_argument("--dir", default=None, help="Scenarios directory (default: benchmark/decisions)")
    b_run.add_argument("--category", default=None, help="Filter category (research|code|procurement|…)")
    b_run.add_argument("--limit", type=int, default=None, dest="run_limit", help="Max scenarios")
    b_run.add_argument("--min-accuracy", type=float, default=1.0, dest="min_accuracy")
    b_run.add_argument("--verbose", action="store_true", help="Include per-scenario results")
    b_run.add_argument("--write-leaderboard", action="store_true", dest="write_leaderboard")
    b_run.add_argument(
        "--leaderboard-path",
        default="benchmark/leaderboard.json",
        dest="leaderboard_path",
    )
    b_run.set_defaults(func=cmd_benchmark_run, decision_run=True)

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
    pk_buy = pkg_sub.add_parser("buy", help="Purchase package (local take-rate ledger)")
    pk_buy.add_argument("package_id")
    pk_buy.set_defaults(func=cmd_package_buy)

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

    conf = sub.add_parser("conformance", help="UGS conformance checks (badge eligibility)")
    conf.add_argument("--workspace", default=".", help="Workspace with narna.yaml")
    conf.add_argument("--json", action="store_true")
    conf.set_defaults(func=cmd_conformance)

    decision = sub.add_parser("decision", help="Decision OS — evaluate with Decision Package")
    decision_sub = decision.add_subparsers(dest="decision_cmd", required=True)
    d_eval = decision_sub.add_parser("evaluate", help="Evaluate action → DecisionResult")
    d_eval.add_argument("--action", required=True, help="Action id e.g. contract.sign")
    d_eval.add_argument("--question", default=None, help="Natural-language question")
    d_eval.add_argument("--provider", default="legal-decision", help="Decision Package provider")
    d_eval.add_argument("--version", default=None)
    d_eval.add_argument("--path", default=None, help="Path to DecisionPackage YAML")
    d_eval.add_argument(
        "--evidence",
        default="",
        help="Comma-separated present evidence types (e.g. policy.decision,human.review)",
    )
    d_eval.add_argument("--session", default=None, help="Optional governance session id")
    d_eval.add_argument("--customer", default=None)
    d_eval.add_argument("--contract", default=None)
    d_eval.add_argument("--project", default=None)
    d_eval.add_argument("--strict", action="store_true", help="Exit 2 on deny")
    d_eval.set_defaults(func=cmd_decision_evaluate)

    adqa = sub.add_parser("adqa", help="ADQA — Decision Quality Score (NGS-0024)")
    adqa_sub = adqa.add_subparsers(dest="adqa_cmd", required=True)
    a_chk = adqa_sub.add_parser("check", help="Evaluate + DQS + Decision Guardian")
    a_chk.add_argument("--action", required=True)
    a_chk.add_argument("--provider", default="legal-decision")
    a_chk.add_argument("--evidence", default="")
    a_chk.add_argument("--agent", default=None)
    a_chk.add_argument("--question", default=None)
    a_chk.add_argument("--strict", action="store_true", help="Exit 2 on guardian reject")
    a_chk.add_argument("--no-persist", action="store_true", help="Do not write Decision Memory")
    a_chk.set_defaults(func=cmd_adqa_check)

    reason = sub.add_parser("reason", help="Model Router complete (NGS-0028)")
    reason.add_argument("--message", required=True)
    reason.add_argument("--task", default="reason", choices=["cheap", "reason", "challenge", "analyze", "plan", "decide"])
    reason.add_argument("--provider", default=None, help="mock|openrouter|openai|ollama")
    reason.set_defaults(func=cmd_reason)

    ask = sub.add_parser("ask", help="Ask NARNA Agent (NGS-0029)")
    ask.add_argument("message", nargs="?", default=None)
    ask.add_argument("--message", dest="message_opt", default=None)
    ask.add_argument("--challenge", action="store_true")
    ask.add_argument("--provider", default=None)
    ask.set_defaults(func=cmd_ask)

    trace = sub.add_parser("trace", help="Decision Trace list/get (NGS-0030)")
    trace_sub = trace.add_subparsers(dest="trace_cmd", required=True)
    tr_list = trace_sub.add_parser("list")
    tr_list.add_argument("--limit", type=int, default=20)
    tr_list.set_defaults(func=cmd_trace)
    tr_get = trace_sub.add_parser("get")
    tr_get.add_argument("trace_id")
    tr_get.set_defaults(func=cmd_trace)

    replay = sub.add_parser("replay", help="Replay a Decision Trace")
    replay.add_argument("trace_id")
    replay.add_argument("--context", default=None)
    replay.add_argument("--provider", default=None)
    replay.set_defaults(func=cmd_replay)

    evaluate_p = sub.add_parser("evaluate", help="ADQA evaluate any action (universal API)")
    evaluate_p.add_argument("action")
    evaluate_p.add_argument("--evidence", default="", help="Comma-separated evidence ids")
    evaluate_p.add_argument("--question", default=None)
    evaluate_p.set_defaults(func=cmd_evaluate)

    chat = sub.add_parser("chat", help="Interactive Hermes-like REPL with slash commands")
    chat.add_argument("--provider", default=None)
    chat.set_defaults(func=cmd_chat)

    tui = sub.add_parser("tui", help="Fullscreen TUI (requires: pip install 'narna[tui]')")
    tui.add_argument("--provider", default=None)
    tui.set_defaults(func=cmd_tui)

    desk = sub.add_parser("desktop", help="NARNA Desktop on your PC (local Ask UI)")
    desk.add_argument("--host", default="127.0.0.1")
    desk.add_argument("--port", type=int, default=None)
    desk.add_argument("--workspace", default=None, help="Default: ~/.narna")
    desk.add_argument("--no-browser", action="store_true")
    desk.add_argument("--tui", action="store_true", help="Use fullscreen TUI instead of browser")
    desk.add_argument("--provider", default=None)
    desk.set_defaults(func=cmd_desktop)

    cfg_p = sub.add_parser("config", help="Show/set ~/.narna config (json or yaml)")
    cfg_sub = cfg_p.add_subparsers(dest="config_cmd", required=True)
    cfg_show = cfg_sub.add_parser("show", help="Print masked config")
    cfg_show.add_argument("--home", default=None, help="Default: ~/.narna")
    cfg_show.set_defaults(func=cmd_config)
    cfg_set = cfg_sub.add_parser("set", help="Set provider|apiKey|model|shellBackend|browserEnabled")
    cfg_set.add_argument("key")
    cfg_set.add_argument("value")
    cfg_set.add_argument("--home", default=None)
    cfg_set.set_defaults(func=cmd_config)

    skills_p = sub.add_parser("skills", help="Local skills + Skill Hub (zip / sync)")
    skills_sub = skills_p.add_subparsers(dest="skills_cmd", required=True)
    sk_list = skills_sub.add_parser("hub-list", help="List local Skill Hub index")
    sk_list.set_defaults(func=cmd_skills)
    sk_ez = skills_sub.add_parser("export-zip", help="Export hub as SKILL.md zip")
    sk_ez.add_argument("--out", default="skills-hub.zip")
    sk_ez.set_defaults(func=cmd_skills)
    sk_iz = skills_sub.add_parser("import-zip", help="Import SKILL.md zip into hub")
    sk_iz.add_argument("path")
    sk_iz.set_defaults(func=cmd_skills)
    sk_sy = skills_sub.add_parser("hub-sync", help="Sync from UAP_SKILL_HUB_INDEX_URL or --url")
    sk_sy.add_argument("--url", default=None)
    sk_sy.set_defaults(func=cmd_skills)

    gw = sub.add_parser("gateway", help="Unified multi-channel social gateway")
    gw_sub = gw.add_subparsers(dest="gateway_cmd", required=True)
    gw_ch = gw_sub.add_parser("channels", help="List all social channels and env keys")
    gw_ch.set_defaults(func=cmd_gateway)
    gw_st = gw_sub.add_parser("status")
    gw_st.set_defaults(func=cmd_gateway)
    gw_once = gw_sub.add_parser("once", help="Poll channels once")
    gw_once.add_argument("--provider", default=None)
    gw_once.set_defaults(func=cmd_gateway)
    gw_run = gw_sub.add_parser("run", help="Run forever")
    gw_run.add_argument("--provider", default=None)
    gw_run.add_argument("--max-iters", type=int, default=None)
    gw_run.set_defaults(func=cmd_gateway)
    gw_pair = gw_sub.add_parser("pair", help="Confirm pairing code or pair chat id directly")
    gw_pair.add_argument("--code", default=None, help="Pending pairing code")
    gw_pair.add_argument("--channel", default="telegram")
    gw_pair.add_argument("--external-id", dest="external_id", default=None)
    gw_pair.set_defaults(func=cmd_gateway)

    cmem = sub.add_parser("cmem", help="CMEM bridge — continuity memory feedstock")
    cmem_sub = cmem.add_subparsers(dest="cmem_cmd", required=True)
    cm_st = cmem_sub.add_parser("status", help="Bridge status / env")
    cm_st.set_defaults(func=cmd_cmem_status)
    cm_se = cmem_sub.add_parser("search", help="Search observations (local or HTTP)")
    cm_se.add_argument("query")
    cm_se.add_argument("--limit", type=int, default=8)
    cm_se.set_defaults(func=cmd_cmem_search)
    cm_in = cmem_sub.add_parser("ingest", help="Ingest local observation stub")
    cm_in.add_argument("--summary", required=True)
    cm_in.add_argument("--action", default=None)
    cm_in.add_argument("--tags", default="")
    cm_in.set_defaults(func=cmd_cmem_ingest)

    integ = sub.add_parser("integrations", help="List hot AI stack adapters + CMEM")
    integ.set_defaults(func=cmd_integrations)

    dqs = sub.add_parser("dqs", help="DQS Network — multi-org priors (NGS-0027)")
    dqs_sub = dqs.add_subparsers(dest="dqs_cmd", required=True)
    dqs_st = dqs_sub.add_parser("status")
    dqs_st.set_defaults(func=cmd_dqs_status)
    dqs_opt = dqs_sub.add_parser("opt-in")
    dqs_opt.add_argument("--off", action="store_true")
    dqs_opt.set_defaults(func=cmd_dqs_opt_in)
    dqs_ex = dqs_sub.add_parser("export")
    dqs_ex.add_argument("--min-count", type=int, default=3)
    dqs_ex.set_defaults(func=cmd_dqs_export)
    dqs_im = dqs_sub.add_parser("import")
    dqs_im.add_argument("path")
    dqs_im.set_defaults(func=cmd_dqs_import)

    dmem = sub.add_parser("dmemory", help="Decision Memory — quality records (NGS-0025)")
    dmem_sub = dmem.add_subparsers(dest="dmemory_cmd", required=True)
    dm_q = dmem_sub.add_parser("query", help="Query decision records")
    dm_q.add_argument("--action", default=None)
    dm_q.add_argument("--customer", default=None)
    dm_q.add_argument("--limit", type=int, default=20)
    dm_q.add_argument("--with-outcome", action="store_true")
    dm_q.set_defaults(func=cmd_dmemory_query)
    dm_l = dmem_sub.add_parser("lessons", help="List lessons for an action")
    dm_l.add_argument("--action", default=None)
    dm_l.add_argument("--limit", type=int, default=5)
    dm_l.set_defaults(func=cmd_dmemory_lessons)

    learn = sub.add_parser("learning", help="Outcome Learning Engine")
    learn_sub = learn.add_subparsers(dest="learning_cmd", required=True)
    l_out = learn_sub.add_parser("outcome", help="Record outcome + update priors")
    l_out.add_argument("decision_id")
    l_out.add_argument("--status", required=True)
    l_out.add_argument("--detail", default=None)
    l_out.add_argument("--score", type=float, default=None)
    l_out.add_argument("--lesson", default=None)
    l_out.set_defaults(func=cmd_learning_outcome)

    connect = sub.add_parser("connect", help="Decision OS — Connect module")
    connect_sub = connect.add_subparsers(dest="connect_cmd", required=True)
    cn_cat = connect_sub.add_parser("catalog", help="List builtins + registered connectors")
    cn_cat.set_defaults(func=cmd_connect_catalog)
    cn_reg = connect_sub.add_parser("register", help="Register a connector")
    cn_reg.add_argument("--type", required=True)
    cn_reg.add_argument("--name", required=True)
    cn_reg.add_argument("--endpoint", default=None)
    cn_reg.set_defaults(func=cmd_connect_register)
    cn_pr = connect_sub.add_parser("probe", help="Probe a registered connector")
    cn_pr.add_argument("connector")
    cn_pr.set_defaults(func=cmd_connect_probe)

    know = sub.add_parser("knowledge", help="Decision OS — Knowledge graph")
    know_sub = know.add_subparsers(dest="knowledge_cmd", required=True)
    k_up = know_sub.add_parser("upsert", help="Upsert an entity")
    k_up.add_argument("--kind", required=True)
    k_up.add_argument("--name", required=True)
    k_up.add_argument("--id", default=None)
    k_up.add_argument("--props", default=None, help="JSON object")
    k_up.set_defaults(func=cmd_knowledge_upsert)
    k_q = know_sub.add_parser("query", help="Query entities")
    k_q.add_argument("--kind", default=None)
    k_q.add_argument("--q", default=None)
    k_q.add_argument("--limit", type=int, default=50)
    k_q.set_defaults(func=cmd_knowledge_query)
    k_rel = know_sub.add_parser("relate", help="Relate two entities")
    k_rel.add_argument("--from", dest="frm", required=True)
    k_rel.add_argument("--to", required=True)
    k_rel.add_argument("--type", required=True)
    k_rel.set_defaults(func=cmd_knowledge_relate)

    mem = sub.add_parser("memory", help="Decision OS — Durable Memory")
    mem_sub = mem.add_subparsers(dest="memory_cmd", required=True)
    m_put = mem_sub.add_parser("put", help="Put records into a scope")
    m_put.add_argument("--scope", required=True, choices=["project", "customer", "contract", "agent", "session", "global"])
    m_put.add_argument("--id", required=True)
    m_put.add_argument("--data", required=True, help="JSON object")
    m_put.set_defaults(func=cmd_memory_put)
    m_get = mem_sub.add_parser("get", help="Get records from a scope")
    m_get.add_argument("--scope", required=True)
    m_get.add_argument("--id", required=True)
    m_get.add_argument("--keys", default=None)
    m_get.set_defaults(func=cmd_memory_get)

    auto = sub.add_parser("automate", help="Decision OS — Automation pipeline stub")
    auto_sub = auto.add_subparsers(dest="automate_cmd", required=True)
    a_run = auto_sub.add_parser("run", help="Run trigger → decision → plan")
    a_run.add_argument("--trigger", required=True)
    a_run.add_argument("--action", required=True)
    a_run.add_argument("--provider", default="legal-decision")
    a_run.add_argument("--path", default=None)
    a_run.add_argument("--customer", default=None)
    a_run.set_defaults(func=cmd_automate_run)

    dmarket = sub.add_parser("dmarket", help="Decision OS — Decision Package marketplace")
    dmarket_sub = dmarket.add_subparsers(dest="dmarket_cmd", required=True)
    dm_l = dmarket_sub.add_parser("list", help="List Decision Packages")
    dm_l.add_argument("--industry", default=None, help="Filter e.g. finance, hospital, crypto")
    dm_l.add_argument("--all", action="store_true", help="Include GovernancePackages too")
    dm_l.set_defaults(func=cmd_dmarket_list)
    dm_i = dmarket_sub.add_parser("install", help="Install package by provider/stem")
    dm_i.add_argument("provider")
    dm_i.set_defaults(func=cmd_dmarket_install)

    cap = sub.add_parser("capability", help="Guardian — Capability Passport evaluate (NGS-0015)")
    cap_sub = cap.add_subparsers(dest="cap_cmd", required=True)
    c_eval = cap_sub.add_parser("evaluate", help="Evaluate capability mode for an agent")
    c_eval.add_argument("--capability", required=True, help="e.g. email, create.agent, wallet")
    c_eval.add_argument("--agent", default=None)
    c_eval.add_argument("--path", default=None, help="CapabilityPassport YAML")
    c_eval.add_argument("--target", default=None, help="Whitelist target (e.g. MCP URL)")
    c_eval.add_argument("--profile", default="guardian", choices=["guardian", "enterprise"])
    c_eval.add_argument("--strict", action="store_true")
    c_eval.set_defaults(func=cmd_capability_evaluate)

    kill = sub.add_parser("kill", help="Guardian — Kill Token local/domain (NGS-0019)")
    kill_sub = kill.add_subparsers(dest="kill_cmd", required=True)
    k_issue = kill_sub.add_parser("issue", help="Issue kill (local|domain; global via council)")
    k_issue.add_argument("--tier", choices=["local", "domain", "global"], default="local")
    k_issue.add_argument("--agent", default=None)
    k_issue.add_argument("--session", default=None)
    k_issue.add_argument("--domain", default=None)
    k_issue.add_argument("--reason", default="manual")
    k_issue.add_argument("--by", default="operator")
    k_issue.set_defaults(func=cmd_kill_issue)
    k_status = kill_sub.add_parser("status", help="Check kill status")
    k_status.add_argument("--agent", default=None)
    k_status.add_argument("--session", default=None)
    k_status.add_argument("--domain", default=None)
    k_status.set_defaults(func=cmd_kill_status)
    k_rev = kill_sub.add_parser("revoke", help="Revoke a kill token")
    k_rev.add_argument("token")
    k_rev.set_defaults(func=cmd_kill_revoke)

    threat = sub.add_parser("threat", help="Guardian — Behavioral Threat Engine (NGS-0017)")
    threat_sub = threat.add_subparsers(dest="threat_cmd", required=True)
    t_an = threat_sub.add_parser("analyze", help="Analyze session execution graph")
    t_an.add_argument("--session", required=True)
    t_an.add_argument("--auto-kill", action="store_true", help="Issue local kill if risk>=0.9")
    t_an.add_argument("--strict", action="store_true")
    t_an.set_defaults(func=cmd_threat_analyze)

    coll = sub.add_parser("collective", help="Guardian L3 — Collective Defense (NGS-0020)")
    coll_sub = coll.add_subparsers(dest="collective_cmd", required=True)
    c_opt = coll_sub.add_parser("opt-in", help="Opt in (or --off) to signature sharing")
    c_opt.add_argument("--off", action="store_true")
    c_opt.set_defaults(func=cmd_collective_opt_in)
    c_pub = coll_sub.add_parser("publish", help="Publish threat signature from a session")
    c_pub.add_argument("--session", required=True)
    c_pub.add_argument("--org", default=None)
    c_pub.add_argument("--min-risk", type=float, default=0.0)
    c_pub.set_defaults(func=cmd_collective_publish)
    c_imp = coll_sub.add_parser("import", help="Import a signature JSON into inbox")
    c_imp.add_argument("path")
    c_imp.set_defaults(func=cmd_collective_import)
    c_list = coll_sub.add_parser("list", help="List inbox/outbox signatures")
    c_list.add_argument("--source", choices=["inbox", "outbox"], default="inbox")
    c_list.set_defaults(func=cmd_collective_list)
    c_match = coll_sub.add_parser("match", help="Match inbox signatures by patterns")
    c_match.add_argument("--patterns", default="", help="comma-separated pattern ids")
    c_match.add_argument("--band", default=None)
    c_match.set_defaults(func=cmd_collective_match)
    c_apply = coll_sub.add_parser("apply", help="Apply signature: restrict caps / optional kill")
    c_apply.add_argument("signature")
    c_apply.add_argument("--agent", default=None)
    c_apply.add_argument("--kill", action="store_true")
    c_apply.set_defaults(func=cmd_collective_apply)
    c_peers = coll_sub.add_parser("peers", help="List or set federation peer URLs")
    c_peers.add_argument("--set", default=None, help="comma-separated peer base URLs")
    c_peers.set_defaults(func=cmd_collective_peers)
    c_push = coll_sub.add_parser("push", help="Push outbox signatures to peers")
    c_push.set_defaults(func=cmd_collective_push)
    c_pull = coll_sub.add_parser("pull", help="Pull peer signatures into inbox")
    c_pull.set_defaults(func=cmd_collective_pull)
    c_exp = coll_sub.add_parser("export", help="Export outbox bundle")
    c_exp.set_defaults(func=cmd_collective_export)
    c_ib = coll_sub.add_parser("import-bundle", help="Import federation bundle JSON")
    c_ib.add_argument("path")
    c_ib.set_defaults(func=cmd_collective_import_bundle)

    cti = sub.add_parser("cti", help="Guardian Tier D — CTI Hub relay")
    cti_sub = cti.add_subparsers(dest="cti_cmd", required=True)
    cti_s = cti_sub.add_parser("submit", help="Submit signature JSON to hub feed")
    cti_s.add_argument("path")
    cti_s.add_argument("--org", default=None)
    cti_s.set_defaults(func=cmd_cti_submit)
    cti_f = cti_sub.add_parser("feed", help="List hub feed")
    cti_f.add_argument("--limit", type=int, default=50)
    cti_f.set_defaults(func=cmd_cti_feed)
    cti_p = cti_sub.add_parser("pull", help="Pull hub feed into local inbox")
    cti_p.add_argument("--limit", type=int, default=50)
    cti_p.set_defaults(func=cmd_cti_pull)
    cti_r = cti_sub.add_parser("relay", help="Relay local outbox into hub")
    cti_r.set_defaults(func=cmd_cti_relay)
    cti_h = cti_sub.add_parser("hubs", help="List or set remote CTI hub URLs")
    cti_h.add_argument("--set", default=None, help="comma-separated hub base URLs")
    cti_h.set_defaults(func=cmd_cti_hubs)
    cti_sy = cti_sub.add_parser("sync", help="Push/pull mesh sync with remote hubs")
    cti_sy.add_argument("--hubs", default=None)
    cti_sy.add_argument("--push-only", action="store_true")
    cti_sy.add_argument("--pull-only", action="store_true")
    cti_sy.set_defaults(func=cmd_cti_sync)

    aiconst = sub.add_parser(
        "ai-constitution",
        help="Guardian L4 — non-agent-editable AI Constitution",
    )
    aiconst_sub = aiconst.add_subparsers(dest="ai_constitution_cmd", required=True)
    ct_in = aiconst_sub.add_parser("install", help="Install default GuardianConstitution")
    ct_in.set_defaults(func=cmd_constitution_install)
    ct_show = aiconst_sub.add_parser("show", help="Show active constitution")
    ct_show.set_defaults(func=cmd_constitution_show)
    ct_ev = aiconst_sub.add_parser("evaluate", help="Evaluate action against constitution")
    ct_ev.add_argument("--action", required=True)
    ct_ev.add_argument("--agent", default=None)
    ct_ev.add_argument("--strict", action="store_true")
    ct_ev.set_defaults(func=cmd_constitution_evaluate)

    council = sub.add_parser("council", help="Guardian L4 — Governance Council")
    council_sub = council.add_subparsers(dest="council_cmd", required=True)
    co_in = council_sub.add_parser("install", help="Install default council")
    co_in.set_defaults(func=cmd_council_install)
    co_pr = council_sub.add_parser(
        "propose", help="Propose amend / domain_kill / global_kill"
    )
    co_pr.add_argument(
        "--kind",
        required=True,
        choices=["amend_constitution", "domain_kill", "global_kill"],
    )
    co_pr.add_argument("--by", required=True, help="council member id")
    co_pr.add_argument("--yaml", default=None, help="path for amend_constitution")
    co_pr.add_argument("--domain", default=None)
    co_pr.add_argument("--reason", default=None)
    co_pr.set_defaults(func=cmd_council_propose)
    co_ap = council_sub.add_parser("approve", help="Approve a proposal (quorum executes)")
    co_ap.add_argument("proposal")
    co_ap.add_argument("--by", required=True)
    co_ap.set_defaults(func=cmd_council_approve)

    bind = sub.add_parser("binding", help="Guardian Tier D — Council legal bindings")
    bind_sub = bind.add_subparsers(dest="binding_cmd", required=True)
    b_l = bind_sub.add_parser("list", help="List sealed bindings")
    b_l.set_defaults(func=cmd_binding_list)
    b_v = bind_sub.add_parser("verify", help="Verify a binding")
    b_v.add_argument("binding")
    b_v.set_defaults(func=cmd_binding_verify)

    juris = sub.add_parser("jurisdiction", help="Guardian Tier D — jurisdiction templates")
    juris_sub = juris.add_subparsers(dest="jurisdiction_cmd", required=True)
    j_l = juris_sub.add_parser("list", help="List jurisdiction templates")
    j_l.set_defaults(func=cmd_jurisdiction_list)
    j_a = juris_sub.add_parser("apply", help="Apply template to a sealed binding")
    j_a.add_argument("binding")
    j_a.add_argument("--jurisdiction", required=True, help="eu-gdpr | us-enterprise | vn-pdpa")
    j_a.set_defaults(func=cmd_jurisdiction_apply)

    iso = sub.add_parser("isolation", help="Guardian Tier D — isolation partners")
    iso_sub = iso.add_subparsers(dest="isolation_cmd", required=True)
    i_l = iso_sub.add_parser("list", help="List partners")
    i_l.set_defaults(func=cmd_isolation_list)
    i_p = iso_sub.add_parser("plan", help="Plan isolation for agent")
    i_p.add_argument("--partner", required=True, choices=["docker", "kubernetes", "k8s"])
    i_p.add_argument("--agent", default="agent")
    i_p.set_defaults(func=cmd_isolation_plan)
    i_a = iso_sub.add_parser("apply", help="Apply isolation (default dry-run)")
    i_a.add_argument("--partner", required=True, choices=["docker", "kubernetes", "k8s"])
    i_a.add_argument("--agent", default="agent")
    i_a.add_argument("--execute", action="store_true")
    i_a.set_defaults(func=cmd_isolation_apply)
    i_c = iso_sub.add_parser("certify", help="Certify partner runtime (NGS-0016-partner-cert)")
    i_c.add_argument("--partner", required=True, choices=["docker", "kubernetes", "k8s"])
    i_c.add_argument("--agent", default="cert-probe")
    i_c.add_argument("--attested", action="store_true", help="Operator attestation → L3")
    i_c.add_argument("--issuer", default="narna-local")
    i_c.set_defaults(func=cmd_isolation_certify)
    i_cs = iso_sub.add_parser("certs", help="List partner certificates")
    i_cs.set_defaults(func=cmd_isolation_certs)
    i_v = iso_sub.add_parser("verify-cert", help="Re-audit and verify partner certificate")
    i_v.add_argument("--partner", required=True, choices=["docker", "kubernetes", "k8s"])
    i_v.set_defaults(func=cmd_isolation_verify_cert)

    rep = sub.add_parser("reputation", help="Guardian — Agent Reputation (NGS-0018)")
    rep_sub = rep.add_subparsers(dest="reputation_cmd", required=True)
    r_get = rep_sub.add_parser("get", help="Get reputation for agent")
    r_get.add_argument("agent")
    r_get.set_defaults(func=cmd_reputation_get)
    r_rec = rep_sub.add_parser("record", help="Record origin/creator/model (+ optional attestation)")
    r_rec.add_argument("agent")
    r_rec.add_argument("--origin", default=None)
    r_rec.add_argument("--creator", default=None)
    r_rec.add_argument("--model", default=None)
    r_rec.add_argument("--attested", action="store_true")
    r_rec.add_argument("--attestation", default=None)
    r_rec.set_defaults(func=cmd_reputation_record)
    r_v = rep_sub.add_parser("violate", help="Record a violation")
    r_v.add_argument("agent")
    r_v.add_argument("--kind", required=True)
    r_v.add_argument("--severity", type=float, default=0.5)
    r_v.add_argument("--detail", default=None)
    r_v.set_defaults(func=cmd_reputation_violate)
    r_f = rep_sub.add_parser("feedback", help="Peer feedback 0–100")
    r_f.add_argument("agent")
    r_f.add_argument("--score", type=float, required=True)
    r_f.add_argument("--by", default="peer")
    r_f.add_argument("--note", default=None)
    r_f.set_defaults(func=cmd_reputation_feedback)
    r_ex = rep_sub.add_parser("export", help="Export privacy-preserving reputation digest")
    r_ex.add_argument("--agent", default=None)
    r_ex.set_defaults(func=cmd_reputation_export)
    r_im = rep_sub.add_parser("import", help="Import peer reputation digest")
    r_im.add_argument("path")
    r_im.add_argument("--map-to", default=None, help="Apply peer low/critical to this agent")
    r_im.set_defaults(func=cmd_reputation_import)

    cont = sub.add_parser("container", help="Guardian — Agent Container (NGS-0016)")
    cont_sub = cont.add_subparsers(dest="container_cmd", required=True)
    ct_i = cont_sub.add_parser("install", help="Install default AgentContainer")
    ct_i.set_defaults(func=cmd_container_install)
    ct_p = cont_sub.add_parser("profile", help="Show container profile")
    ct_p.add_argument("--agent", default=None)
    ct_p.set_defaults(func=cmd_container_profile)
    ct_c = cont_sub.add_parser("check", help="Check action against container contract")
    ct_c.add_argument("--agent", default=None)
    ct_c.add_argument("--action", required=True)
    ct_c.add_argument("--tool", default=None)
    ct_c.add_argument("--network", action="store_true")
    ct_c.add_argument("--spawn-depth", type=int, default=None)
    ct_c.add_argument("--strict", action="store_true")
    ct_c.set_defaults(func=cmd_container_check)
    ct_d = cont_sub.add_parser("docker-run", help="Plan/run optional Docker Agent Container")
    ct_d.add_argument("--agent", default="agent")
    ct_d.add_argument("--image", default="narna/agent-container:0.1")
    ct_d.add_argument("--network", default="none")
    ct_d.add_argument("--execute", action="store_true", help="Actually run docker (default dry-run)")
    ct_d.set_defaults(func=cmd_container_docker)

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
