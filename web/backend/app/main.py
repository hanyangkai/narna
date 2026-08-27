from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any


def _load_dotenv() -> None:
    """Load web/backend/.env into os.environ (does not override existing vars)."""
    from pathlib import Path

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        pass


_load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from .auth import get_org_from_api_key, get_org_optional
from .billing import (
    add_plan_period,
    checkout_usd_amount,
    count_governance_units,
    normalize_plan,
    now_utc,
    plan_adqa_hard_cap,
    plan_adqa_soft_cap,
    plan_agent_turns_hard_cap,
    plan_allows_byo_llm,
    plan_event_limit,
    plan_gu_limit,
    plan_price_cents,
    plan_seats,
    plan_usd_price,
)
from .crypto_bot import start_background_bot
from .agent_jobs_ticker import start_jobs_ticker, tick_all_tenants
from .crypto_chains import build_pay_uri, list_supported_networks, validate_crypto_payment
from .invoice_utils import (
    allocate_unique_amount,
    build_qr_payload,
    expire_pending_invoices,
    invoice_expires_at,
)
from .database import get_db, init_db
from .metrics import METRICS
from .mcp_http import router as mcp_router
from .quota import bump_adqa_usage, bump_agent_turns, enforce_plan_limit
from .tenants import tenant_id_for_org, tenant_workspace
from .models import (
    ApiKey,
    GovernanceSessionRow,
    MarketplacePurchase,
    Organization,
    PaymentInvoice,
    RegistryAgent,
    RegistryGovernancePackage,
    RegistryPlugin,
    Run,
    RunEvent,
    TelemetryContribution,
    generate_api_key,
)
from .observability import configure_logging, init_sentry_if_configured
from .rate_limit import build_rate_limiter
from .schemas import (
    ApiKeyResponse,
    AgentAskRequest,
    AgentJobCreateRequest,
    AgentModelsPutRequest,
    AgentOutcomeRequest,
    AgentSkillHubInstallRequest,
    AgentSkillHubPublishRequest,
    AgentSkillHubSyncRequest,
    AgentSkillMarkdownImportRequest,
    BillingCheckoutRequest,
    BillingCheckoutResponse,
    BillingCryptoCheckoutRequest,
    BillingCryptoCheckoutResponse,
    BillingCryptoNetworkResponse,
    BillingInvoiceResponse,
    BillingMockSetPlanRequest,
    BillingStatusResponse,
    CertificationSubmitRequest,
    CertificationSubmitResponse,
    IngestRequest,
    IngestResponse,
    PluginPublishRequest,
    PluginPublishResponse,
    PluginSummary,
    PackagePublishRequest,
    PackagePublishResponse,
    PackagePurchaseRequest,
    PackagePurchaseResponse,
    PackageSummary,
    RegistryAgentSummary,
    RegistryPublishRequest,
    RegistryPublishResponse,
    RouterCompleteRequest,
    RunDetail,
    RunSummary,
    SessionDetail,
    SessionSummary,
    TelemetryAggregateResponse,
    TelemetryAggregateRow,
    TelemetryConsentRequest,
    TelemetryConsentResponse,
    TelemetryContributeRequest,
    TelemetryContributeResponse,
)

logger = logging.getLogger("uap-cloud")
configure_logging()

app = FastAPI(title="NARNA Cloud API", version="0.2.0")
app.include_router(mcp_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("UAP_CLOUD_CORS_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT_PER_MIN = int(os.environ.get("UAP_RATE_LIMIT_PER_MIN", "120"))
limiter = build_rate_limiter(limit_per_min=RATE_LIMIT_PER_MIN)


def _rate_key(req: Request) -> str:
    auth = req.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:]
    return req.client.host if req.client else "anon"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/health") or request.url.path in {"/v1/ready", "/mcp"}:
        if request.method == "GET" and request.url.path.startswith("/v1/health"):
            return await call_next(request)
        if request.url.path == "/v1/ready":
            return await call_next(request)
    METRICS.inc_request()
    key = _rate_key(request)
    allowed, retry_after = limiter.allow(key)
    if not allowed:
        METRICS.inc_429()
        return JSONResponse(
            status_code=429,
            content={"ok": False, "error": "rate_limited"},
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
    started = datetime.now(timezone.utc)
    response = await call_next(request)
    elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    METRICS.observe_latency(elapsed_ms)
    if response.status_code >= 500:
        METRICS.inc_error()
    logger.info(
        "request",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    sentry_on = init_sentry_if_configured()
    logger.info("startup", extra={"sentry_enabled": sentry_on})
    _seed_dev_org()
    _seed_marketplace_packages()
    _seed_demo_registry_agent()
    start_background_bot()
    start_jobs_ticker()


@app.post("/v1/agent/jobs/tick-all")
def agent_jobs_tick_all(request: Request) -> dict[str, Any]:
    """Ops cron: tick all tenant job queues (requires UAP_JOBS_TICK_SECRET)."""
    secret = os.environ.get("UAP_JOBS_TICK_SECRET", "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail="UAP_JOBS_TICK_SECRET not set")
    got = request.headers.get("X-Narna-Jobs-Secret", "")
    if got != secret:
        raise HTTPException(status_code=403, detail="invalid jobs secret")
    return {"ok": True, **tick_all_tenants()}


def _seed_dev_org() -> None:
    from .database import SessionLocal

    db = SessionLocal()
    try:
        if db.query(Organization).first() is not None:
            return
        org = Organization(name="dev", plan="free")
        db.add(org)
        db.flush()

        dev_key = "uap_live_dev_local_key_change_in_prod"
        import hashlib

        db.add(
            ApiKey(
                org_id=org.id,
                key_prefix=dev_key[:16],
                key_hash=hashlib.sha256(dev_key.encode()).hexdigest(),
                label="dev",
            )
        )
        db.commit()
        print(f"[UAP Cloud] Dev API key: {dev_key}")
    finally:
        db.close()


def _seed_demo_registry_agent() -> None:
    """Public demo passport for /passport/narna-demo-agent (no login) — Ed25519 signed."""
    from pathlib import Path
    import tempfile

    from .database import SessionLocal

    db = SessionLocal()
    try:
        agent_id = "narna-demo-agent"
        existing = (
            db.query(RegistryAgent).filter(RegistryAgent.agent_id == agent_id).first()
        )

        def _build_signed_passport() -> dict[str, Any]:
            passport: dict[str, Any] = {
                "passportId": "passport_demo_001",
                "apiVersion": "narna.ai/v1alpha1",
                "kind": "Passport",
                "identity": {
                    "agentId": agent_id,
                    "name": "NARNA Demo Agent",
                    "version": "0.1.0",
                    "creator": "narna.org",
                },
                "capability": {"declared": ["general", "governance", "audit"]},
                "governance": {
                    "policyRef": "local-default@0.0.0",
                    "package": "eu-ai-act@2.0.0",
                },
                "trust": {"score": 0.92, "band": "high", "algorithm": "vap-trust-v0"},
                "history": {"runCount": 128, "successCount": 126, "failureCount": 2, "violationCount": 0},
            }
            try:
                from uap.passport_sign import sign_passport

                with tempfile.TemporaryDirectory() as td:
                    return sign_passport(passport, Path(td))
            except Exception as e:
                logger.warning("demo passport sign failed: %s", e)
                return passport

        def _needs_resign(row: RegistryAgent) -> bool:
            if not row.passport_json:
                return True
            try:
                doc = json.loads(row.passport_json)
            except Exception:
                return True
            sig = doc.get("signature") if isinstance(doc, dict) else None
            return not (isinstance(sig, dict) and sig.get("value") and sig.get("publicKey"))

        if existing is not None:
            if _needs_resign(existing):
                signed = _build_signed_passport()
                existing.passport_json = json.dumps(signed)
                existing.trust_score = 0.92
                existing.verified = 1 if isinstance(signed.get("signature"), dict) else 0
                existing.name = "NARNA Demo Agent"
                existing.creator = "narna.org"
                db.commit()
            return

        signed = _build_signed_passport()
        org = db.query(Organization).first()
        db.add(
            RegistryAgent(
                agent_id=agent_id,
                name="NARNA Demo Agent",
                version="0.1.0",
                creator="narna.org",
                category="governance",
                capabilities_json=json.dumps(["general", "governance", "audit"]),
                trust_score=0.92,
                stars=42,
                downloads=1000,
                executions=5000,
                passport_json=json.dumps(signed),
                verified=1 if isinstance(signed.get("signature"), dict) else 0,
                org_id=org.id if org else None,
            )
        )
        db.commit()
    except Exception as e:
        logger.warning("demo registry seed skipped: %s", e)
    finally:
        db.close()


# Marketplace supply — seed global compliance Governance Packages (upsert on startup).
# Prices in cents; 0 = free. Take rate 20% (2000 bps) unless overridden.
_SEED_PACKAGES = [
    {"file": "eu-ai-act.yaml", "price_usd": 9900, "stars": 420, "downloads": 1280},
    {"file": "gdpr.yaml", "price_usd": 7900, "stars": 510, "downloads": 2100},
    {"file": "hipaa.yaml", "price_usd": 12900, "stars": 310, "downloads": 640},
    {"file": "pci-dss.yaml", "price_usd": 14900, "stars": 280, "downloads": 520},
    {"file": "ccpa-cpra.yaml", "price_usd": 6900, "stars": 190, "downloads": 410},
    {"file": "uk-dpa.yaml", "price_usd": 6900, "stars": 175, "downloads": 380},
    {"file": "china-pipl.yaml", "price_usd": 8900, "stars": 160, "downloads": 290},
    {"file": "brazil-lgpd.yaml", "price_usd": 5900, "stars": 120, "downloads": 210},
    {"file": "singapore-ai-gov.yaml", "price_usd": 4900, "stars": 140, "downloads": 260},
    {"file": "nist-ai-rmf.yaml", "price_usd": 0, "stars": 680, "downloads": 4500},
    {"file": "iso-42001.yaml", "price_usd": 9900, "stars": 240, "downloads": 580},
    {"file": "soc2-tsc.yaml", "price_usd": 11900, "stars": 350, "downloads": 920},
    {"file": "anthropic-constitution.yaml", "price_usd": 0, "stars": 210, "downloads": 1873},
]

# Old demo stub IDs replaced by legal-mapping packs
_OBSOLETE_PACKAGE_IDS = (
    "pkg_eu_ai_act_v1",
    "pkg_medical_v1",
)


def _seed_marketplace_packages() -> None:
    import hashlib
    from pathlib import Path

    try:
        import yaml  # type: ignore
    except Exception:
        return

    from .database import SessionLocal

    here = Path(__file__).resolve()
    examples_dir: Path | None = None
    for parent in here.parents:
        candidate = parent / "specs" / "examples" / "packages"
        if candidate.exists():
            examples_dir = candidate
            break
    if examples_dir is None:
        return

    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        org_id = org.id if org else None

        for obsolete_id in _OBSOLETE_PACKAGE_IDS:
            old = (
                db.query(RegistryGovernancePackage)
                .filter(RegistryGovernancePackage.package_id == obsolete_id)
                .first()
            )
            if old is not None:
                db.delete(old)

        for seed in _SEED_PACKAGES:
            path = examples_dir / seed["file"]
            if not path.exists():
                continue
            try:
                doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:
                continue
            meta = doc.get("metadata", {}) or {}
            spec = doc.get("spec", {}) or {}
            package_id = str(meta.get("id") or path.stem)
            spec_json = json.dumps(spec, sort_keys=True)
            row = (
                db.query(RegistryGovernancePackage)
                .filter(RegistryGovernancePackage.package_id == package_id)
                .first()
            )
            if row is None:
                row = RegistryGovernancePackage(package_id=package_id, org_id=org_id)
                db.add(row)
            row.name = str(meta.get("name") or package_id)
            row.version = str(meta.get("version") or "1.0.0")
            row.provider = str(meta.get("provider") or "community")
            row.package_kind = str(meta.get("packageKind") or "Compliance")
            row.license = str(meta.get("license") or "MIT")
            row.disclaimer = str(meta.get("disclaimer") or "")
            row.package_hash = hashlib.sha256(spec_json.encode()).hexdigest()
            row.spec_json = spec_json
            row.price_usd = int(seed.get("price_usd", 0))
            row.take_rate_bps = 2000
            row.stars = max(int(row.stars or 0), int(seed.get("stars", 0)))
            row.downloads = max(int(row.downloads or 0), int(seed.get("downloads", 0)))
            row.org_id = org_id
        db.commit()
    except Exception as e:  # pragma: no cover - seeding is best-effort
        logger.warning("marketplace seed skipped: %s", e)
    finally:
        db.close()


@app.get("/v1/health")
def health() -> dict[str, Any]:
    checks: dict[str, Any] = {"api": "ok"}
    status = "ok"
    # DB probe
    try:
        from sqlalchemy import text

        from .database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            checks["db"] = "ok"
        finally:
            db.close()
    except Exception as e:
        checks["db"] = f"down:{e}"
        status = "degraded"
    # Redis optional
    redis_url = os.environ.get("UAP_REDIS_URL") or ""
    if not redis_url:
        checks["redis"] = "not_configured"
    else:
        try:
            import socket
            from urllib.parse import urlparse

            u = urlparse(redis_url)
            host = u.hostname or "127.0.0.1"
            port = int(u.port or 6379)
            with socket.create_connection((host, port), timeout=1.5):
                checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"down:{e}"
            if status == "ok":
                status = "degraded"
    return {
        "status": status,
        "service": "narna-cloud",
        "version": "0.2.1",
        "api": "https://api.narna.org",
        "mcp": "https://api.narna.org/mcp",
        "checks": checks,
        "browser": _browser_health(),
        "shellBackend": (os.environ.get("UAP_SHELL_BACKEND") or "local").strip().lower(),
    }


def _browser_health() -> dict[str, Any]:
    try:
        from uap.browser_session import browser_ready

        return browser_ready()
    except Exception as e:
        return {"ready": False, "error": str(e)[:200]}


@app.get("/v1/ready")
def ready() -> dict[str, Any]:
    h = health()
    if h.get("checks", {}).get("db") != "ok":
        raise HTTPException(status_code=503, detail=h)
    return {"ready": True, **h}


@app.get("/v1/metrics/slo")
def metrics_slo() -> dict[str, Any]:
    return {"ok": True, "slo": METRICS.to_slo(), "service": "narna-cloud"}


@app.get("/v1/billing/paddle/status")
def paddle_billing_status(live_probe: bool = False) -> dict[str, Any]:
    """Paddle retired — NARNA Cloud is USDC/USDT only."""
    return {
        "billingMode": get_billing_mode(),
        "paddleConfigured": False,
        "retired": True,
        "paymentRail": "usdc_usdt",
        "checkoutError": "Paddle/card checkout removed. Use POST /v1/billing/crypto/checkout-session",
        "cryptoCheckout": "/v1/billing/crypto/checkout-session",
        "billingUi": "https://narna.org/billing",
    }


def get_billing_mode() -> str:
    return os.environ.get("UAP_BILLING_MODE", "mock").lower()


def _plan_price_cents(plan: str) -> int:
    """USD cents for Cloud plans."""
    return plan_price_cents(plan)


# enforce_plan_limit + bump_adqa_usage imported from .quota


@app.post("/v1/ingest", response_model=IngestResponse)
def ingest(
    body: IngestRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> IngestResponse:
    projected_gu = count_governance_units(body.events)
    enforce_plan_limit(org=org, projected_events=len(body.events), projected_gu=projected_gu)

    run = (
        db.query(Run)
        .filter(Run.org_id == org.id, Run.run_id == body.runId)
        .first()
    )
    if run is None:
        run = Run(
            org_id=org.id,
            run_id=body.runId,
            agent_id=body.agentId,
            agent_name=body.agentName,
        )
        db.add(run)
        db.flush()
    else:
        run.agent_id = body.agentId
        run.agent_name = body.agentName

    run.state = body.state
    run.tip_hash = body.tipHash
    session_id = body.sessionId
    if not session_id:
        for evt in body.events:
            if evt.get("sessionId"):
                session_id = str(evt["sessionId"])
                break
    if session_id:
        run.session_id = session_id
    run.total_gu = int(run.total_gu or 0) + projected_gu
    if body.trustScore:
        run.trust_score = body.trustScore.get("score")
    if body.proofBundle:
        run.proof_bundle_json = json.dumps(body.proofBundle)
    run.updated_at = datetime.now(timezone.utc)

    # Upsert governance session + graph nodes from EU events
    if session_id:
        sess = (
            db.query(GovernanceSessionRow)
            .filter(
                GovernanceSessionRow.org_id == org.id,
                GovernanceSessionRow.session_id == session_id,
            )
            .first()
        )
        if sess is None:
            sess = GovernanceSessionRow(
                org_id=org.id,
                session_id=session_id,
                logical_agent_id=body.agentId,
            )
            db.add(sess)
        graph = json.loads(sess.graph_json or "{}")
        nodes = {n["unitId"]: n for n in graph.get("nodes", []) if n.get("unitId")}
        for evt in body.events:
            if evt.get("eventType") == "ExecutionUnitStarted":
                eu = (evt.get("payload") or {}).get("executionUnit") or {}
                uid = eu.get("unitId") or evt.get("executionUnitId")
                if uid:
                    nodes[uid] = {
                        "unitId": uid,
                        "unitKind": eu.get("unitKind") or "tool",
                        "logicalAgentId": eu.get("logicalAgentId") or body.agentId,
                        "parentUnitId": eu.get("parentUnitId") or evt.get("parentExecutionUnitId"),
                        "guCost": int(eu.get("guCost") or 1),
                        "label": eu.get("label") or eu.get("toolName"),
                        "runId": body.runId,
                    }
            if evt.get("eventType") in {"SessionCompleted", "BudgetExceeded", "LoopDetected"}:
                sess.state = "terminated" if evt.get("eventType") != "SessionCompleted" else "closed"
                sess.closed_at = datetime.now(timezone.utc)
                reason = (evt.get("payload") or {}).get("reason")
                if reason:
                    sess.terminate_reason = str(reason)
        sess.graph_json = json.dumps({"nodes": list(nodes.values())})
        sess.total_gu = int(sess.total_gu or 0) + projected_gu

    existing_ids = {
        e.event_id for e in db.query(RunEvent).filter(RunEvent.run_pk == run.id).all()
    }
    ingested = 0
    for evt in body.events:
        eid = evt.get("eventId", "")
        if not eid or eid in existing_ids:
            continue
        db.add(
            RunEvent(
                run_pk=run.id,
                event_id=eid,
                event_type=str(evt.get("eventType", "")),
                sequence=int(evt.get("sequence", 0)),
                ts=str(evt.get("ts", "")),
                payload_json=json.dumps(evt.get("payload", {})),
                event_hash=str(evt.get("eventHash", "")),
            )
        )
        existing_ids.add(eid)
        ingested += 1

    org.events_in_period = int(org.events_in_period) + ingested
    org.gu_in_period = int(org.gu_in_period) + projected_gu
    METRICS.inc_ingest()
    METRICS.inc_ingest_accepted()
    db.commit()

    if bool(getattr(org, "telemetry_opt_in", 0)) and ingested > 0:
        try:
            from uap.telemetry import build_contribution_from_events, strip_forbidden

            contribution = build_contribution_from_events(
                events=body.events,
                org_id=org.id,
                agent_id=body.agentId,
                agent_name=body.agentName,
                trust_score=(body.trustScore or {}).get("score") if body.trustScore else None,
                telemetry_opt_in=True,
                train_opt_in=bool(getattr(org, "train_opt_in", 0)),
            )
            contribution = strip_forbidden(contribution)
            spec = contribution.get("spec") if isinstance(contribution, dict) else {}
            if isinstance(spec, dict) and spec.get("tenantHash"):
                nodes = spec.get("nodes") if isinstance(spec.get("nodes"), list) else []
                edges = spec.get("edges") if isinstance(spec.get("edges"), list) else []
                totals = spec.get("totals") if isinstance(spec.get("totals"), dict) else {}
                db.add(
                    TelemetryContribution(
                        org_id=org.id,
                        tenant_hash=str(spec.get("tenantHash")),
                        session_hash=spec.get("sessionHash"),
                        train_opt_in=1 if bool(getattr(org, "train_opt_in", 0)) else 0,
                        nodes_json=json.dumps(strip_forbidden(nodes)),
                        edges_json=json.dumps(strip_forbidden(edges)),
                        totals_json=json.dumps(totals),
                        node_count=len(nodes),
                        gu_total=int(totals.get("gu") or projected_gu),
                    )
                )
                db.commit()
        except Exception as e:
            logger.debug("telemetry auto-contribute skipped: %s", e)

    return IngestResponse(
        runId=body.runId,
        eventsIngested=ingested,
        guIngested=projected_gu,
        sessionId=session_id,
        url=f"/console/runs/{body.runId}",
    )


@app.get("/v1/runs", response_model=list[RunSummary])
def list_runs(
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
    limit: int = 50,
) -> list[RunSummary]:
    runs = (
        db.query(Run)
        .filter(Run.org_id == org.id)
        .order_by(Run.updated_at.desc())
        .limit(limit)
        .all()
    )
    out: list[RunSummary] = []
    for r in runs:
        count = db.query(RunEvent).filter(RunEvent.run_pk == r.id).count()
        out.append(
            RunSummary(
                runId=r.run_id,
                agentId=r.agent_id,
                agentName=r.agent_name,
                state=r.state,
                tipHash=r.tip_hash,
                trustScore=r.trust_score,
                eventCount=count,
                updatedAt=r.updated_at.isoformat() if r.updated_at else "",
                sessionId=r.session_id,
                totalGu=int(r.total_gu or 0),
            )
        )
    return out


@app.get("/v1/sessions", response_model=list[SessionSummary])
def list_sessions(
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
    limit: int = 50,
) -> list[SessionSummary]:
    rows = (
        db.query(GovernanceSessionRow)
        .filter(GovernanceSessionRow.org_id == org.id)
        .order_by(GovernanceSessionRow.created_at.desc())
        .limit(limit)
        .all()
    )
    out: list[SessionSummary] = []
    for s in rows:
        run_count = db.query(Run).filter(Run.org_id == org.id, Run.session_id == s.session_id).count()
        out.append(
            SessionSummary(
                sessionId=s.session_id,
                logicalAgentId=s.logical_agent_id,
                state=s.state,
                totalGu=int(s.total_gu or 0),
                runCount=run_count,
                createdAt=s.created_at.isoformat() if s.created_at else "",
                closedAt=s.closed_at.isoformat() if s.closed_at else None,
                terminateReason=s.terminate_reason,
            )
        )
    return out


@app.get("/v1/sessions/{session_id}", response_model=SessionDetail)
def get_session(
    session_id: str,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> SessionDetail:
    s = (
        db.query(GovernanceSessionRow)
        .filter(
            GovernanceSessionRow.org_id == org.id,
            GovernanceSessionRow.session_id == session_id,
        )
        .first()
    )
    if s is None:
        raise HTTPException(status_code=404, detail="session not found")
    runs_db = (
        db.query(Run)
        .filter(Run.org_id == org.id, Run.session_id == session_id)
        .order_by(Run.updated_at.desc())
        .all()
    )
    runs: list[RunSummary] = []
    for r in runs_db:
        count = db.query(RunEvent).filter(RunEvent.run_pk == r.id).count()
        runs.append(
            RunSummary(
                runId=r.run_id,
                agentId=r.agent_id,
                agentName=r.agent_name,
                state=r.state,
                tipHash=r.tip_hash,
                trustScore=r.trust_score,
                eventCount=count,
                updatedAt=r.updated_at.isoformat() if r.updated_at else "",
                sessionId=r.session_id,
                totalGu=int(r.total_gu or 0),
            )
        )
    graph = json.loads(s.graph_json or "{}")
    return SessionDetail(
        sessionId=s.session_id,
        logicalAgentId=s.logical_agent_id,
        state=s.state,
        totalGu=int(s.total_gu or 0),
        runCount=len(runs),
        createdAt=s.created_at.isoformat() if s.created_at else "",
        closedAt=s.closed_at.isoformat() if s.closed_at else None,
        terminateReason=s.terminate_reason,
        graph=graph,
        runs=runs,
        units=list(graph.get("nodes") or []),
    )


@app.get("/v1/runs/{run_id}", response_model=RunDetail)
def get_run(
    run_id: str,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> RunDetail:
    run = (
        db.query(Run)
        .filter(Run.org_id == org.id, Run.run_id == run_id)
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    events_db = (
        db.query(RunEvent)
        .filter(RunEvent.run_pk == run.id)
        .order_by(RunEvent.sequence.asc())
        .all()
    )
    events: list[dict[str, Any]] = []
    for e in events_db:
        events.append(
            {
                "eventId": e.event_id,
                "eventType": e.event_type,
                "sequence": e.sequence,
                "ts": e.ts,
                "payload": json.loads(e.payload_json),
                "eventHash": e.event_hash,
            }
        )

    proof = json.loads(run.proof_bundle_json) if run.proof_bundle_json else None
    return RunDetail(
        runId=run.run_id,
        agentId=run.agent_id,
        agentName=run.agent_name,
        state=run.state,
        tipHash=run.tip_hash,
        trustScore=run.trust_score,
        eventCount=len(events),
        updatedAt=run.updated_at.isoformat() if run.updated_at else "",
        sessionId=run.session_id,
        totalGu=int(run.total_gu or 0),
        events=events,
        proofBundle=proof,
    )


@app.get("/v1/metrics")
def metrics(org: Organization = Depends(get_org_from_api_key)) -> dict[str, Any]:
    limit = plan_event_limit(org.plan)
    return {
        "plan": normalize_plan(org.plan),
        "periodStartAt": org.period_start_at.isoformat()
        if org.period_start_at
        else "",
        "eventsInPeriod": org.events_in_period,
        "eventsLimit": limit,
        "guInPeriod": org.gu_in_period,
        "guLimit": plan_gu_limit(org.plan),
        "adqaChecksInPeriod": int(getattr(org, "adqa_checks_in_period", 0) or 0),
        "adqaSoftCap": plan_adqa_soft_cap(org.plan),
        "adqaHardCap": plan_adqa_hard_cap(org.plan),
        "seatCount": int(getattr(org, "seat_count", 1) or 1),
        "seatDefault": plan_seats(org.plan),
        "metrics": METRICS.__dict__,
        "slo": METRICS.to_slo(),
    }


@app.post("/v1/billing/mock/set-plan", response_model=BillingCheckoutResponse)
def mock_set_plan(
    body: BillingMockSetPlanRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> BillingCheckoutResponse:
    if not _mock_plan_allowed():
        raise HTTPException(
            status_code=403,
            detail=(
                "mock set-plan disabled in production. "
                "Pay with USDC/USDT via /v1/billing/crypto/checkout-session"
            ),
        )
    org.plan = normalize_plan(body.plan)
    now = now_utc()
    org.period_start_at = now
    org.plan_expires_at = add_plan_period(now) if org.plan != "free" else None
    org.events_in_period = 0
    org.gu_in_period = 0
    org.adqa_checks_in_period = 0
    if org.plan == "team" and int(getattr(org, "seat_count", 1) or 1) < 3:
        org.seat_count = 3
    db.commit()
    return BillingCheckoutResponse(ok=True, url="mock://plan-changed", mode="mock")


@app.get("/v1/billing/status", response_model=BillingStatusResponse)
def billing_status(
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> BillingStatusResponse:
    from .quota import reset_period_if_needed

    reset_period_if_needed(org)
    db.add(org)
    db.commit()
    db.refresh(org)
    expires = getattr(org, "plan_expires_at", None)
    return BillingStatusResponse(
        plan=normalize_plan(org.plan),
        periodStartAt=org.period_start_at.isoformat() if org.period_start_at else "",
        eventsInPeriod=int(org.events_in_period),
        eventsLimit=plan_event_limit(org.plan),
        guInPeriod=int(org.gu_in_period),
        guLimit=plan_gu_limit(org.plan),
        billingMode=get_billing_mode(),
        cryptoMode=get_crypto_mode(),
        mockPlanAllowed=_mock_plan_allowed(),
        planExpiresAt=expires.isoformat() if expires else None,
        adqaChecksInPeriod=int(getattr(org, "adqa_checks_in_period", 0) or 0),
        adqaSoftCap=plan_adqa_soft_cap(org.plan),
        adqaHardCap=plan_adqa_hard_cap(org.plan),
        agentTurnsInPeriod=int(getattr(org, "agent_turns_in_period", 0) or 0),
        agentTurnsHardCap=plan_agent_turns_hard_cap(org.plan),
        seatCount=int(getattr(org, "seat_count", 1) or 1),
        byoLlmAllowed=plan_allows_byo_llm(org.plan),
    )


@app.post("/v1/billing/checkout-session", response_model=BillingCheckoutResponse)
def checkout_session(
    body: BillingCheckoutRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> BillingCheckoutResponse:
    """Card / Stripe / Paddle checkout disabled — pay with USDC/USDT only."""
    # Dev-only instant plan flip (blocked when live crypto)
    if _mock_plan_allowed() and get_billing_mode() == "mock":
        org.plan = normalize_plan(body.plan)
        now = now_utc()
        org.period_start_at = now
        org.plan_expires_at = add_plan_period(now) if org.plan != "free" else None
        org.events_in_period = 0
        org.gu_in_period = 0
        org.adqa_checks_in_period = 0
        db.commit()
        return BillingCheckoutResponse(
            ok=True, url="mock://checkout/success", mode="mock"
        )

    raise HTTPException(
        status_code=410,
        detail=(
            "Card / Stripe / Paddle checkout removed. "
            "Pay with USDC or USDT via POST /v1/billing/crypto/checkout-session "
            "(networks: ethereum, polygon, base, arbitrum, bsc)."
        ),
    )


def get_crypto_mode() -> str:
    return os.environ.get("UAP_CRYPTO_MODE", "mock").lower()


def _mock_plan_allowed() -> bool:
    """Allow free plan flips only in local/demo — never when live crypto is on."""
    flag = os.environ.get("UAP_ALLOW_MOCK_PLAN", "").lower()
    if flag in {"1", "true", "yes"}:
        return True
    if flag in {"0", "false", "no"}:
        return False
    return get_crypto_mode() != "live"


def get_crypto_receiver_wallet() -> str:
    return os.environ.get(
        "UAP_CRYPTO_RECEIVER_WALLET",
        "0x24DAb37fd89222710ce1D5A4c4E81e26D51E34D5",
    )


def _invoice_response(inv: PaymentInvoice) -> BillingInvoiceResponse:
    return BillingInvoiceResponse(
        invoiceId=inv.invoice_id,
        kind=inv.kind,
        plan=inv.plan,
        asset=inv.asset,
        network=inv.network,
        recipientWallet=inv.recipient_wallet,
        expectedAmount=inv.expected_amount,
        status=inv.status,
        txHash=inv.tx_hash,
        createdAt=inv.created_at.isoformat() if inv.created_at else "",
        expiresAt=inv.expires_at.isoformat() if inv.expires_at else None,
        paidAt=inv.paid_at.isoformat() if inv.paid_at else None,
        seatCount=int(getattr(inv, "seat_count", 1) or 1),
    )


def _checkout_crypto_response(
    *,
    invoice: PaymentInvoice,
    mode: str,
    url: str,
    qr_payload: str,
) -> BillingCryptoCheckoutResponse:
    return BillingCryptoCheckoutResponse(
        ok=True,
        url=url,
        mode=mode,
        invoiceId=invoice.invoice_id,
        plan=invoice.plan,
        asset=invoice.asset,
        network=invoice.network,
        recipientWallet=invoice.recipient_wallet,
        expectedAmount=invoice.expected_amount,
        expiresAt=invoice.expires_at.isoformat() if invoice.expires_at else "",
        qrPayload=qr_payload,
        seatCount=int(getattr(invoice, "seat_count", 1) or 1),
    )


@app.post("/v1/billing/crypto/checkout-session", response_model=BillingCryptoCheckoutResponse)
def crypto_checkout_session(
    body: BillingCryptoCheckoutRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> BillingCryptoCheckoutResponse:
    mode = get_crypto_mode()

    asset = str(body.asset).lower()
    network = str(body.network).lower()
    try:
        _chain, token = validate_crypto_payment(network=network, asset=asset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    plan = normalize_plan(body.plan)
    base_usd, seat_count = checkout_usd_amount(plan, seats=body.seats)
    if base_usd <= 0:
        raise HTTPException(status_code=400, detail="plan is not payable by crypto")
    receiver_wallet = get_crypto_receiver_wallet()

    import hashlib

    invoice_src = (
        f"{org.id}:{plan}:{seat_count}:{asset}:{network}:"
        f"{datetime.now(timezone.utc).timestamp()}"
    )
    invoice_id = "inv_" + hashlib.sha256(invoice_src.encode()).hexdigest()[:16]
    expires = invoice_expires_at()
    amount_str = allocate_unique_amount(
        db, network=network, asset=asset, base_usd=base_usd
    )
    qr_payload = build_qr_payload(
        recipient_wallet=receiver_wallet,
        expected_amount=amount_str,
        asset=asset,
        network=network,
        invoice_id=invoice_id,
    )

    invoice = PaymentInvoice(
        org_id=org.id,
        invoice_id=invoice_id,
        kind="crypto",
        plan=plan,
        seat_count=seat_count,
        asset=asset,
        network=network,
        recipient_wallet=receiver_wallet,
        expected_amount=amount_str,
        status="pending",
        expires_at=expires,
    )
    db.add(invoice)

    mock_pending = os.environ.get("UAP_CRYPTO_MOCK_PENDING", "0").lower() in {"1", "true", "yes"}

    if mode == "mock" and not mock_pending:
        # In mock mode we simulate an on-chain payment: switch plan immediately.
        now = now_utc()
        org.plan = plan
        org.period_start_at = now
        org.plan_expires_at = add_plan_period(now)
        org.seat_count = seat_count
        org.events_in_period = 0
        org.gu_in_period = 0
        org.adqa_checks_in_period = 0
        invoice.status = "paid"
        invoice.tx_hash = "0xmock"
        invoice.paid_at = now
        db.commit()
        return _checkout_crypto_response(
            invoice=invoice,
            mode="mock",
            url=f"mock://crypto/{asset}/{invoice_id}",
            qr_payload=qr_payload,
        )

    if mode == "mock" and mock_pending:
        db.commit()
        return _checkout_crypto_response(
            invoice=invoice,
            mode="mock-pending",
            url=f"mock://crypto/pending/{invoice_id}",
            qr_payload=qr_payload,
        )

    if mode != "live":
        raise HTTPException(status_code=503, detail="crypto mode not configured")

    db.commit()
    pay_url = build_pay_uri(
        network=network,
        receiver_wallet=receiver_wallet,
        token=token,
        asset=asset,
        amount=amount_str,
        invoice_id=invoice_id,
    )
    return _checkout_crypto_response(
        invoice=invoice,
        mode="live",
        url=pay_url,
        qr_payload=qr_payload,
    )


@app.get("/v1/billing/crypto/networks", response_model=list[BillingCryptoNetworkResponse])
def crypto_networks() -> list[BillingCryptoNetworkResponse]:
    return [BillingCryptoNetworkResponse(**n) for n in list_supported_networks()]


@app.get("/v1/billing/crypto/invoices", response_model=list[BillingInvoiceResponse])
def list_crypto_invoices(
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
    limit: int = 20,
) -> list[BillingInvoiceResponse]:
    expire_pending_invoices(db)
    db.commit()
    rows = (
        db.query(PaymentInvoice)
        .filter(PaymentInvoice.org_id == org.id, PaymentInvoice.kind == "crypto")
        .order_by(PaymentInvoice.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_invoice_response(r) for r in rows]


@app.post("/v1/billing/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    raise HTTPException(
        status_code=410,
        detail="Stripe billing removed. Pay with USDC/USDT via /v1/billing/crypto/checkout-session",
    )


def _registry_summary(row: RegistryAgent, request: Request | None = None) -> RegistryAgentSummary:
    caps = json.loads(row.capabilities_json or "[]")
    base = ""
    if request is not None:
        base = str(request.base_url).rstrip("/")
    verified = bool(getattr(row, "verified", 0))
    cert = None
    if getattr(row, "certification_json", None):
        try:
            cert = json.loads(row.certification_json)
        except Exception:
            cert = None
    badge = None
    level = None
    level_label = None
    if isinstance(cert, dict):
        badge = cert.get("badge")
        level = cert.get("level")
        level_label = cert.get("levelLabel")
    if verified and not badge:
        badge = "NARNA Certified"
    return RegistryAgentSummary(
        agentId=row.agent_id,
        name=row.name,
        version=row.version,
        creator=row.creator,
        category=row.category,
        capabilities=caps if isinstance(caps, list) else [],
        trustScore=row.trust_score,
        stars=int(row.stars or 0),
        downloads=int(row.downloads or 0),
        executions=int(row.executions or 0),
        publishedAt=row.published_at.isoformat() if row.published_at else "",
        passportUrl=f"{base}/v1/passport/{row.agent_id}" if base else f"/v1/passport/{row.agent_id}",
        verified=verified,
        badge=badge,
        level=level,
        levelLabel=level_label,
    )


@app.post("/v1/registry/publish", response_model=RegistryPublishResponse)
def registry_publish(
    body: RegistryPublishRequest,
    request: Request,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> RegistryPublishResponse:
    row = db.query(RegistryAgent).filter(RegistryAgent.agent_id == body.agentId).first()
    if row is None:
        row = RegistryAgent(agent_id=body.agentId, org_id=org.id)
        db.add(row)
    row.name = body.name
    row.version = body.version
    row.creator = body.creator
    row.category = body.category or "general"
    row.capabilities_json = json.dumps(body.capabilities or [])
    if body.trustScore is not None:
        row.trust_score = body.trustScore
    row.stars = max(int(row.stars or 0), int(body.stars or 0))
    row.downloads = max(int(row.downloads or 0), int(body.downloads or 0))
    row.executions = max(int(row.executions or 0), int(body.executions or 0))
    row.passport_json = json.dumps(body.passport) if body.passport else row.passport_json
    row.identity_json = json.dumps(body.identity) if body.identity else row.identity_json
    row.org_id = org.id
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    base = str(request.base_url).rstrip("/")
    return RegistryPublishResponse(
        agentId=row.agent_id,
        passportUrl=f"{base}/v1/passport/{row.agent_id}",
        registryUrl=f"{base}/v1/registry/agents/{row.agent_id}",
        status="published",
    )


@app.get("/v1/registry/agents", response_model=list[RegistryAgentSummary])
def registry_list(
    request: Request,
    db: Session = Depends(get_db),
    capability: str | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = 50,
) -> list[RegistryAgentSummary]:
    rows = db.query(RegistryAgent).order_by(RegistryAgent.updated_at.desc()).limit(200).all()
    out: list[RegistryAgentSummary] = []
    for row in rows:
        caps = json.loads(row.capabilities_json or "[]")
        if capability and capability.lower() not in [str(c).lower() for c in caps]:
            continue
        if category and category.lower() != str(row.category or "").lower():
            continue
        if q:
            needle = q.lower()
            hay = f"{row.name} {row.agent_id} {row.creator}".lower()
            if needle not in hay:
                continue
        out.append(_registry_summary(row, request))
        if len(out) >= limit:
            break
    return out


@app.get("/v1/registry/trending", response_model=list[RegistryAgentSummary])
def registry_trending(
    request: Request,
    db: Session = Depends(get_db),
    category: str | None = None,
    limit: int = 20,
) -> list[RegistryAgentSummary]:
    rows = db.query(RegistryAgent).all()
    if category:
        rows = [r for r in rows if str(r.category or "").lower() == category.lower()]
    rows.sort(
        key=lambda r: (
            float(r.trust_score or 0),
            int(r.stars or 0),
            int(r.downloads or 0),
            int(r.executions or 0),
        ),
        reverse=True,
    )
    return [_registry_summary(r, request) for r in rows[:limit]]


@app.get("/v1/registry/agents/{agent_id}", response_model=RegistryAgentSummary)
def registry_get(
    agent_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RegistryAgentSummary:
    row = db.query(RegistryAgent).filter(RegistryAgent.agent_id == agent_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found in registry")
    return _registry_summary(row, request)


@app.post("/v1/registry/agents/{agent_id}/star")
def registry_star(agent_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.query(RegistryAgent).filter(RegistryAgent.agent_id == agent_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found")
    row.stars = int(row.stars or 0) + 1
    db.commit()
    return {"ok": True, "agentId": agent_id, "stars": row.stars}


@app.get("/v1/passport/{agent_id}")
def public_passport(agent_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.query(RegistryAgent).filter(RegistryAgent.agent_id == agent_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="passport not found")
    passport = json.loads(row.passport_json) if row.passport_json else None
    cert = json.loads(row.certification_json) if getattr(row, "certification_json", None) else None
    verified = bool(getattr(row, "verified", 0))
    badge = None
    level = None
    level_label = None
    if isinstance(cert, dict):
        badge = cert.get("badge")
        level = cert.get("level")
        level_label = cert.get("levelLabel")
    if verified and not badge:
        badge = "NARNA Certified"
    return {
        "agentId": row.agent_id,
        "name": row.name,
        "version": row.version,
        "creator": row.creator,
        "category": row.category,
        "capabilities": json.loads(row.capabilities_json or "[]"),
        "trustScore": row.trust_score,
        "stars": row.stars,
        "downloads": row.downloads,
        "executions": row.executions,
        "publishedAt": row.published_at.isoformat() if row.published_at else "",
        "passport": passport,
        "verified": verified,
        "badge": badge,
        "level": level,
        "levelLabel": level_label,
        "certification": cert,
    }


@app.get("/v1/passport/{agent_id}/verify")
def public_passport_verify(agent_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Public passport verification — no API key required."""
    row = db.query(RegistryAgent).filter(RegistryAgent.agent_id == agent_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="passport not found")
    passport = json.loads(row.passport_json) if row.passport_json else None
    if not isinstance(passport, dict):
        return {
            "agentId": agent_id,
            "verified": False,
            "signatureValid": False,
            "problems": ["passport document missing"],
            "passportUrl": f"/v1/passport/{agent_id}",
            "publicPage": f"/passport/{agent_id}",
        }
    try:
        from uap.passport_sign import verify_passport_signature

        ok, problems = verify_passport_signature(passport)
    except Exception as e:
        ok, problems = False, [str(e)]
    base = os.environ.get("NARNA_PUBLIC_URL", "https://narna.org").rstrip("/")
    return {
        "agentId": agent_id,
        "name": row.name,
        "verified": bool(getattr(row, "verified", 0)) and ok,
        "signatureValid": ok,
        "trustScore": row.trust_score,
        "problems": problems,
        "passportId": passport.get("passportId"),
        "passportUrl": f"{base}/passport/{agent_id}",
        "apiUrl": f"/v1/passport/{agent_id}",
    }

def certification_submit(
    body: CertificationSubmitRequest,
    request: Request,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> CertificationSubmitResponse:
    """Accept certification result and stamp Registry with level badge."""
    level = (body.level or "").upper()
    if level not in {"L1", "L2", "L3"} and body.status != "passed":
        raise HTTPException(
            status_code=400,
            detail="submit requires achieved level L1/L2/L3 or status=passed",
        )
    if level not in {"L1", "L2", "L3"} and body.status == "passed":
        level = (body.targetLevel or "L2").upper()
        if level not in {"L1", "L2", "L3"}:
            level = "L2"

    badges = {
        "L1": "NARNA Certified",
        "L2": "NARNA Certified+",
        "L3": "Enterprise Ready",
    }
    labels = {
        "L1": "Level 1",
        "L2": "Level 2",
        "L3": "Enterprise Ready",
    }
    badge = body.badge or badges.get(level, "NARNA Certified")
    level_label = body.levelLabel or labels.get(level)

    row = db.query(RegistryAgent).filter(RegistryAgent.agent_id == body.agentId).first()
    if row is None:
        row = RegistryAgent(agent_id=body.agentId, org_id=org.id, name=body.agentId)
        db.add(row)
    cert_payload = {
        "certificationId": body.certificationId,
        "agentId": body.agentId,
        "status": body.status,
        "level": level,
        "targetLevel": body.targetLevel,
        "badge": badge,
        "levelLabel": level_label,
        "algorithm": body.algorithm,
        "issuedAt": body.issuedAt,
        "expiresAt": body.expiresAt,
        "trustScore": body.trustScore,
        "checks": body.checks,
        "runId": body.runId,
        "proofHash": body.proofHash,
        "passportHash": body.passportHash,
        "constitutionId": body.constitutionId,
        "constitutionHash": body.constitutionHash,
        "orgId": org.id,
    }
    row.certification_json = json.dumps(cert_payload)
    row.verified = 1
    if body.trustScore is not None:
        row.trust_score = body.trustScore
    row.org_id = org.id
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    base = str(request.base_url).rstrip("/")
    return CertificationSubmitResponse(
        agentId=row.agent_id,
        verified=True,
        badge=badge,
        level=level,
        levelLabel=level_label,
        passportUrl=f"{base}/v1/passport/{row.agent_id}",
        status="verified",
    )


@app.post("/v1/playground/validate")
def playground_validate(body: dict[str, Any]) -> dict[str, Any]:
    """Validate narna.yaml manifest and preview constitution + score dimensions."""
    import yaml

    raw = body.get("manifest")
    if not raw or not isinstance(raw, str):
        raise HTTPException(status_code=400, detail="manifest string required")
    try:
        from uap.manifest import compile_manifest_to_constitution
        from uap.schemas import validator_for

        doc = yaml.safe_load(raw)
        if not isinstance(doc, dict):
            raise ValueError("manifest must be a YAML mapping")
        if doc.get("kind") != "Manifest":
            doc = {
                **doc,
                "apiVersion": doc.get("apiVersion", "narna.ai/v1alpha1"),
                "kind": "Manifest",
            }
        validator_for("manifest.schema.json").validate(doc)
        constitution = compile_manifest_to_constitution(doc)
        caps = len(doc.get("capabilities") or [])
        gov = 1.0 if doc.get("governance") or doc.get("constitution") else 0.4
        breakdown = {
            "identity": 0.5,
            "capability": min(1.0, 0.4 + 0.1 * caps),
            "evidence": 0.3,
            "governance": gov,
            "compliance": 0.2,
            "operational": 0.3,
        }
        score_0_1 = sum(breakdown.values()) / len(breakdown)
        return {
            "ok": True,
            "constitutionPreview": {
                "constitutionId": constitution.get("metadata", {}).get("id"),
                "entityId": constitution.get("metadata", {}).get("entityId"),
                "supports": constitution.get("spec", {}).get("capability", {}).get("supports", []),
                "rules": len(constitution.get("spec", {}).get("policy", {}).get("rules") or []),
            },
            "narnaScore": int(round(score_0_1 * 100)),
            "breakdown": breakdown,
            "algorithm": "narna-score-v0-preview",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/v1/score/{agent_id}")
def narna_score_for_agent(agent_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Derive NARNA Score from registry passport + certification metadata."""
    row = db.query(RegistryAgent).filter(RegistryAgent.agent_id == agent_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="agent not found")
    passport = json.loads(row.passport_json or "{}")
    cert = json.loads(row.certification_json or "{}") if row.certification_json else {}
    trust = passport.get("trust", {})
    breakdown = {
        "identity": 1.0 if passport.get("identity") else 0.0,
        "capability": min(1.0, 0.5 + 0.05 * len(passport.get("capability", {}).get("declared") or [])),
        "evidence": float(trust.get("score") or 0.5),
        "governance": 1.0 if passport.get("governance") else 0.3,
        "compliance": {"L3": 1.0, "L2": 0.85, "L1": 0.65}.get(str(cert.get("level") or ""), 0.2),
        "operational": min(1.0, (passport.get("history", {}).get("successCount") or 0) / max(1, passport.get("history", {}).get("runCount") or 1)),
    }
    score_0_1 = sum(breakdown.values()) / len(breakdown)
    return {
        "agentId": agent_id,
        "narnaScore": int(round(score_0_1 * 100)),
        "breakdown": breakdown,
        "algorithm": "narna-score-v0-registry",
        "passportUrl": f"/v1/passport/{agent_id}",
    }


@app.post("/v1/passport/verify")
def passport_verify(body: dict[str, Any]) -> dict[str, Any]:
    """Verify signed Agent Passport offline (Ed25519)."""
    passport = body.get("passport")
    if not isinstance(passport, dict):
        raise HTTPException(status_code=400, detail="passport object required")
    try:
        from uap.passport_sign import verify_passport_signature

        ok, problems = verify_passport_signature(passport)
        return {
            "verified": ok,
            "passportId": passport.get("passportId"),
            "problems": problems,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/policy/evaluate")
def policy_evaluate(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0004 / NGS-0013 — evaluate a permission request (cloud stub + SDK PolicyEngine)."""
    permission = str(body.get("permission") or "").strip()
    if not permission:
        raise HTTPException(status_code=400, detail="permission required")
    parameters = body.get("parameters") if isinstance(body.get("parameters"), dict) else {}
    policy_ref = str(body.get("policyRef") or "local-default@0.0.0")
    agent_id = str(body.get("agentId") or "anonymous")
    try:
        from pathlib import Path

        from uap.policy import PolicyEngine

        engine = PolicyEngine(Path.cwd())
        decision = engine.evaluate(
            policy_ref=policy_ref,
            agent_permissions=body.get("grants") if isinstance(body.get("grants"), list) else [],
            permission=permission,
            parameters=parameters,
            agent_id=agent_id,
            run_id=str(body.get("runId") or "api"),
        )
        return {"ok": True, "decision": decision, "standard": "NGS-0004"}
    except Exception as e:
        # Deny-safe fallback if SDK unavailable in container
        return {
            "ok": True,
            "decision": {
                "decision": "deny",
                "permission": permission,
                "reasons": [f"policy evaluate fallback: {e}"],
                "policyRef": policy_ref,
            },
            "standard": "NGS-0004",
        }


@app.post("/v1/decision/evaluate")
def decision_evaluate(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0014 — Decision OS evaluate (risk + reasons + approvals + evidence)."""
    action = str(body.get("action") or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="action required")
    question = body.get("question")
    provider = str(body.get("provider") or body.get("decisionPackage") or "legal-decision")
    version = body.get("version")
    path = body.get("path")
    evidence = body.get("evidencePresent") or body.get("evidence") or []
    if isinstance(evidence, str):
        evidence = [x.strip() for x in evidence.split(",") if x.strip()]
    if not isinstance(evidence, list):
        evidence = []
    try:
        from pathlib import Path

        from uap.decision import DecisionEngine

        engine = DecisionEngine(Path.cwd())
        result = engine.evaluate(
            action=action,
            question=str(question) if question else None,
            provider=provider,
            version=str(version) if version else None,
            path=path,
            context=body.get("context") if isinstance(body.get("context"), dict) else None,
            session_id=str(body.get("sessionId") or "") or None,
            evidence_present=[str(x) for x in evidence],
        )
        return {"ok": True, "result": result, "standard": "NGS-0014"}
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "result": {
                "decision": "deny",
                "action": action,
                "reasons": [f"decision evaluate fallback: {e}"],
                "riskScore": 1.0,
                "riskBand": "critical",
                "evaluatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
            "standard": "NGS-0014",
        }


@app.post("/v1/adqa/check")
def adqa_check(
    body: dict[str, Any],
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """NGS-0024 — Autonomous Decision Quality Assurance (DQS + Decision Guardian).

    Cloud SaaS: send Authorization: Bearer uap_live_… for tenant Decision Memory + metering.
    Anonymous allowed when UAP_ADQA_REQUIRE_AUTH!=1 (demo); free hard-capped via soft public budget.
    """
    require = os.environ.get("UAP_ADQA_REQUIRE_AUTH", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if require and org is None:
        raise HTTPException(status_code=401, detail="API key required for ADQA Cloud")
    action = str(body.get("action") or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="action required")
    evidence = body.get("evidencePresent") or body.get("evidence") or []
    if isinstance(evidence, str):
        evidence = [x.strip() for x in evidence.split(",") if x.strip()]
    if not isinstance(evidence, list):
        evidence = []

    from uap.adqa import ADQAEngine

    warn = None
    ws = tenant_workspace(org.id) if org is not None else tenant_workspace(tenant_id="anon")
    if org is not None:
        warn = enforce_plan_limit(org=org, projected_events=0, projected_gu=0, projected_adqa=1)

    out = ADQAEngine(ws).check_proposed(
        action=action,
        provider=str(body.get("provider") or body.get("decisionPackage") or "legal-decision"),
        evidence_present=[str(x) for x in evidence],
        context=body.get("context") if isinstance(body.get("context"), dict) else None,
        agent_id=str(body.get("agentId") or "") or None,
        question=str(body.get("question") or "") or None,
    )
    if org is not None:
        bump_adqa_usage(org=org, db=db)
        out["tenantId"] = tenant_id_for_org(org.id)
        out["plan"] = normalize_plan(org.plan)
    if warn:
        out["quota"] = warn
    return {"ok": True, **out}


@app.post("/v1/adqa/evaluate")
def adqa_evaluate(
    body: dict[str, Any],
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Universal ADQA evaluate — wrap any agent decision (Hermes/LangGraph/custom).

    Returns DQS + Guardian + ACT/REVIEW/REJECT verdict.
    """
    from narna.evaluate import evaluate as narna_evaluate

    require = os.environ.get("UAP_ADQA_REQUIRE_AUTH", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if require and org is None:
        raise HTTPException(status_code=401, detail="API key required for ADQA Cloud")
    action = str(body.get("action") or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="action required")
    ws = tenant_workspace(org.id) if org is not None else tenant_workspace(tenant_id="anon")
    warn = None
    if org is not None:
        warn = enforce_plan_limit(org=org, projected_events=0, projected_gu=0, projected_adqa=1)
    try:
        out = narna_evaluate(
            action=action,
            evidence=body.get("evidence") or body.get("evidencePresent"),
            context=body.get("context") if isinstance(body.get("context"), dict) else None,
            question=body.get("question"),
            workspace=ws,
            agent_id=str(body.get("agentId") or "") or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if org is not None:
        bump_adqa_usage(org=org, db=db)
        out["tenantId"] = tenant_id_for_org(org.id)
        out["plan"] = normalize_plan(org.plan)
    if warn:
        out["quota"] = warn
    return out


@app.get("/v1/decision/traces")
def decision_traces_list(
    request: Request,
    limit: int = 20,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List recent Decision Traces (NGS-0030)."""
    from uap.decision_trace import DecisionTraceStore

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    ws = tenant_workspace(resolved.id)
    rows = DecisionTraceStore(ws, tenant_id=tenant_id_for_org(resolved.id)).list_traces(
        limit=limit
    )
    return {"ok": True, "traces": rows, "count": len(rows), "standard": "NGS-0030-trace"}


@app.get("/v1/decision/traces/{trace_id}")
def decision_trace_get(
    trace_id: str,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.decision_trace import DecisionTraceStore

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    ws = tenant_workspace(resolved.id)
    row = DecisionTraceStore(ws, tenant_id=tenant_id_for_org(resolved.id)).get(trace_id)
    if not row:
        raise HTTPException(status_code=404, detail="trace not found")
    return {"ok": True, "trace": row}


@app.post("/v1/decision/replay")
def decision_replay(
    body: dict[str, Any],
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Replay a Decision Trace with today's knowledge."""
    from uap.narna_agent import NarnaAgent

    trace_id = str(body.get("traceId") or body.get("trace_id") or "").strip()
    if not trace_id:
        raise HTTPException(status_code=400, detail="traceId required")
    resolved = _resolve_ask_org(request=request, org=org, db=db)
    warn = enforce_plan_limit(org=resolved, projected_agent_turns=1)
    agent = NarnaAgent(
        workspace=tenant_workspace(resolved.id),
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    try:
        out = agent.replay(
            trace_id,
            extra_context=str(body.get("extraContext") or body.get("extra_context") or "")
            or None,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    bump_agent_turns(org=resolved, db=db)
    out["plan"] = normalize_plan(resolved.plan)
    if warn:
        out["quota"] = warn
    return out


def _anon_org_name(request: Request) -> str:
    import hashlib

    ip = (request.client.host if request.client else "0.0.0.0") or "0.0.0.0"
    device = (request.headers.get("x-narna-device") or "").strip()
    raw = f"{ip}:{device}"
    return "anon_" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _resolve_ask_org(
    *,
    request: Request,
    org: Organization | None,
    db: Session,
) -> Organization:
    if org is not None:
        return org
    name = _anon_org_name(request)
    row = db.query(Organization).filter(Organization.name == name).first()
    if row is None:
        row = Organization(name=name, plan="free")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _router_for_org(org: Organization, *, override: dict[str, Any] | None = None):
    import json as _json

    from uap.model_router import ModelRouter

    cfg: dict[str, Any] = {}
    raw = getattr(org, "llm_config_json", None)
    if raw and plan_allows_byo_llm(org.plan):
        try:
            cfg = _json.loads(raw)
        except Exception:
            cfg = {}
    # Per-request BYOK wins (Hermes: user key, not hosted LLM)
    if override:
        if override.get("apiKey"):
            cfg["apiKey"] = override["apiKey"]
        if override.get("provider"):
            cfg["provider"] = override["provider"]
        if override.get("baseUrl"):
            cfg["baseUrl"] = override["baseUrl"]
        if override.get("modelReason"):
            cfg["modelReason"] = override["modelReason"]
            cfg["modelCheap"] = override.get("modelCheap") or override["modelReason"]
            cfg["modelChallenge"] = override.get("modelChallenge") or override["modelReason"]

    provider = str(cfg.get("provider") or "").lower()
    api_key = str(cfg.get("apiKey") or "").strip()
    # No hosted OpenRouter fallback — mock unless user brought a key
    if not provider:
        provider = "openrouter" if api_key else "mock"
    if provider in {"openrouter", "openai"} and not api_key:
        provider = "mock"
    models = {}
    if cfg.get("modelCheap"):
        models["cheap"] = str(cfg["modelCheap"])
    if cfg.get("modelReason"):
        models["reason"] = str(cfg["modelReason"])
    if cfg.get("modelChallenge"):
        models["challenge"] = str(cfg["modelChallenge"])
    return ModelRouter(
        provider=provider,
        api_key=api_key or None,
        base_url=str(cfg.get("baseUrl") or "") or None,
        models=models or None,
    )


@app.post("/v1/router/complete")
def router_complete(
    body: RouterCompleteRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """NGS-0028 — Model Router chat completion."""
    resolved = _resolve_ask_org(request=request, org=org, db=db)
    enforce_plan_limit(org=resolved, projected_agent_turns=1)
    router = _router_for_org(resolved)
    try:
        result = router.complete(
            messages=body.messages,
            task=body.task,
            temperature=body.temperature,
            max_tokens=body.maxTokens,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    bump_agent_turns(org=resolved, db=db)
    out = result.to_dict()
    out["plan"] = normalize_plan(resolved.plan)
    return out


@app.post("/v1/agent/ask")
def agent_ask(
    body: AgentAskRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """NGS-0029 — Ask NARNA (Memory → Reason → ADQA → Answer)."""
    from uap.narna_agent import NarnaAgent

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    warn = enforce_plan_limit(org=resolved, projected_agent_turns=1)
    # Paid/team may enable challenge; free can opt-in but still billed as 1 turn
    challenge = bool(body.challenge) and normalize_plan(resolved.plan) != "free"
    if body.challenge and normalize_plan(resolved.plan) == "free":
        # Allow challenge on free for product demo but still one turn; soft note
        challenge = True

    override = None
    if body.llmApiKey or body.llmProvider or body.llmBaseUrl or body.llmModel:
        override = {
            "apiKey": body.llmApiKey,
            "provider": body.llmProvider or "openrouter",
            "baseUrl": body.llmBaseUrl,
            "modelReason": body.llmModel,
        }

    ws = tenant_workspace(resolved.id)
    agent = NarnaAgent(
        workspace=ws,
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved, override=override),
    )
    try:
        out = agent.ask(
            body.message,
            session_id=body.sessionId,
            files=body.files,
            challenge=challenge,
            channel="web",
            use_tools=True,
            mode=str(body.mode or "cheap"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    bump_agent_turns(org=resolved, db=db)
    out["plan"] = normalize_plan(resolved.plan)
    out["agentTurnsInPeriod"] = int(getattr(resolved, "agent_turns_in_period", 0) or 0)
    out["agentTurnsHardCap"] = plan_agent_turns_hard_cap(resolved.plan)
    if warn:
        out["quota"] = warn
    # Hide model ids for free UX unless power header set
    if request.headers.get("x-narna-show-models", "").lower() not in {"1", "true", "yes"}:
        if normalize_plan(resolved.plan) == "free":
            out["modelsUsed"] = []
    return out


@app.get("/v1/agent/skills")
def agent_skills_list(
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.agent_skills import SkillStore

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    ws = tenant_workspace(resolved.id)
    skills = SkillStore(ws).list_skills()
    return {"ok": True, "skills": skills, "count": len(skills), "standard": "NGS-0029-skills"}


@app.get("/v1/agent/skills/hub")
def agent_skill_hub_list(
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.skill_hub import SkillHub

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    skills = SkillHub(tenant_workspace(resolved.id)).list_public()
    return {"ok": True, "skills": skills, "count": len(skills), "standard": "NGS-0029-skill-hub"}


@app.post("/v1/agent/skills/hub")
def agent_skill_hub_publish(
    body: AgentSkillHubPublishRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.skill_hub import SkillHub

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    try:
        row = SkillHub(tenant_workspace(resolved.id)).publish(
            name=body.name,
            body=body.body,
            tags=body.tags,
            author=body.author or resolved.name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "skill": row}


@app.post("/v1/agent/skills/hub/install")
def agent_skill_hub_install(
    body: AgentSkillHubInstallRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.agent_skills import SkillStore
    from uap.skill_hub import SkillHub

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    ws = tenant_workspace(resolved.id)
    try:
        installed = SkillHub(ws).install_to_store(body.skillId, skills=SkillStore(ws))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"ok": True, "installed": installed}


@app.post("/v1/agent/skills/hub/sync")
def agent_skill_hub_sync(
    request: Request,
    body: AgentSkillHubSyncRequest | None = None,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Pull public skill index from URL (UAP_SKILL_HUB_INDEX_URL or body.url). Not Nous."""
    from uap.skill_hub import SkillHub

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    url = (body.url if body else None) or None
    out = SkillHub(tenant_workspace(resolved.id)).sync_from_url(url)
    if not out.get("ok"):
        raise HTTPException(status_code=400, detail=str(out.get("error") or "sync failed"))
    return out


@app.get("/v1/agent/skills/hub/export.zip")
def agent_skill_hub_export_zip(
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
):
    """Download SKILL.md zip bundle from the tenant hub."""
    from pathlib import Path as _Path

    from fastapi.responses import Response
    from uap.skill_hub import SkillHub

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    hub = SkillHub(tenant_workspace(resolved.id))
    result = hub.export_zip()
    data = _Path(str(result["path"])).read_bytes()
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="narna-skills-hub.zip"'},
    )


@app.get("/v1/agent/skills/{skill_id}/markdown")
def agent_skill_export_markdown(
    skill_id: str,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Export skill as agentskills.io SKILL.md (Hermes interop)."""
    from uap.agent_skills import SkillStore
    from uap.skill_md import skill_to_markdown

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    skill = SkillStore(tenant_workspace(resolved.id)).get(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="skill not found")
    return {"ok": True, "skillId": skill_id, "markdown": skill_to_markdown(skill)}


@app.post("/v1/agent/skills/import-markdown")
def agent_skill_import_markdown(
    body: AgentSkillMarkdownImportRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Import agentskills.io SKILL.md into tenant skill store."""
    from uap.agent_skills import SkillStore
    from uap.skill_md import markdown_to_skill

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    parsed = markdown_to_skill(body.markdown)
    row = SkillStore(tenant_workspace(resolved.id)).save(
        name=str(parsed.get("name") or "imported"),
        body=str(parsed.get("body") or ""),
        tags=list(parsed.get("tags") or []),
    )
    return {"ok": True, "skill": row, "standard": "agentskills.io"}


@app.get("/v1/agent/sessions/{session_id}")
def agent_session_get(
    session_id: str,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.agent_session import AgentSessionStore

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    ws = tenant_workspace(resolved.id)
    row = AgentSessionStore(ws).get(session_id)
    if not row:
        raise HTTPException(status_code=404, detail="session not found")
    return {"ok": True, "session": row, "standard": "NGS-0029"}


def _org_for_device_key(db: Session, device_key: str) -> Organization:
    import hashlib

    name = "anon_" + hashlib.sha256(device_key.encode()).hexdigest()[:16]
    row = db.query(Organization).filter(Organization.name == name).first()
    if row is None:
        row = Organization(name=name, plan="free")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@app.get("/v1/agent/gateway/status")
def agent_gateway_status() -> dict[str, Any]:
    """Gateway health + pairing posture (no side effects)."""
    from pathlib import Path

    from uap.gateway_pairing import GatewayPairingStore, pairing_enabled
    from uap.gateway_runner import UnifiedGateway, config_from_env
    from uap.agent_tools import TOOL_SPECS

    cfg = config_from_env()
    root = Path(os.environ.get("UAP_TENANT_ROOT") or "/data/tenants") / "_gateway"
    gw = UnifiedGateway(ask_fn=lambda *_: {}, config=cfg, workspace=root)
    return {
        "ok": True,
        **gw.status(),
        "pairing": GatewayPairingStore(root).status(),
        "pairingEnabled": pairing_enabled(),
        "toolCount": len(TOOL_SPECS),
        "standard": "NGS-0029-gateway",
    }


@app.post("/v1/agent/telegram/webhook")
async def agent_telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Phone channel: Telegram → Ask NARNA (set webhook to this URL)."""
    from uap.narna_agent import NarnaAgent
    from uap.telegram_gateway import (
        extract_telegram_text,
        format_agent_reply,
        send_telegram_message,
        telegram_enabled,
    )

    if not telegram_enabled():
        raise HTTPException(status_code=503, detail="Telegram bot not configured")

    secret = os.environ.get("UAP_TELEGRAM_WEBHOOK_SECRET", "").strip()
    if secret:
        got = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if got != secret:
            raise HTTPException(status_code=403, detail="invalid webhook secret")

    try:
        update = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid JSON") from e

    chat_id, text, _username = extract_telegram_text(update if isinstance(update, dict) else {})
    if not chat_id or not text:
        return {"ok": True, "ignored": True}

    from uap.gateway_pairing import gate_inbound
    from pathlib import Path

    # Pairing gate uses a shared workspace root (not per-tenant) for bot-level allowlist
    pair_ws = Path(os.environ.get("UAP_TENANT_ROOT") or "/data/tenants") / "_gateway"
    blocked = gate_inbound(
        channel="telegram",
        external_id=str(chat_id),
        text=text,
        workspace=pair_ws,
    )
    if blocked:
        try:
            send_telegram_message(chat_id, str(blocked.get("answer") or "pairing required"))
        except Exception:
            pass
        return {"ok": True, "pairing": True, "paired": blocked.get("paired")}

    resolved = _org_for_device_key(db, f"telegram:{chat_id}")
    try:
        enforce_plan_limit(org=resolved, projected_agent_turns=1)
    except HTTPException as e:
        if e.status_code == 402:
            try:
                send_telegram_message(
                    chat_id,
                    "Free Ask quota reached. Upgrade with USDC/USDT at https://narna.org/billing",
                )
            except Exception:
                pass
            return {"ok": True, "quota": True}
        raise

    ws = tenant_workspace(resolved.id)
    agent = NarnaAgent(
        workspace=ws,
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    try:
        out = agent.ask(
            text,
            channel="telegram",
            external_id=str(chat_id),
            use_tools=True,
        )
    except Exception as e:
        try:
            send_telegram_message(chat_id, f"NARNA error: {e}")
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=str(e)) from e

    bump_agent_turns(org=resolved, db=db)
    try:
        send_telegram_message(chat_id, format_agent_reply(out))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"telegram send failed: {e}") from e
    return {"ok": True, "decisionId": out.get("decisionId"), "sessionId": out.get("sessionId")}


@app.post("/v1/agent/discord/webhook")
async def agent_discord_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Discord message webhook / interaction relay → Ask NARNA."""
    from uap.discord_gateway import (
        discord_enabled,
        extract_discord_message,
        format_agent_reply,
        send_discord_message,
    )
    from uap.narna_agent import NarnaAgent

    if not discord_enabled():
        raise HTTPException(status_code=503, detail="Discord bot not configured")

    secret = os.environ.get("UAP_DISCORD_WEBHOOK_SECRET", "").strip()
    if secret:
        got = request.headers.get("X-Narna-Discord-Secret", "")
        if got != secret:
            raise HTTPException(status_code=403, detail="invalid discord secret")

    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid JSON") from e

    # Discord Interactions URL verification (PING type=1)
    if isinstance(payload, dict) and payload.get("type") == 1:
        return {"type": 1}

    channel_id, text, author_id = extract_discord_message(
        payload if isinstance(payload, dict) else {}
    )
    if not channel_id or not text:
        return {"ok": True, "ignored": True}

    resolved = _org_for_device_key(db, f"discord:{author_id or channel_id}")
    try:
        enforce_plan_limit(org=resolved, projected_agent_turns=1)
    except HTTPException as e:
        if e.status_code == 402:
            try:
                send_discord_message(
                    channel_id,
                    "Free Ask quota reached. Upgrade with USDC/USDT at https://narna.org/billing",
                )
            except Exception:
                pass
            return {"ok": True, "quota": True}
        raise

    ws = tenant_workspace(resolved.id)
    agent = NarnaAgent(
        workspace=ws,
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    try:
        out = agent.ask(
            text,
            channel="discord",
            external_id=str(channel_id),
            use_tools=True,
        )
    except Exception as e:
        try:
            send_discord_message(channel_id, f"NARNA error: {e}")
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=str(e)) from e

    bump_agent_turns(org=resolved, db=db)
    try:
        send_discord_message(channel_id, format_agent_reply(out))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"discord send failed: {e}") from e
    return {"ok": True, "decisionId": out.get("decisionId"), "sessionId": out.get("sessionId")}


@app.post("/v1/agent/slack/events")
async def agent_slack_events(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.narna_agent import NarnaAgent
    from uap.slack_gateway import (
        extract_slack_event,
        format_agent_reply,
        send_slack_message,
        slack_enabled,
    )

    if not slack_enabled():
        raise HTTPException(status_code=503, detail="Slack bot not configured")

    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid JSON") from e

    if isinstance(payload, dict) and payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    channel, text, user = extract_slack_event(payload if isinstance(payload, dict) else {})
    if not channel or not text:
        return {"ok": True, "ignored": True}

    resolved = _org_for_device_key(db, f"slack:{user or channel}")
    try:
        enforce_plan_limit(org=resolved, projected_agent_turns=1)
    except HTTPException as e:
        if e.status_code == 402:
            try:
                send_slack_message(channel, "Free Ask quota reached — https://narna.org/billing")
            except Exception:
                pass
            return {"ok": True, "quota": True}
        raise

    agent = NarnaAgent(
        workspace=tenant_workspace(resolved.id),
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    try:
        out = agent.ask(text, channel="slack", external_id=str(channel), use_tools=True)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    bump_agent_turns(org=resolved, db=db)
    send_slack_message(channel, format_agent_reply(out))
    return {"ok": True, "decisionId": out.get("decisionId")}


@app.post("/v1/agent/whatsapp/webhook")
async def agent_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Twilio WhatsApp webhook (form-urlencoded)."""
    from uap.narna_agent import NarnaAgent
    from uap.whatsapp_gateway import (
        extract_whatsapp_form,
        format_agent_reply,
        send_whatsapp_message,
        whatsapp_enabled,
    )

    if not whatsapp_enabled():
        raise HTTPException(status_code=503, detail="WhatsApp/Twilio not configured")

    form = dict(await request.form())
    frm, text = extract_whatsapp_form(form)
    if not frm or not text:
        return {"ok": True, "ignored": True}

    resolved = _org_for_device_key(db, f"whatsapp:{frm}")
    try:
        enforce_plan_limit(org=resolved, projected_agent_turns=1)
    except HTTPException as e:
        if e.status_code == 402:
            try:
                send_whatsapp_message(frm, "Free Ask quota reached — narna.org/billing")
            except Exception:
                pass
            return {"ok": True, "quota": True}
        raise

    agent = NarnaAgent(
        workspace=tenant_workspace(resolved.id),
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    try:
        out = agent.ask(text, channel="whatsapp", external_id=frm, use_tools=True)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    bump_agent_turns(org=resolved, db=db)
    send_whatsapp_message(frm, format_agent_reply(out))
    return {"ok": True, "decisionId": out.get("decisionId")}


@app.post("/v1/agent/signal/webhook")
async def agent_signal_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.narna_agent import NarnaAgent
    from uap.signal_gateway import extract_signal_message, format_agent_reply, signal_enabled

    if not signal_enabled():
        raise HTTPException(status_code=503, detail="Signal bridge not configured (UAP_SIGNAL_WEBHOOK_URL)")

    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="invalid JSON") from e
    sender, text = extract_signal_message(payload if isinstance(payload, dict) else {})
    if not sender or not text:
        return {"ok": True, "ignored": True}

    resolved = _org_for_device_key(db, f"signal:{sender}")
    enforce_plan_limit(org=resolved, projected_agent_turns=1)
    agent = NarnaAgent(
        workspace=tenant_workspace(resolved.id),
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    out = agent.ask(text, channel="signal", external_id=sender, use_tools=True)
    bump_agent_turns(org=resolved, db=db)
    # Outbound: POST to bridge URL
    import urllib.request as _ur

    bridge = os.environ.get("UAP_SIGNAL_WEBHOOK_URL", "").strip()
    body = json.dumps({"to": sender, "message": format_agent_reply(out)}).encode()
    req = _ur.Request(
        bridge,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        _ur.urlopen(req, timeout=20).read()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"signal outbound failed: {e}") from e
    return {"ok": True, "decisionId": out.get("decisionId")}


@app.post("/v1/agent/email/webhook")
async def agent_email_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.email_gateway import extract_email_message, format_agent_reply
    from uap.narna_agent import NarnaAgent

    ctype = (request.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        payload = await request.json()
        form = payload if isinstance(payload, dict) else {}
    else:
        form = dict(await request.form())
    frm, subject, text = extract_email_message(form)
    if not frm or not text:
        return {"ok": True, "ignored": True}
    msg = f"Subject: {subject}\n\n{text}" if subject else text
    resolved = _org_for_device_key(db, f"email:{frm}")
    enforce_plan_limit(org=resolved, projected_agent_turns=1)
    agent = NarnaAgent(
        workspace=tenant_workspace(resolved.id),
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    out = agent.ask(msg, channel="email", external_id=frm, use_tools=True)
    bump_agent_turns(org=resolved, db=db)
    return {
        "ok": True,
        "decisionId": out.get("decisionId"),
        "reply": format_agent_reply(out, subject=subject or ""),
    }


@app.get("/v1/agent/tools")
def agent_tools_catalog() -> dict[str, Any]:
    from uap.agent_tools import TOOL_SPECS

    return {"ok": True, "tools": TOOL_SPECS, "count": len(TOOL_SPECS), "standard": "NGS-0029"}


@app.post("/v1/agent/ask/stream")
def agent_ask_stream(
    body: AgentAskRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
):
    """SSE progress events then final Ask result (mobile-friendly)."""
    import json as _json

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    warn = enforce_plan_limit(org=resolved, projected_agent_turns=1)
    challenge = bool(body.challenge)
    ws = tenant_workspace(resolved.id)
    override = None
    if body.llmApiKey or body.llmProvider or body.llmBaseUrl or body.llmModel:
        override = {
            "apiKey": body.llmApiKey,
            "provider": body.llmProvider or "openrouter",
            "baseUrl": body.llmBaseUrl,
            "modelReason": body.llmModel,
        }

    def gen():
        yield f"event: status\ndata: {_json.dumps({'phase': 'start'})}\n\n"
        from uap.narna_agent import NarnaAgent

        agent = NarnaAgent(
            workspace=ws,
            tenant_id=tenant_id_for_org(resolved.id),
            router=_router_for_org(resolved, override=override),
        )
        yield f"event: status\ndata: {_json.dumps({'phase': 'reason'})}\n\n"
        try:
            out = agent.ask(
                body.message,
                session_id=body.sessionId,
                files=body.files,
                challenge=challenge,
                channel="web",
                use_tools=True,
                mode=str(body.mode or "cheap"),
            )
        except Exception as e:
            yield f"event: error\ndata: {_json.dumps({'error': str(e)})}\n\n"
            return
        bump_agent_turns(org=resolved, db=db)
        out["plan"] = normalize_plan(resolved.plan)
        out["agentTurnsInPeriod"] = int(getattr(resolved, "agent_turns_in_period", 0) or 0)
        out["agentTurnsHardCap"] = plan_agent_turns_hard_cap(resolved.plan)
        if warn:
            out["quota"] = warn
        if request.headers.get("x-narna-show-models", "").lower() not in {"1", "true", "yes"}:
            if normalize_plan(resolved.plan) == "free":
                out["modelsUsed"] = []
        yield f"event: result\ndata: {_json.dumps(out)}\n\n"
        yield f"event: done\ndata: {_json.dumps({'ok': True})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/v1/agent/jobs")
def agent_jobs_list(
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.agent_jobs import AgentJobStore

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    jobs = AgentJobStore(tenant_workspace(resolved.id)).list_jobs()
    return {"ok": True, "jobs": jobs, "count": len(jobs)}


@app.post("/v1/agent/jobs")
def agent_jobs_create(
    body: AgentJobCreateRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.agent_jobs import AgentJobStore

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    every = body.everyMinutes
    run_at = body.runAt
    prompt = body.prompt
    channel = body.channel or "job"
    deliver_to = body.deliverTo
    if body.schedule:
        from uap.nl_cron import parse_nl_schedule

        try:
            parsed = parse_nl_schedule(
                body.schedule if not body.prompt else f"{body.schedule} {body.prompt}"
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        every = parsed.get("everyMinutes") if every is None else every
        run_at = parsed.get("runAt") if not run_at else run_at
        prompt = str(parsed.get("prompt") or prompt)
        channel = str(parsed.get("channel") or channel)
        deliver_to = parsed.get("deliverTo") or deliver_to
    if normalize_plan(resolved.plan) == "free" and every:
        raise HTTPException(
            status_code=403,
            detail="Recurring jobs require Personal or Team — upgrade at /billing",
        )
    try:
        row = AgentJobStore(tenant_workspace(resolved.id)).create(
            prompt=prompt,
            every_minutes=every,
            run_at=run_at,
            channel=channel,
            deliver_to=deliver_to,
            enabled=body.enabled,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "job": row}


@app.post("/v1/agent/jobs/tick")
def agent_jobs_tick(
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Run due jobs (call from cron / health worker)."""
    from uap.narna_agent import NarnaAgent

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    agent = NarnaAgent(
        workspace=tenant_workspace(resolved.id),
        tenant_id=tenant_id_for_org(resolved.id),
        router=_router_for_org(resolved),
    )
    due = agent.jobs.due_jobs()
    if not due:
        return {"ok": True, "ran": [], "count": 0}
    enforce_plan_limit(org=resolved, projected_agent_turns=min(len(due), 5))
    ran = agent.run_due_jobs(limit=5)
    bump_agent_turns(org=resolved, db=db, n=len(ran))
    return {
        "ok": True,
        "count": len(ran),
        "ran": [
            {
                "jobId": r["jobId"],
                "decisionId": (r.get("ask") or {}).get("decisionId"),
                "dqs": (r.get("ask") or {}).get("dqs"),
            }
            for r in ran
        ],
    }


@app.post("/v1/agent/outcome")
def agent_outcome(
    body: AgentOutcomeRequest,
    request: Request,
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    from uap.narna_agent import NarnaAgent

    resolved = _resolve_ask_org(request=request, org=org, db=db)
    ws = tenant_workspace(resolved.id)
    agent = NarnaAgent(workspace=ws, tenant_id=tenant_id_for_org(resolved.id))
    try:
        row = agent.record_outcome(
            body.decisionId,
            status=body.status,
            detail=body.detail or "",
            success_score=body.successScore,
            lesson=body.lesson,
            skill_id=body.skillId,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"ok": True, "record": row, "standard": "NGS-0029"}


@app.get("/v1/agent/models")
def agent_models_get(
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    import json as _json

    raw = getattr(org, "llm_config_json", None)
    cfg: dict[str, Any] = {}
    if raw:
        try:
            cfg = _json.loads(raw)
        except Exception:
            cfg = {}
    key = str(cfg.get("apiKey") or "")
    redacted = (key[:4] + "…" + key[-4:]) if len(key) > 8 else ("set" if key else None)
    return {
        "ok": True,
        "byoLlmAllowed": plan_allows_byo_llm(org.plan),
        "provider": cfg.get("provider") or os.environ.get("UAP_ROUTER_PROVIDER") or "mock",
        "baseUrl": cfg.get("baseUrl"),
        "apiKeySet": bool(key),
        "apiKeyPreview": redacted,
        "modelCheap": cfg.get("modelCheap"),
        "modelReason": cfg.get("modelReason"),
        "modelChallenge": cfg.get("modelChallenge"),
        "plan": normalize_plan(org.plan),
    }


@app.put("/v1/agent/models")
def agent_models_put(
    body: AgentModelsPutRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    import json as _json

    if not plan_allows_byo_llm(org.plan):
        raise HTTPException(
            status_code=403,
            detail="BYO LLM not allowed on this plan",
        )
    provider = str(body.provider or "openrouter").lower()
    if provider not in {"openrouter", "openai", "ollama", "mock"}:
        raise HTTPException(status_code=400, detail="unsupported provider")
    existing: dict[str, Any] = {}
    if org.llm_config_json:
        try:
            existing = _json.loads(org.llm_config_json)
        except Exception:
            existing = {}
    cfg = {
        "provider": provider,
        "apiKey": body.apiKey if body.apiKey is not None else existing.get("apiKey"),
        "baseUrl": body.baseUrl if body.baseUrl is not None else existing.get("baseUrl"),
        "modelCheap": body.modelCheap or existing.get("modelCheap"),
        "modelReason": body.modelReason or existing.get("modelReason"),
        "modelChallenge": body.modelChallenge or existing.get("modelChallenge"),
    }
    org.llm_config_json = _json.dumps(cfg)
    db.add(org)
    db.commit()
    return {"ok": True, "provider": provider, "byoLlmAllowed": True}


@app.get("/v1/integrations")
def list_integrations() -> dict[str, Any]:
    """Hot AI stacks + CMEM bridge catalog (Borrow the Wave)."""
    from narna.integrations import integration_manifest

    return integration_manifest()


@app.get("/v1/cmem/status")
def cmem_status() -> dict[str, Any]:
    from pathlib import Path

    from uap.cmem_bridge import CmemBridge

    return CmemBridge(Path.cwd()).status()


@app.post("/v1/cmem/enrich")
def cmem_enrich(body: dict[str, Any]) -> dict[str, Any]:
    action = str(body.get("action") or body.get("query") or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="action required")
    from pathlib import Path

    from uap.cmem_bridge import CmemBridge

    ctx = CmemBridge(Path.cwd()).enrich_context(
        action,
        body.get("context") if isinstance(body.get("context"), dict) else None,
        limit=int(body.get("limit") or 8),
    )
    return {"ok": True, "context": ctx, "cmem": ctx.get("_cmem")}


@app.post("/v1/cmem/ingest")
def cmem_ingest_local(body: dict[str, Any]) -> dict[str, Any]:
    """Offline observation stub for demos (not a CMEM Cloud write)."""
    from pathlib import Path

    from uap.cmem_bridge import CmemBridge

    return CmemBridge(Path.cwd()).ingest_local(body if isinstance(body, dict) else {})


@app.get("/v1/mcp/tools")
def mcp_tools_list() -> dict[str, Any]:
    from narna.mcp_tools import NarnaMcpTools

    return {"ok": True, "tools": NarnaMcpTools(tenant_workspace(tenant_id="local")).list_tools()}


@app.post("/v1/mcp/call")
def mcp_tools_call(
    body: dict[str, Any],
    org: Organization | None = Depends(get_org_optional),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    name = str(body.get("name") or body.get("tool") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    from narna.mcp_tools import NarnaMcpTools

    ws = tenant_workspace(org.id) if org is not None else tenant_workspace(tenant_id="anon")
    args = body.get("arguments") if isinstance(body.get("arguments"), dict) else body
    if name == "narna_adqa_check" and org is not None:
        enforce_plan_limit(org=org, projected_events=0, projected_gu=0, projected_adqa=1)
        bump_adqa_usage(org=org, db=db)
    return NarnaMcpTools(ws).call_tool(name, args)


@app.post("/v1/adqa/score")
def adqa_score(body: dict[str, Any]) -> dict[str, Any]:
    """Score an existing DecisionResult without re-running packages."""
    result = body.get("decisionResult") or body.get("result")
    if not isinstance(result, dict):
        raise HTTPException(status_code=400, detail="decisionResult required")
    from uap.adqa import ADQAEngine

    evidence = body.get("evidencePresent") or []
    if isinstance(evidence, str):
        evidence = [x.strip() for x in evidence.split(",") if x.strip()]
    return {
        "ok": True,
        "adqa": ADQAEngine(tenant_workspace(tenant_id="local")).score(
            result,
            evidence_present=[str(x) for x in evidence],
            agent_id=str(body.get("agentId") or "") or None,
            capability=str(body.get("capability") or result.get("action") or "") or None,
        ),
    }


@app.post("/v1/dmemory/record")
def dmemory_record(
    body: dict[str, Any],
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.decision_memory import DecisionMemory

    action = str(body.get("action") or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="action required")
    tid = tenant_id_for_org(org.id)
    return DecisionMemory(tenant_workspace(org.id)).record(
        action=action,
        context=body.get("context") if isinstance(body.get("context"), dict) else None,
        reasoning=body.get("reasoning") if isinstance(body.get("reasoning"), list) else None,
        guardian=str(body.get("guardian") or "") or None,
        dqs=int(body["dqs"]) if body.get("dqs") is not None else None,
        confidence=float(body["confidence"]) if body.get("confidence") is not None else None,
        provider=str(body.get("provider") or "") or None,
        decision=str(body.get("decision") or "") or None,
        adqa=body.get("adqa") if isinstance(body.get("adqa"), dict) else None,
        tenant_id=tid,
    )


@app.post("/v1/dmemory/{decision_id}/outcome")
def dmemory_outcome(
    decision_id: str,
    body: dict[str, Any],
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.outcome_learning import OutcomeLearningEngine

    status = str(body.get("status") or "").strip()
    if not status:
        raise HTTPException(status_code=400, detail="status required")
    try:
        return OutcomeLearningEngine(tenant_workspace(org.id)).evaluate(
            decision_id,
            status=status,
            detail=str(body.get("detail") or "") or None,
            success_score=float(body["successScore"]) if body.get("successScore") is not None else None,
            lesson=str(body.get("lesson") or "") or None,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/v1/dmemory/query")
def dmemory_query(
    action: str | None = None,
    customer: str | None = None,
    limit: int = 20,
    with_outcome: bool = False,
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.decision_memory import DecisionMemory

    tid = tenant_id_for_org(org.id)
    return {
        "ok": True,
        "tenantId": tid,
        "records": DecisionMemory(tenant_workspace(org.id)).query(
            action=action,
            customer=customer,
            tenant_id=tid,
            limit=limit,
            with_outcome_only=with_outcome,
        ),
    }


@app.get("/v1/dmemory/lessons")
def dmemory_lessons(
    action: str | None = None,
    limit: int = 5,
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.decision_memory import DecisionMemory

    tid = tenant_id_for_org(org.id)
    return {
        "ok": True,
        "tenantId": tid,
        "lessons": DecisionMemory(tenant_workspace(org.id)).lessons_for(
            action=action, limit=limit
        ),
    }


@app.post("/v1/learning/evaluate")
def learning_evaluate(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.outcome_learning import OutcomeLearningEngine

    did = str(body.get("decisionId") or "").strip()
    status = str(body.get("status") or "").strip()
    if not did or not status:
        raise HTTPException(status_code=400, detail="decisionId and status required")
    try:
        return OutcomeLearningEngine(Path.cwd()).evaluate(
            did,
            status=status,
            detail=str(body.get("detail") or "") or None,
            success_score=float(body["successScore"]) if body.get("successScore") is not None else None,
            lesson=str(body.get("lesson") or "") or None,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/v1/learning/prior/{action}")
def learning_prior(action: str) -> dict[str, Any]:
    from pathlib import Path

    from uap.outcome_learning import OutcomeLearningEngine

    prior = OutcomeLearningEngine(Path.cwd()).prior_for(action)
    return {"ok": True, "action": action, "prior": prior}


@app.get("/v1/dqs/status")
def dqs_network_status(
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.dqs_network import DqsNetwork

    return DqsNetwork(tenant_workspace(org.id)).status()


@app.post("/v1/dqs/opt-in")
def dqs_network_opt_in(
    body: dict[str, Any],
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.dqs_network import DqsNetwork

    enabled = bool(body.get("enabled") if body.get("enabled") is not None else body.get("optIn", True))
    return DqsNetwork(tenant_workspace(org.id)).set_opt_in(enabled)


@app.post("/v1/dqs/export")
def dqs_network_export(
    body: dict[str, Any] | None = None,
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.dqs_network import DqsNetwork

    body = body or {}
    return DqsNetwork(tenant_workspace(org.id)).export_digest(
        org_id=org.id,
        min_count=int(body.get("minCount") or 3),
    )


@app.post("/v1/dqs/import")
def dqs_network_import(
    body: dict[str, Any],
    org: Organization = Depends(get_org_from_api_key),
) -> dict[str, Any]:
    from uap.dqs_network import DqsNetwork

    digest = body.get("digest") if isinstance(body.get("digest"), dict) else body
    return DqsNetwork(tenant_workspace(org.id)).import_digest(digest)


@app.get("/v1/connect/catalog")
def connect_catalog() -> dict[str, Any]:
    from pathlib import Path

    from uap.connect import ConnectRegistry

    return ConnectRegistry(Path.cwd()).catalog()


@app.post("/v1/connect/register")
def connect_register(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.connect import ConnectRegistry

    return {
        "ok": True,
        "connector": ConnectRegistry(Path.cwd()).register(
            type=str(body.get("type") or "api"),
            name=str(body.get("name") or "unnamed"),
            endpoint=str(body.get("endpoint") or "") or None,
            config=body.get("config") if isinstance(body.get("config"), dict) else None,
        ),
    }


@app.post("/v1/connect/probe/{connector_id}")
def connect_probe(connector_id: str) -> dict[str, Any]:
    from pathlib import Path

    from uap.connect import ConnectRegistry

    try:
        return {"ok": True, **ConnectRegistry(Path.cwd()).probe(connector_id)}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/v1/knowledge/entities")
def knowledge_upsert(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.knowledge import KnowledgeGraph

    return {
        "ok": True,
        "entity": KnowledgeGraph(Path.cwd()).upsert_entity(
            kind=str(body.get("kind") or "entity"),
            name=str(body.get("name") or ""),
            props=body.get("props") if isinstance(body.get("props"), dict) else None,
            entity_id=str(body.get("entityId") or "") or None,
        ),
    }


@app.get("/v1/knowledge/entities")
def knowledge_query(
    kind: str | None = None, q: str | None = None, limit: int = 50
) -> dict[str, Any]:
    from pathlib import Path

    from uap.knowledge import KnowledgeGraph

    return {
        "ok": True,
        "entities": KnowledgeGraph(Path.cwd()).query(kind=kind, name_contains=q, limit=limit),
    }


@app.post("/v1/knowledge/relations")
def knowledge_relate(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.knowledge import KnowledgeGraph

    try:
        return {
            "ok": True,
            "relation": KnowledgeGraph(Path.cwd()).relate(
                from_id=str(body.get("from") or ""),
                to_id=str(body.get("to") or ""),
                rel_type=str(body.get("type") or "related"),
            ),
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/memory/{scope}/{scope_id}")
def memory_put(scope: str, scope_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.durable_memory import DurableMemory

    records = body.get("records") if isinstance(body.get("records"), dict) else body
    if "_meta" in records:
        records = {k: v for k, v in records.items() if k != "_meta"}
    return {
        "ok": True,
        **DurableMemory(Path.cwd()).put(scope=scope, scope_id=scope_id, records=records),
    }


@app.get("/v1/memory/{scope}/{scope_id}")
def memory_get(scope: str, scope_id: str) -> dict[str, Any]:
    from pathlib import Path

    from uap.durable_memory import DurableMemory

    return {"ok": True, **DurableMemory(Path.cwd()).get(scope=scope, scope_id=scope_id)}


@app.post("/v1/automate/run")
def automate_run(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.automation import AutomationEngine

    trigger = str(body.get("trigger") or "").strip()
    action = str(body.get("action") or "").strip()
    if not trigger or not action:
        raise HTTPException(status_code=400, detail="trigger and action required")
    return AutomationEngine(Path.cwd()).run(
        trigger=trigger,
        action=action,
        provider=str(body.get("provider") or "legal-decision"),
        path=body.get("path"),
        context=body.get("context") if isinstance(body.get("context"), dict) else None,
    )


@app.get("/v1/dmarket/packages")
def dmarket_list(industry: str | None = None, all_packages: bool = False) -> dict[str, Any]:
    from pathlib import Path

    from uap.decision_market import DecisionMarketplace

    return {
        "ok": True,
        "packages": DecisionMarketplace(Path.cwd()).list_packages(
            industry=industry,
            decisions_only=not all_packages,
        ),
    }


@app.post("/v1/dmarket/install")
def dmarket_install(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.decision_market import DecisionMarketplace

    provider = str(body.get("provider") or "").strip()
    if not provider:
        raise HTTPException(status_code=400, detail="provider required")
    try:
        return DecisionMarketplace(Path.cwd()).install(provider)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/v1/capability/evaluate")
def capability_evaluate(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0015 — Capability Passport evaluate (Guardian Layer 2)."""
    capability = str(body.get("capability") or "").strip()
    if not capability:
        raise HTTPException(status_code=400, detail="capability required")
    try:
        from pathlib import Path

        from uap.capability_gov import CapabilityGovernor

        gov = CapabilityGovernor(Path.cwd())
        result = gov.evaluate(
            capability=capability,
            agent_id=str(body.get("agentId") or "") or None,
            path=body.get("path"),
            target=str(body.get("target") or "") or None,
            profile=str(body.get("profile") or "guardian"),
        )
        return {"ok": True, "result": result, "standard": "NGS-0015"}
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "result": {
                "decision": "deny",
                "capability": capability,
                "reasons": [f"capability evaluate fallback: {e}"],
            },
            "standard": "NGS-0015",
        }


# --- Guardian Network v1: Citizen / AI Gateway (NGS-0021/0022/0023) ---


@app.post("/v1/citizen/register")
def citizen_register(body: dict[str, Any] | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.citizen_registry import CitizenRegistry

    body = body or {}
    return CitizenRegistry(Path.cwd()).register(
        label=str(body.get("label") or "") or None,
        profile=str(body.get("profile") or "citizen"),
    )


@app.get("/v1/citizen/audit")
def citizen_audit(limit: int = 50, device_id: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.citizen_registry import CitizenRegistry

    return {
        "ok": True,
        "audit": CitizenRegistry(Path.cwd()).list_audit(limit=limit, device_id=device_id),
    }

@app.post("/v1/citizen/approve")
def citizen_approve(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.citizen_registry import CitizenRegistry

    device_id = str(body.get("deviceId") or "").strip()
    capability = str(body.get("capability") or "").strip()
    if not device_id or not capability:
        raise HTTPException(status_code=400, detail="deviceId and capability required")
    return CitizenRegistry(Path.cwd()).issue_approval(
        device_id=device_id, capability=capability
    )


@app.get("/v1/gateway/providers")
def gateway_providers() -> dict[str, Any]:
    from pathlib import Path

    from uap.ai_gateway import AIGateway

    return {"ok": True, "providers": AIGateway(Path.cwd()).providers(), "standard": "NGS-0021"}


@app.post("/v1/gateway/check")
def gateway_check(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.ai_gateway import AIGateway
    from uap.citizen_registry import CitizenRegistry

    reg = CitizenRegistry(Path.cwd())
    device = None
    key = str(body.get("apiKey") or body.get("citizenKey") or "").strip() or None
    if key:
        device = reg.resolve_key(key)
    profile = str(
        (device or {}).get("profile")
        or body.get("profile")
        or "citizen"
    )
    device_id = str((device or {}).get("deviceId") or body.get("deviceId") or "") or None
    return AIGateway(Path.cwd()).check(
        provider=str(body.get("provider") or "") or None,
        url=str(body.get("url") or "") or None,
        action=str(body.get("action") or "message.send"),
        text=str(body.get("text") or "") or None,
        agent_hint=str(body.get("agentHint") or body.get("agentId") or "") or None,
        capability=str(body.get("capability") or "") or None,
        approval_token=str(body.get("approvalToken") or "") or None,
        device_id=device_id,
        profile=profile,
    )


@app.get("/v1/cti/citizen/feed")
def cti_citizen_feed(limit: int = 50, since: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.ai_gateway import AIGateway

    return AIGateway(Path.cwd()).citizen_cti_feed(limit=limit, since=since)


@app.post("/v1/guardian/emergency/broadcast")
def emergency_broadcast(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.emergency import EmergencyBroadcast

    msg = str(body.get("message") or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message required")
    return EmergencyBroadcast(Path.cwd()).broadcast(
        message=msg,
        severity=str(body.get("severity") or "high"),
        action=str(body.get("action") or "refresh_cti"),
        issued_by=str(body.get("issuedBy") or "operator"),
    )


@app.get("/v1/guardian/emergency/feed")
def emergency_feed(limit: int = 20, since: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.emergency import EmergencyBroadcast

    return {
        "ok": True,
        "broadcasts": EmergencyBroadcast(Path.cwd()).list(limit=limit, since=since),
    }


@app.get("/v1/gateway/passport")
def gateway_passport(provider: str | None = None, agentHint: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.universal_ai_passport import UniversalAIPassport

    return {
        "ok": True,
        **UniversalAIPassport(Path.cwd()).resolve(provider=provider, agent_hint=agentHint),
    }


@app.post("/v1/guardian/kill")
def guardian_kill_issue(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0019 — issue Local Kill Token."""
    agent_id = str(body.get("agentId") or "").strip() or None
    session_id = str(body.get("sessionId") or "").strip() or None
    if not agent_id and not session_id:
        raise HTTPException(status_code=400, detail="agentId or sessionId required")
    try:
        from pathlib import Path

        from uap.kill import KillStore

        entry = KillStore(Path.cwd()).issue_local(
            agent_id=agent_id,
            session_id=session_id,
            reason=str(body.get("reason") or "api"),
            issued_by=str(body.get("issuedBy") or "api"),
        )
        return {"ok": True, "kill": entry, "standard": "NGS-0019"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/v1/guardian/kill/status")
def guardian_kill_status(
    agent_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    from pathlib import Path

    from uap.kill import KillStore

    return {
        "ok": True,
        **KillStore(Path.cwd()).status(agent_id=agent_id, session_id=session_id),
    }


@app.post("/v1/guardian/threat/analyze")
def guardian_threat_analyze(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0017 — analyze session execution graph for threat patterns."""
    session_id = str(body.get("sessionId") or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId required")
    try:
        from pathlib import Path

        from uap.threat import ThreatEngine

        engine = ThreatEngine(Path.cwd())
        if body.get("autoKill"):
            result = engine.analyze_and_maybe_kill(session_id, auto_kill=True)
        else:
            result = engine.analyze_session(session_id)
        return {"ok": True, "result": result, "standard": "NGS-0017"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/guardian/collective/opt-in")
def guardian_collective_opt_in(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0020 — opt in/out of collective threat signature sharing."""
    from pathlib import Path

    from uap.collective import CollectiveDefense

    return {
        "ok": True,
        **CollectiveDefense(Path.cwd()).set_opt_in(bool(body.get("optIn", True))),
        "standard": "NGS-0020",
    }


@app.post("/v1/guardian/collective/publish")
def guardian_collective_publish(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0020 — publish privacy-preserving signature from threat report/session."""
    from pathlib import Path

    from uap.collective import CollectiveDefense
    from uap.threat import ThreatEngine

    session_id = str(body.get("sessionId") or "").strip()
    report = body.get("report")
    try:
        if report is None:
            if not session_id:
                raise HTTPException(status_code=400, detail="sessionId or report required")
            report = ThreatEngine(Path.cwd()).analyze_session(session_id)
        sig = CollectiveDefense(Path.cwd()).publish_from_threat(
            report, org_id=str(body.get("orgId") or "") or None
        )
        return {"ok": True, "signature": sig, "standard": "NGS-0020"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/guardian/collective/import")
def guardian_collective_import(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense

    sig = body.get("signature")
    if not isinstance(sig, dict):
        raise HTTPException(status_code=400, detail="signature object required")
    return {
        "ok": True,
        "signature": CollectiveDefense(Path.cwd()).import_signature(sig),
        "standard": "NGS-0020",
    }


@app.get("/v1/guardian/collective/signatures")
def guardian_collective_list(source: str = "inbox") -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense

    return {
        "ok": True,
        "signatures": CollectiveDefense(Path.cwd()).list_signatures(source=source),
        "standard": "NGS-0020",
    }


@app.post("/v1/guardian/collective/apply")
def guardian_collective_apply(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense

    sid = str(body.get("signatureId") or "").strip()
    if not sid:
        raise HTTPException(status_code=400, detail="signatureId required")
    try:
        return CollectiveDefense(Path.cwd()).apply(
            sid,
            agent_id=str(body.get("agentId") or "") or None,
            auto_kill=bool(body.get("autoKill")),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/v1/guardian/constitution/evaluate")
def guardian_constitution_evaluate(body: dict[str, Any]) -> dict[str, Any]:
    """Guardian L4 — evaluate action against AI Constitution."""
    action = str(body.get("action") or "").strip()
    if not action:
        raise HTTPException(status_code=400, detail="action required")
    try:
        from pathlib import Path

        from uap.council import GuardianConstitution

        result = GuardianConstitution(Path.cwd()).evaluate(
            action=action,
            agent_id=str(body.get("agentId") or "") or None,
        )
        return {"ok": True, "result": result, "standard": "NGS-L4"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/guardian/constitution/install")
def guardian_constitution_install() -> dict[str, Any]:
    from pathlib import Path

    from uap.council import GuardianConstitution

    return {"ok": True, **GuardianConstitution(Path.cwd()).install_default(), "standard": "NGS-L4"}


@app.post("/v1/guardian/council/install")
def guardian_council_install() -> dict[str, Any]:
    from pathlib import Path

    from uap.council import GovernanceCouncil

    return {"ok": True, **GovernanceCouncil(Path.cwd()).install_default(), "standard": "NGS-L4"}


@app.post("/v1/guardian/council/propose")
def guardian_council_propose(body: dict[str, Any]) -> dict[str, Any]:
    kind = str(body.get("kind") or "").strip()
    member = str(body.get("proposedBy") or body.get("memberId") or "").strip()
    if not kind or not member:
        raise HTTPException(status_code=400, detail="kind and proposedBy required")
    try:
        from pathlib import Path

        from uap.council import GovernanceCouncil

        prop = GovernanceCouncil(Path.cwd()).propose(
            kind=kind,
            payload=dict(body.get("payload") or {}),
            proposed_by=member,
        )
        return {"ok": True, "proposal": prop, "standard": "NGS-L4"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/guardian/council/approve")
def guardian_council_approve(body: dict[str, Any]) -> dict[str, Any]:
    proposal_id = str(body.get("proposalId") or "").strip()
    member = str(body.get("memberId") or "").strip()
    if not proposal_id or not member:
        raise HTTPException(status_code=400, detail="proposalId and memberId required")
    try:
        from pathlib import Path

        from uap.council import GovernanceCouncil

        prop = GovernanceCouncil(Path.cwd()).approve(proposal_id, member_id=member)
        return {"ok": True, "proposal": prop, "standard": "NGS-L4"}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/v1/guardian/kill/domain")
def guardian_kill_domain(body: dict[str, Any]) -> dict[str, Any]:
    """NGS-0019 domain tier — stop all agents in org/domain."""
    from pathlib import Path

    from uap.kill import KillStore

    entry = KillStore(Path.cwd()).issue_domain(
        domain_id=str(body.get("domainId") or "") or None,
        reason=str(body.get("reason") or "api-domain"),
        issued_by=str(body.get("issuedBy") or "api"),
    )
    return {"ok": True, "kill": entry, "standard": "NGS-0019"}


@app.get("/v1/guardian/reputation/{agent_id}")
def guardian_reputation_get(agent_id: str) -> dict[str, Any]:
    from pathlib import Path

    from uap.reputation import ReputationStore

    return {"ok": True, "reputation": ReputationStore(Path.cwd()).get(agent_id), "standard": "NGS-0018"}


@app.post("/v1/guardian/reputation/{agent_id}")
def guardian_reputation_update(agent_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.reputation import ReputationStore

    store = ReputationStore(Path.cwd())
    if body.get("violation"):
        v = body["violation"] if isinstance(body["violation"], dict) else {}
        rep = store.add_violation(
            agent_id,
            kind=str(v.get("kind") or body.get("kind") or "manual"),
            severity=float(v.get("severity") or body.get("severity") or 0.5),
            detail=str(v.get("detail") or ""),
        )
    elif body.get("feedback") is not None:
        fb = body["feedback"] if isinstance(body["feedback"], dict) else {"score": body["feedback"]}
        rep = store.add_feedback(
            agent_id,
            score=float(fb.get("score") if isinstance(fb, dict) else fb),
            by=str((fb.get("by") if isinstance(fb, dict) else None) or body.get("by") or "peer"),
            note=str((fb.get("note") if isinstance(fb, dict) else None) or ""),
        )
    else:
        rep = store.record(
            agent_id,
            origin=str(body.get("origin") or "") or None,
            creator=str(body.get("creator") or "") or None,
            model=str(body.get("model") or "") or None,
            attested=bool(body.get("attested")),
            attestation_ref=str(body.get("attestationRef") or "") or None,
        )
    return {"ok": True, "reputation": rep, "standard": "NGS-0018"}


@app.post("/v1/guardian/container/install")
def guardian_container_install() -> dict[str, Any]:
    from pathlib import Path

    from uap.container import AgentContainer

    return {"ok": True, **AgentContainer(Path.cwd()).install_default(), "standard": "NGS-0016"}


@app.get("/v1/guardian/container/profile")
def guardian_container_profile(agent_id: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.container import AgentContainer

    try:
        return AgentContainer(Path.cwd()).profile(agent_id)
    except FileNotFoundError:
        AgentContainer(Path.cwd()).install_default()
        return AgentContainer(Path.cwd()).profile(agent_id)


@app.post("/v1/guardian/container/check")
def guardian_container_check(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.container import AgentContainer

    try:
        AgentContainer(Path.cwd()).load()
    except FileNotFoundError:
        AgentContainer(Path.cwd()).install_default()
    return AgentContainer(Path.cwd()).check(
        agent_id=str(body.get("agentId") or "anonymous"),
        action=str(body.get("action") or ""),
        tool=str(body.get("tool") or "") or None,
        network=bool(body.get("network")),
        spawn_depth=body.get("spawnDepth"),
    )


@app.post("/v1/guardian/collective/peers")
def guardian_collective_peers(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense

    peers = body.get("peers") or []
    if not isinstance(peers, list):
        raise HTTPException(status_code=400, detail="peers must be a list of URLs")
    return {"ok": True, **CollectiveDefense(Path.cwd()).set_peers([str(p) for p in peers])}


@app.post("/v1/guardian/collective/push")
def guardian_collective_push() -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense

    try:
        return CollectiveDefense(Path.cwd()).push_to_peers()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@app.post("/v1/guardian/collective/pull")
def guardian_collective_pull() -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense

    try:
        return CollectiveDefense(Path.cwd()).pull_from_peers()
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@app.post("/v1/guardian/cti/submit")
def guardian_cti_submit(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.cti_hub import CTIHub

    sig = body.get("signature")
    if not isinstance(sig, dict):
        raise HTTPException(status_code=400, detail="signature object required")
    try:
        # Cloud hub accepts when NARNA_CTI_HUB=1 or opt-in
        import os

        os.environ.setdefault("NARNA_CTI_HUB", "1")
        return CTIHub(Path.cwd()).submit(
            sig, org_id=str(body.get("orgId") or "") or None, require_opt_in=False
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/v1/guardian/cti/feed")
def guardian_cti_feed(limit: int = 100, since: str | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.cti_hub import CTIHub

    return {
        "ok": True,
        "feed": CTIHub(Path.cwd()).feed_list(limit=limit, since=since),
        "standard": "NGS-0020-hub",
    }


@app.post("/v1/guardian/cti/pull")
def guardian_cti_pull(body: dict[str, Any] | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense
    from uap.cti_hub import CTIHub

    body = body or {}
    # ensure opt-in for pull into workspace
    CollectiveDefense(Path.cwd()).set_opt_in(True)
    return CTIHub(Path.cwd()).pull_into_workspace(limit=int(body.get("limit") or 50))


@app.post("/v1/guardian/cti/subscribe")
def guardian_cti_subscribe(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.cti_hub import CTIHub

    org_hash = str(body.get("orgHash") or "").strip()
    if not org_hash:
        raise HTTPException(status_code=400, detail="orgHash required")
    return CTIHub(Path.cwd()).subscribe(
        org_hash=org_hash, callback_url=str(body.get("callbackUrl") or "") or None
    )


@app.post("/v1/guardian/cti/mesh/hubs")
def guardian_cti_mesh_hubs(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.cti_mesh import CTIMesh

    hubs = body.get("hubs") or []
    if not isinstance(hubs, list):
        raise HTTPException(status_code=400, detail="hubs must be a list")
    return {"ok": True, **CTIMesh(Path.cwd()).set_hubs([str(h) for h in hubs])}


@app.post("/v1/guardian/cti/mesh/sync")
def guardian_cti_mesh_sync(body: dict[str, Any] | None = None) -> dict[str, Any]:
    from pathlib import Path

    from uap.collective import CollectiveDefense
    from uap.cti_mesh import CTIMesh

    body = body or {}
    CollectiveDefense(Path.cwd()).set_opt_in(True)
    mesh = CTIMesh(Path.cwd())
    hubs = body.get("hubs")
    if isinstance(hubs, list) and hubs:
        mesh.set_hubs([str(h) for h in hubs])
    if body.get("pullOnly"):
        return mesh.pull()
    if body.get("pushOnly"):
        return mesh.push()
    return mesh.sync()


@app.get("/v1/guardian/jurisdictions")
def guardian_jurisdictions() -> dict[str, Any]:
    from pathlib import Path

    from uap.jurisdiction import JurisdictionTemplates

    return {"ok": True, "jurisdictions": JurisdictionTemplates(Path.cwd()).list()}


@app.post("/v1/guardian/bindings/{binding_id}/jurisdiction")
def guardian_binding_jurisdiction(binding_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.council_binding import CouncilBinding
    from uap.jurisdiction import JurisdictionTemplates

    jid = str(body.get("jurisdictionId") or body.get("jurisdiction") or "").strip()
    if not jid:
        raise HTTPException(status_code=400, detail="jurisdictionId required")
    try:
        binding = CouncilBinding(Path.cwd()).get(binding_id)
        return {
            "ok": True,
            "binding": JurisdictionTemplates(Path.cwd()).apply_to_binding(
                binding, jurisdiction_id=jid
            ),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/v1/guardian/isolation/partners")
def guardian_isolation_partners() -> dict[str, Any]:
    from pathlib import Path

    from uap.isolation_partner import IsolationRegistry

    return {"ok": True, "partners": IsolationRegistry(Path.cwd()).list()}


@app.post("/v1/guardian/isolation/certify")
def guardian_isolation_certify(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.partner_cert import PartnerRuntimeCertifier

    partner = str(body.get("partner") or "").strip()
    if not partner:
        raise HTTPException(status_code=400, detail="partner required")
    return PartnerRuntimeCertifier(Path.cwd()).certify(
        partner,
        agent_id=str(body.get("agentId") or "cert-probe"),
        attested=bool(body.get("attested")),
        issuer=str(body.get("issuer") or "narna-api"),
    )


@app.get("/v1/guardian/isolation/certs")
def guardian_isolation_certs() -> dict[str, Any]:
    from pathlib import Path

    from uap.partner_cert import PartnerRuntimeCertifier

    return {"ok": True, "certificates": PartnerRuntimeCertifier(Path.cwd()).list()}


@app.get("/v1/guardian/isolation/certs/{partner}/verify")
def guardian_isolation_cert_verify(partner: str) -> dict[str, Any]:
    from pathlib import Path

    from uap.partner_cert import PartnerRuntimeCertifier

    return PartnerRuntimeCertifier(Path.cwd()).verify(partner)


@app.post("/v1/guardian/isolation/plan")
def guardian_isolation_plan(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.isolation_partner import IsolationRegistry

    partner = str(body.get("partner") or "docker")
    agent_id = str(body.get("agentId") or "agent")
    try:
        return IsolationRegistry(Path.cwd()).plan(partner, agent_id=agent_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/v1/guardian/bindings")
def guardian_bindings_list() -> dict[str, Any]:
    from pathlib import Path

    from uap.council_binding import CouncilBinding

    return {"ok": True, "bindings": CouncilBinding(Path.cwd()).list()}


@app.get("/v1/guardian/bindings/{binding_id}/verify")
def guardian_binding_verify(binding_id: str) -> dict[str, Any]:
    from pathlib import Path

    from uap.council_binding import CouncilBinding

    try:
        return CouncilBinding(Path.cwd()).verify(binding_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.get("/v1/guardian/reputation/{agent_id}/digest")
def guardian_reputation_digest(agent_id: str) -> dict[str, Any]:
    from pathlib import Path

    from uap.reputation import ReputationStore

    return ReputationStore(Path.cwd()).export_digest(agent_id)


@app.post("/v1/guardian/reputation/import")
def guardian_reputation_import(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.reputation import ReputationStore

    return ReputationStore(Path.cwd()).import_digest(
        body if body.get("digests") else {"digests": body.get("digest") and [body["digest"]] or []},
        map_to_agent=str(body.get("mapToAgent") or "") or None,
    )


@app.get("/v1/guardian/status")
def guardian_status() -> dict[str, Any]:
    """Aggregate Guardian surface status for console."""
    from pathlib import Path

    from uap.collective import CollectiveDefense
    from uap.container import AgentContainer
    from uap.council import GovernanceCouncil, GuardianConstitution
    from uap.decision_market import DecisionMarketplace
    from uap.kill import KillStore

    ws = Path.cwd()
    out: dict[str, Any] = {"ok": True, "standard": "Guardian", "layers": ["L1", "L2", "L3", "L4"]}
    try:
        out["kill"] = KillStore(ws).status()
    except Exception as e:
        out["kill"] = {"error": str(e)}
    try:
        cd = CollectiveDefense(ws)
        out["collective"] = {
            "optIn": cd._opt_in(),  # noqa: SLF001
            "peers": cd.list_peers(),
            "inbox": len(cd.list_signatures(source="inbox")),
            "outbox": len(cd.list_signatures(source="outbox")),
        }
    except Exception as e:
        out["collective"] = {"error": str(e)}
    try:
        GuardianConstitution(ws).load()
        out["constitution"] = {"installed": True}
    except FileNotFoundError:
        try:
            GuardianConstitution(ws).install_default()
            out["constitution"] = {"installed": True, "justInstalled": True}
        except Exception as e:
            out["constitution"] = {"installed": False, "error": str(e)}
    try:
        GovernanceCouncil(ws).load()
        out["council"] = {"installed": True, "quorum": GovernanceCouncil(ws).quorum()}
    except FileNotFoundError:
        try:
            GovernanceCouncil(ws).install_default()
            out["council"] = {"installed": True, "justInstalled": True}
        except Exception as e:
            out["council"] = {"installed": False, "error": str(e)}
    try:
        AgentContainer(ws).load()
        out["container"] = AgentContainer(ws).profile()
    except FileNotFoundError:
        AgentContainer(ws).install_default()
        out["container"] = AgentContainer(ws).profile()
    except Exception as e:
        out["container"] = {"error": str(e)}
    try:
        out["decisionPackages"] = len(
            DecisionMarketplace(ws).list_packages(decisions_only=True)
        )
    except Exception as e:
        out["decisionPackages"] = {"error": str(e)}
    try:
        from uap.cti_hub import CTIHub
        from uap.council_binding import CouncilBinding
        from uap.cti_mesh import CTIMesh
        from uap.isolation_partner import IsolationRegistry
        from uap.jurisdiction import JurisdictionTemplates
        from uap.partner_cert import PartnerRuntimeCertifier

        hub = CTIHub(ws)
        out["ctiHub"] = {"feedSize": len(hub.feed_list(limit=1000)), "standard": "NGS-0020-hub"}
        out["ctiMesh"] = {"hubs": CTIMesh(ws).list_hubs()}
        out["bindings"] = {"count": len(CouncilBinding(ws).list())}
        out["jurisdictions"] = {"count": len(JurisdictionTemplates(ws).list())}
        out["isolation"] = {"partners": IsolationRegistry(ws).list()}
        out["partnerCerts"] = {
            "count": len(PartnerRuntimeCertifier(ws).list()),
            "standard": "NGS-0016-partner-cert",
        }
    except Exception as e:
        out["tierD"] = {"error": str(e)}
    return out


@app.post("/v1/guardian/container/docker-run")
def guardian_container_docker(body: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path

    from uap.container_runner import DockerContainerRunner

    return DockerContainerRunner(Path.cwd()).run(
        dry_run=not bool(body.get("execute")),
        agent_id=str(body.get("agentId") or "agent"),
        image=str(body.get("image") or "narna/agent-container:0.1"),
        network=str(body.get("network") or "none"),
    )


@app.get("/v1/telemetry/consent", response_model=TelemetryConsentResponse)
def telemetry_get_consent(
    org: Organization = Depends(get_org_from_api_key),
) -> TelemetryConsentResponse:
    return TelemetryConsentResponse(
        telemetryOptIn=bool(getattr(org, "telemetry_opt_in", 0)),
        trainOptIn=bool(getattr(org, "train_opt_in", 0)),
        message="Consent status",
    )


@app.post("/v1/telemetry/consent", response_model=TelemetryConsentResponse)
def telemetry_set_consent(
    body: TelemetryConsentRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> TelemetryConsentResponse:
    org.telemetry_opt_in = 1 if body.telemetryOptIn else 0
    org.train_opt_in = 1 if body.trainOptIn else 0
    db.commit()
    return TelemetryConsentResponse(
        telemetryOptIn=bool(org.telemetry_opt_in),
        trainOptIn=bool(org.train_opt_in),
        message="Consent updated — default remains off until you opt in",
    )


@app.post("/v1/telemetry/contribute", response_model=TelemetryContributeResponse)
def telemetry_contribute(
    body: TelemetryContributeRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> TelemetryContributeResponse:
    """Opt-in Governance Telemetry — sanitized graphs only (no prompts)."""
    if not bool(getattr(org, "telemetry_opt_in", 0)):
        raise HTTPException(
            status_code=403,
            detail="telemetryOptIn is false — POST /v1/telemetry/consent first",
        )

    try:
        from uap.telemetry import build_contribution_from_events, strip_forbidden
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"telemetry module unavailable: {e}") from e

    contribution = body.contribution
    if contribution is None:
        if not body.events:
            raise HTTPException(status_code=400, detail="contribution or events required")
        contribution = build_contribution_from_events(
            events=body.events,
            org_id=org.id,
            agent_id=body.agentId,
            agent_name=body.agentName,
            trust_score=body.trustScore,
            telemetry_opt_in=True,
            train_opt_in=bool(getattr(org, "train_opt_in", 0)),
        )
    else:
        contribution = strip_forbidden(contribution)

    # Defense-in-depth: refuse if consent flag inside payload is false
    meta = contribution.get("metadata") if isinstance(contribution, dict) else {}
    consent = (meta or {}).get("consent") if isinstance(meta, dict) else {}
    if isinstance(consent, dict) and consent.get("telemetryOptIn") is False:
        raise HTTPException(status_code=403, detail="contribution.consent.telemetryOptIn is false")

    spec = contribution.get("spec") if isinstance(contribution, dict) else None
    if not isinstance(spec, dict):
        raise HTTPException(status_code=400, detail="invalid contribution.spec")

    nodes = spec.get("nodes") if isinstance(spec.get("nodes"), list) else []
    edges = spec.get("edges") if isinstance(spec.get("edges"), list) else []
    totals = spec.get("totals") if isinstance(spec.get("totals"), dict) else {}
    tenant_hash = str(spec.get("tenantHash") or "")
    if not tenant_hash.startswith("th_"):
        raise HTTPException(status_code=400, detail="tenantHash must be pseudonymized (th_…)")

    # Strip any accidental forbidden keys from nodes
    nodes = strip_forbidden(nodes)
    edges = strip_forbidden(edges)

    row = TelemetryContribution(
        org_id=org.id,
        tenant_hash=tenant_hash,
        session_hash=spec.get("sessionHash"),
        train_opt_in=1 if bool(getattr(org, "train_opt_in", 0)) else 0,
        nodes_json=json.dumps(nodes),
        edges_json=json.dumps(edges),
        totals_json=json.dumps(totals),
        node_count=len(nodes),
        gu_total=int(totals.get("gu") or 0),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return TelemetryContributeResponse(
        contributionId=int(row.id),
        nodeCount=len(nodes),
        guTotal=int(row.gu_total),
        message="Sanitized governance graph accepted",
    )


@app.delete("/v1/telemetry/contributions")
def telemetry_delete_contributions(
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    deleted = (
        db.query(TelemetryContribution)
        .filter(TelemetryContribution.org_id == org.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"ok": True, "deleted": int(deleted)}


@app.get("/v1/telemetry/aggregate", response_model=TelemetryAggregateResponse)
def telemetry_aggregate(k: int = 5) -> TelemetryAggregateResponse:
    """Public k-anonymous Governance Intelligence aggregates."""
    k = max(2, min(int(k), 50))
    from .database import SessionLocal

    db = SessionLocal()
    try:
        rows = db.query(TelemetryContribution).all()
    finally:
        db.close()

    # Bucket by (agentClass, capabilityFamily)
    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        try:
            nodes = json.loads(row.nodes_json or "[]")
        except Exception:
            nodes = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            key = (
                str(node.get("agentClass") or "general"),
                str(node.get("capabilityFamily") or "unknown"),
            )
            b = buckets.setdefault(
                key,
                {
                    "tenants": set(),
                    "nodes": 0,
                    "human": 0,
                    "denies": 0,
                    "loops": 0,
                    "gu": 0,
                },
            )
            b["tenants"].add(row.tenant_hash)
            b["nodes"] += 1
            if node.get("humanApproval"):
                b["human"] += 1
            if node.get("decision") == "deny":
                b["denies"] += 1
            if node.get("failureClass") == "loop":
                b["loops"] += 1
            b["gu"] += int(node.get("guCost") or 0)

    out: list[TelemetryAggregateRow] = []
    for (agent_cls, cap), b in sorted(buckets.items()):
        tenant_count = len(b["tenants"])
        if tenant_count < k:
            continue
        n = max(1, b["nodes"])
        out.append(
            TelemetryAggregateRow(
                agentClass=agent_cls,
                capabilityFamily=cap,
                humanApprovalRate=round(b["human"] / n, 4),
                denyRate=round(b["denies"] / n, 4),
                loopFailureRate=round(b["loops"] / n, 4),
                avgGu=round(b["gu"] / n, 4),
                tenantCount=tenant_count,
                sampleNodes=b["nodes"],
            )
        )

    return TelemetryAggregateResponse(k=k, rows=out)


@app.get("/v1/benchmark/governance")
def governance_benchmark() -> dict[str, Any]:
    """Public governance leaderboard (not LLM MMLU)."""
    try:
        from uap.governance_benchmark import leaderboard

        return leaderboard()
    except Exception:
        # fallback if SDK path unavailable in API container
        return {
            "algorithm": "narna-governance-bench-v0",
            "description": "Governance / compliance posture — not LLM capability MMLU.",
            "rows": [
                {"vendor": "Anthropic", "score": 0.98, "notes": "Strong policy culture"},
                {"vendor": "OpenAI", "score": 0.96, "notes": "Agents SDK + OTel"},
                {"vendor": "Google", "score": 0.94, "notes": "Gemini / ADK"},
                {"vendor": "LangGraph", "score": 0.92, "notes": "narna-langgraph"},
                {"vendor": "CrewAI", "score": 0.9, "notes": "narna-crewai"},
            ],
        }


@app.get("/v1/compatibility/badges")
def compatibility_badges(request: Request) -> dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    # Frontend serves SVGs; document paths for embedders
    return {
        "badges": [
            {"id": "ugs-compatible", "title": "UGS Compatible", "path": "/badges/ugs-compatible.svg"},
            {"id": "uap-compatible", "title": "UGS Compatible", "path": "/badges/uap-compatible.svg"},
            {
                "id": "constitution-compatible",
                "title": "Constitution Compatible",
                "path": "/badges/constitution-compatible.svg",
            },
            {"id": "narna-certified", "title": "Verified by NARNA", "path": "/badges/narna-certified.svg"},
            {"id": "narna-certified-plus", "title": "NARNA Certified+", "path": "/badges/narna-certified-plus.svg"},
            {"id": "enterprise-ready", "title": "Enterprise Ready", "path": "/badges/enterprise-ready.svg"},
        ],
        "programUrl": f"{base.replace(':8000', ':5173')}/compatibility",
    }


@app.post("/v1/plugins/publish", response_model=PluginPublishResponse)
def plugins_publish(
    body: PluginPublishRequest,
    request: Request,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> PluginPublishResponse:
    row = db.query(RegistryPlugin).filter(RegistryPlugin.plugin_id == body.pluginId).first()
    if row is None:
        row = RegistryPlugin(plugin_id=body.pluginId, org_id=org.id)
        db.add(row)
    row.name = body.name
    row.version = body.version
    row.license = body.license
    row.spec_json = json.dumps(body.spec or {})
    row.stars = max(int(row.stars or 0), int(body.stars or 0))
    row.downloads = max(int(row.downloads or 0), int(body.downloads or 0))
    row.org_id = org.id
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    base = str(request.base_url).rstrip("/")
    return PluginPublishResponse(
        pluginId=row.plugin_id,
        registryUrl=f"{base}/v1/plugins/{row.plugin_id}",
        status="published",
    )


@app.get("/v1/plugins", response_model=list[PluginSummary])
def plugins_list(db: Session = Depends(get_db), q: str | None = None, limit: int = 50) -> list[PluginSummary]:
    rows = db.query(RegistryPlugin).order_by(RegistryPlugin.updated_at.desc()).limit(200).all()
    out: list[PluginSummary] = []
    for row in rows:
        if q:
            needle = q.lower()
            if needle not in f"{row.name} {row.plugin_id}".lower():
                continue
        out.append(
            PluginSummary(
                pluginId=row.plugin_id,
                name=row.name,
                version=row.version,
                license=row.license,
                spec=json.loads(row.spec_json or "{}"),
                stars=int(row.stars or 0),
                downloads=int(row.downloads or 0),
                publishedAt=row.published_at.isoformat() if row.published_at else "",
            )
        )
        if len(out) >= limit:
            break
    return out


@app.get("/v1/plugins/{plugin_id}", response_model=PluginSummary)
def plugins_get(plugin_id: str, db: Session = Depends(get_db)) -> PluginSummary:
    row = db.query(RegistryPlugin).filter(RegistryPlugin.plugin_id == plugin_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="plugin not found")
    return PluginSummary(
        pluginId=row.plugin_id,
        name=row.name,
        version=row.version,
        license=row.license,
        spec=json.loads(row.spec_json or "{}"),
        stars=int(row.stars or 0),
        downloads=int(row.downloads or 0),
        publishedAt=row.published_at.isoformat() if row.published_at else "",
    )


@app.post("/v1/packages/publish", response_model=PackagePublishResponse)
def packages_publish(
    body: PackagePublishRequest,
    request: Request,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> PackagePublishResponse:
    row = db.query(RegistryGovernancePackage).filter(
        RegistryGovernancePackage.package_id == body.packageId
    ).first()
    if row is None:
        row = RegistryGovernancePackage(package_id=body.packageId, org_id=org.id)
        db.add(row)
    row.name = body.name
    row.version = body.version
    row.provider = body.provider
    row.package_kind = body.packageKind
    row.license = body.license
    row.disclaimer = body.disclaimer or ""
    row.package_hash = body.packageHash or ""
    row.spec_json = json.dumps(body.spec or {})
    row.price_usd = int(getattr(body, "priceUsd", 0) or 0)
    row.take_rate_bps = int(getattr(body, "takeRateBps", 2000) or 2000)
    row.stars = max(int(row.stars or 0), int(body.stars or 0))
    row.downloads = max(int(row.downloads or 0), int(body.downloads or 0))
    row.org_id = org.id
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    base = str(request.base_url).rstrip("/")
    return PackagePublishResponse(
        packageId=row.package_id,
        registryUrl=f"{base}/v1/packages/{row.package_id}",
        status="published",
    )


def _package_summary(row: RegistryGovernancePackage) -> PackageSummary:
    return PackageSummary(
        packageId=row.package_id,
        name=row.name,
        version=row.version,
        provider=row.provider,
        packageKind=row.package_kind,
        license=row.license,
        disclaimer=row.disclaimer or "",
        packageHash=row.package_hash or "",
        spec=json.loads(row.spec_json or "{}"),
        priceUsd=int(row.price_usd or 0),
        takeRateBps=int(row.take_rate_bps or 2000),
        authorRevenueUsd=int(row.author_revenue_usd or 0),
        platformRevenueUsd=int(row.platform_revenue_usd or 0),
        stars=int(row.stars or 0),
        downloads=int(row.downloads or 0),
        publishedAt=row.published_at.isoformat() if row.published_at else "",
    )


@app.get("/v1/packages", response_model=list[PackageSummary])
def packages_list(
    db: Session = Depends(get_db), q: str | None = None, limit: int = 50
) -> list[PackageSummary]:
    rows = (
        db.query(RegistryGovernancePackage)
        .order_by(RegistryGovernancePackage.updated_at.desc())
        .limit(200)
        .all()
    )
    out: list[PackageSummary] = []
    for row in rows:
        if q:
            needle = q.lower()
            if needle not in f"{row.name} {row.package_id} {row.provider}".lower():
                continue
        out.append(_package_summary(row))
        if len(out) >= limit:
            break
    return out


@app.get("/v1/packages/{package_id}", response_model=PackageSummary)
def packages_get(package_id: str, db: Session = Depends(get_db)) -> PackageSummary:
    row = (
        db.query(RegistryGovernancePackage)
        .filter(RegistryGovernancePackage.package_id == package_id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="package not found")
    return _package_summary(row)


@app.post("/v1/packages/purchase", response_model=PackagePurchaseResponse)
def packages_purchase(
    body: PackagePurchaseRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> PackagePurchaseResponse:
    """Buy a Governance Package.

    - Free → activate immediately
    - Paid + UAP_BILLING_MODE=mock → simulate payment (local demo)
    - Paid otherwise → 410 (use USDC/USDT Cloud billing; card/Stripe/Paddle removed)
    """
    row = (
        db.query(RegistryGovernancePackage)
        .filter(RegistryGovernancePackage.package_id == body.packageId)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="package not found")

    already = (
        db.query(MarketplacePurchase)
        .filter(
            MarketplacePurchase.org_id == org.id,
            MarketplacePurchase.package_id == row.package_id,
            MarketplacePurchase.status.in_(("paid", "free", "mock")),
        )
        .first()
    )
    if already is not None:
        return PackagePurchaseResponse(
            packageId=row.package_id,
            priceUsd=int(already.price_usd or 0),
            takeRateBps=int(already.take_rate_bps or 2000),
            platformCutUsd=int(already.platform_cut_usd or 0),
            authorCutUsd=int(already.author_cut_usd or 0),
            guCharged=int(already.gu_charged or 0),
            status=str(already.status),
            mode="owned",
            message=f"Already owned: {row.name}",
        )

    price = int(row.price_usd or 0)
    bps = int(row.take_rate_bps or 2000)
    platform_cut = (price * bps) // 10_000
    author_cut = price - platform_cut
    # Free packages still charge 1 GU for activation metering; paid ≈ $1 → 1 GU floor
    gu_charged = 1 if price == 0 else max(1, price // 100)
    mode = get_billing_mode()

    def _fulfill(*, status: str, mode_label: str, stripe_session_id: str | None = None) -> PackagePurchaseResponse:
        enforce_plan_limit(org=org, projected_events=0, projected_gu=gu_charged)
        org.gu_in_period = int(org.gu_in_period) + gu_charged
        row.downloads = int(row.downloads or 0) + 1
        row.author_revenue_usd = int(row.author_revenue_usd or 0) + author_cut
        row.platform_revenue_usd = int(row.platform_revenue_usd or 0) + platform_cut
        db.add(
            MarketplacePurchase(
                org_id=org.id,
                package_id=row.package_id,
                price_usd=price,
                take_rate_bps=bps,
                platform_cut_usd=platform_cut,
                author_cut_usd=author_cut,
                gu_charged=gu_charged,
                status=status,
                stripe_session_id=stripe_session_id,
            )
        )
        db.commit()
        return PackagePurchaseResponse(
            packageId=row.package_id,
            priceUsd=price,
            takeRateBps=bps,
            platformCutUsd=platform_cut,
            authorCutUsd=author_cut,
            guCharged=gu_charged,
            status=status,
            mode=mode_label,
            message=f"Purchased {row.name} — platform take {bps / 100:.0f}%",
        )

    # Free packages: no payment needed
    if price == 0:
        return _fulfill(status="free", mode_label="free")

    # Local / demo: simulate payment
    if mode == "mock":
        return _fulfill(status="mock", mode_label="mock")

    # Card / Stripe / Paddle removed — stablecoins only
    raise HTTPException(
        status_code=410,
        detail=(
            "Card / Stripe / Paddle checkout removed. "
            "Pay NARNA Cloud seats with USDC/USDT via POST /v1/billing/crypto/checkout-session "
            "or /billing. For paid marketplace packages, contact enterprise@narna.ai "
            "or use mock mode for local demos."
        ),
    )


@app.post("/v1/packages/verify-session", response_model=PackagePurchaseResponse)
def packages_verify_session(
    body: dict[str, Any],
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> PackagePurchaseResponse:
    """Card session verify retired — use USDC/USDT billing."""
    raise HTTPException(
        status_code=410,
        detail=(
            "Stripe / Paddle package verify removed. "
            "Pay with USDC/USDT via /billing or contact enterprise@narna.ai."
        ),
    )


@app.post("/v1/billing/paddle/webhook")
async def paddle_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    raise HTTPException(
        status_code=410,
        detail="Paddle billing removed. Pay with USDC/USDT via /v1/billing/crypto/checkout-session",
    )


def _fulfill_stripe_package_purchase(
    *,
    db: Session,
    org_id: int,
    package_id: str,
    stripe_session_id: str | None,
) -> bool:
    """Legacy helper retained for idempotent DB repairs — card rail is retired."""
    pending = (
        db.query(MarketplacePurchase)
        .filter(
            MarketplacePurchase.org_id == org_id,
            MarketplacePurchase.package_id == package_id,
            MarketplacePurchase.status == "pending",
        )
        .order_by(MarketplacePurchase.id.desc())
        .first()
    )
    if pending is None:
        paid = (
            db.query(MarketplacePurchase)
            .filter(
                MarketplacePurchase.org_id == org_id,
                MarketplacePurchase.package_id == package_id,
                MarketplacePurchase.status == "paid",
            )
            .first()
        )
        return paid is not None

    org = db.query(Organization).filter(Organization.id == org_id).first()
    row = (
        db.query(RegistryGovernancePackage)
        .filter(RegistryGovernancePackage.package_id == package_id)
        .first()
    )
    if org is None or row is None:
        return False

    gu_charged = int(pending.gu_charged or 0) or (
        1 if int(pending.price_usd or 0) == 0 else max(1, int(pending.price_usd or 0) // 100)
    )
    enforce_plan_limit(org=org, projected_events=0, projected_gu=gu_charged)
    org.gu_in_period = int(org.gu_in_period) + gu_charged
    row.downloads = int(row.downloads or 0) + 1
    row.author_revenue_usd = int(row.author_revenue_usd or 0) + int(pending.author_cut_usd or 0)
    row.platform_revenue_usd = int(row.platform_revenue_usd or 0) + int(pending.platform_cut_usd or 0)
    pending.status = "paid"
    pending.gu_charged = gu_charged
    if stripe_session_id:
        pending.stripe_session_id = stripe_session_id
    db.commit()
    return True


@app.post("/v1/keys", response_model=ApiKeyResponse)
def create_api_key(
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
    label: str = "default",
) -> ApiKeyResponse:
    full, prefix, key_hash = generate_api_key()
    db.add(ApiKey(org_id=org.id, key_prefix=prefix, key_hash=key_hash, label=label))
    db.commit()
    return ApiKeyResponse(
        apiKey=full,
        prefix=prefix,
        label=label,
        message="Store this key securely; it will not be shown again.",
    )

