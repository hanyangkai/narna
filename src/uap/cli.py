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
    agent = Agent(workspace=Path.cwd())
    agent.runtime.init()
    spec_dst = Path("agent.yaml")
    if not spec_dst.exists():
        example = Path("specs/examples/trading-agent.yaml")
        if example.exists():
            spec_dst.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Created {spec_dst} from example.")
        else:
            print("Created minimal agent.yaml.")
    if spec_dst.exists():
        spec = load_agent_spec(spec_dst)
        identity = IdentityStore(Path.cwd()).issue(spec)
        AgentRegistry(Path.cwd()).register(spec_dst, workspace=Path.cwd())
        Marketplace(Path.cwd()).index()
        print(f"Issued identity for {spec.agent_id}")
        _print_json({"agentId": identity["agentId"], "specHash": identity["specHash"]})
    print("Initialized .uap workspace.")
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
    store = BenchmarkStore(Path.cwd())
    if args.avg:
        agent = Agent.from_spec(args.spec)
        avg = store.average_score(agent_id=agent.spec.agent_id)
        _print_json({"agentId": agent.spec.agent_id, "averageScore": avg})
        return 0
    rows = store.list(limit=args.limit)
    _print_json({"records": rows})
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
    agent = Agent.from_spec(args.spec)
    doc = agent.passport(run_id=args.run, refresh=args.refresh)
    _print_json(doc)
    return 0


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
        description="NARNA CLI — Open Runtime for Trusted AI Agents (UAP protocol)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="Initialize workspace, identity, registry")
    init.set_defaults(func=cmd_init)

    doctor = sub.add_parser("doctor", help="Validate workspace + AgentSpec + identity")
    doctor.add_argument("--spec", default="agent.yaml")
    doctor.add_argument("--full", action="store_true", help="Full spec conformance checks")
    doctor.set_defaults(func=cmd_doctor)

    bench = sub.add_parser("benchmark", help="Trust score benchmarks across runs")
    bench.add_argument("--spec", default="agent.yaml")
    bench.add_argument("--avg", action="store_true", help="Average score for agent")
    bench.add_argument("--limit", type=int, default=20)
    bench.set_defaults(func=cmd_benchmark)

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

    passport = sub.add_parser("passport", help="Show or refresh passport")
    passport.add_argument("--spec", default="agent.yaml")
    passport.add_argument("--run", default=None)
    passport.add_argument("--refresh", action="store_true")
    passport.set_defaults(func=cmd_passport)

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
        help="Validate / show constitution.yaml (Constitution Layer)",
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
