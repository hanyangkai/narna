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
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .auth import get_org_from_api_key
from .billing import (
    count_governance_units,
    now_utc,
    plan_event_limit,
    plan_gu_limit,
    plan_usd_price,
    reset_if_new_period,
)
from .crypto_bot import start_background_bot
from .crypto_chains import build_pay_uri, list_supported_networks, validate_crypto_payment
from .invoice_utils import build_qr_payload, expire_pending_invoices, invoice_expires_at
from .database import get_db, init_db
from .metrics import METRICS
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
from .rate_limit import InMemoryRateLimiter
from .schemas import (
    ApiKeyResponse,
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

app = FastAPI(title="UAP Cloud API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("UAP_CLOUD_CORS_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT_PER_MIN = int(os.environ.get("UAP_RATE_LIMIT_PER_MIN", "120"))
limiter = InMemoryRateLimiter(limit_per_min=RATE_LIMIT_PER_MIN)


def _rate_key(req: Request) -> str:
    auth = req.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:]
    return req.client.host if req.client else "anon"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/v1/health"):
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
    """Public demo passport for /passport/narna-demo-agent (no login)."""
    from .database import SessionLocal

    db = SessionLocal()
    try:
        agent_id = "narna-demo-agent"
        existing = (
            db.query(RegistryAgent).filter(RegistryAgent.agent_id == agent_id).first()
        )
        passport = {
            "passportId": "passport_demo_001",
            "identity": {"agentId": agent_id, "name": "NARNA Demo Agent", "version": "0.1.0"},
            "capability": {"declared": ["general", "governance", "audit"]},
            "governance": {"policyRef": "local-default@0.0.0"},
            "trust": {"score": 0.92, "band": "high"},
            "history": {"runCount": 128, "successCount": 126},
        }
        if existing is not None:
            if not existing.passport_json:
                existing.passport_json = json.dumps(passport)
                existing.trust_score = 0.92
                existing.verified = 1
                db.commit()
            return
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
                passport_json=json.dumps(passport),
                verified=1,
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
def health() -> dict[str, str]:
    return {"status": "ok", "service": "narna-cloud", "version": "0.1.0", "api": "https://api.narna.org"}


@app.get("/v1/billing/paddle/status")
def paddle_billing_status(live_probe: bool = False) -> dict[str, Any]:
    """Paddle checkout readiness (config only; optional live_probe=1 creates a $1 test txn)."""
    from .paddle_billing import paddle_api_key, paddle_api_base, paddle_product_id, paddle_request
    from .paddle_urls import narna_public_url, paddle_success_url

    key = paddle_api_key()
    product_id = paddle_product_id()
    mode = get_billing_mode()
    out: dict[str, Any] = {
        "billingMode": mode,
        "paddleConfigured": bool(key and product_id),
        "paddleApiBase": paddle_api_base() if key else None,
        "productId": product_id or None,
        "publicUrl": narna_public_url(),
        "successUrlBilling": paddle_success_url("billing"),
        "successUrlPackage": paddle_success_url("package"),
        "webhookPath": "/v1/billing/paddle/webhook",
        "checkoutEnabled": None,
        "checkoutError": None,
        "setupDoc": "/docs/PADDLE-SETUP.md",
    }
    if mode != "paddle" or not key or not product_id:
        out["checkoutError"] = "Set UAP_BILLING_MODE=paddle, PADDLE_API_KEY, PADDLE_PRODUCT_ID"
        return out
    if not live_probe:
        out["hint"] = "Add ?live_probe=1 to test transaction creation (creates $1 probe txn)"
        return out
    try:
        probe = paddle_request(
            "POST",
            "/transactions",
            {
                "items": [
                    {
                        "quantity": 1,
                        "price": {
                            "description": "NARNA checkout probe",
                            "name": "Probe",
                            "product_id": product_id,
                            "unit_price": {"amount": "100", "currency_code": "USD"},
                            "tax_mode": "account_setting",
                        },
                    }
                ],
                "currency_code": "USD",
                "collection_mode": "automatic",
                "custom_data": {"kind": "probe"},
            },
        )
        data = probe.get("data") or {}
        checkout_url = (data.get("checkout") or {}).get("url")
        out["checkoutEnabled"] = bool(checkout_url)
        out["probeTransactionId"] = data.get("id")
        if not checkout_url:
            out["checkoutError"] = "Transaction created but checkout URL missing"
    except Exception as e:
        msg = str(e)
        out["checkoutEnabled"] = False
        out["checkoutError"] = msg
        if "transaction_checkout_not_enabled" in msg:
            out["onboardingHint"] = (
                "Complete Paddle seller onboarding, default payment link, website approval. "
                "Email sellers@paddle.com if stuck."
            )
    return out


def get_billing_mode() -> str:
    return os.environ.get("UAP_BILLING_MODE", "mock").lower()


def _plan_price_cents(plan: str) -> int:
    """USD cents for Cloud plans (fallback if Paddle catalog price not set)."""
    table = {
        "pro": 1900,
        "team": 4900,
        "business": 9900,
        "enterprise": 0,
    }
    return int(table.get(plan.lower(), 0))


def enforce_plan_limit(
    *,
    org: Organization,
    projected_events: int,
    projected_gu: int = 0,
) -> None:
    now = now_utc()
    if org.period_start_at is None or reset_if_new_period(
        period_start_at=org.period_start_at, now=now
    ):
        org.period_start_at = now
        org.events_in_period = 0
        org.gu_in_period = 0

    gu_limit = plan_gu_limit(org.plan)
    if gu_limit is not None and projected_gu > 0:
        if (int(org.gu_in_period) + projected_gu) > gu_limit:
            raise HTTPException(
                status_code=402,
                detail=f"plan GU limit exceeded: plan={org.plan}, limit={gu_limit} GU/mo",
            )

    limit = plan_event_limit(org.plan)
    if limit is None:
        return

    if (int(org.events_in_period) + projected_events) > limit:
        raise HTTPException(
            status_code=402,
            detail=f"plan limit exceeded: plan={org.plan}, limit={limit} events/mo",
        )


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
        "plan": org.plan,
        "periodStartAt": org.period_start_at.isoformat()
        if org.period_start_at
        else "",
        "eventsInPeriod": org.events_in_period,
        "eventsLimit": limit,
        "guInPeriod": org.gu_in_period,
        "guLimit": plan_gu_limit(org.plan),
        "metrics": METRICS.__dict__,
    }


@app.post("/v1/billing/mock/set-plan", response_model=BillingCheckoutResponse)
def mock_set_plan(
    body: BillingMockSetPlanRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> BillingCheckoutResponse:
    org.plan = body.plan
    now = now_utc()
    org.period_start_at = now
    org.events_in_period = 0
    org.gu_in_period = 0
    db.commit()
    return BillingCheckoutResponse(ok=True, url="mock://plan-changed", mode="mock")


@app.get("/v1/billing/status", response_model=BillingStatusResponse)
def billing_status(
    org: Organization = Depends(get_org_from_api_key),
) -> BillingStatusResponse:
    return BillingStatusResponse(
        plan=org.plan,
        periodStartAt=org.period_start_at.isoformat() if org.period_start_at else "",
        eventsInPeriod=int(org.events_in_period),
        eventsLimit=plan_event_limit(org.plan),
        guInPeriod=int(org.gu_in_period),
        guLimit=plan_gu_limit(org.plan),
        billingMode=get_billing_mode(),
    )


@app.post("/v1/billing/checkout-session", response_model=BillingCheckoutResponse)
def checkout_session(
    body: BillingCheckoutRequest,
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> BillingCheckoutResponse:
    mode = get_billing_mode()
    if mode == "mock":
        org.plan = body.plan
        now = now_utc()
        org.period_start_at = now
        org.events_in_period = 0
        org.gu_in_period = 0
        db.commit()
        return BillingCheckoutResponse(
            ok=True, url="mock://checkout/success", mode="mock"
        )

    if mode == "paddle":
        try:
            from .paddle_billing import create_plan_checkout
            from .paddle_urls import paddle_success_url

            cents = _plan_price_cents(body.plan)
            if cents <= 0:
                raise HTTPException(status_code=400, detail=f"plan {body.plan} not purchasable via checkout")
            success = paddle_success_url("billing")
            out = create_plan_checkout(
                plan=body.plan,
                org_id=org.id,
                price_cents=cents,
                success_url=success,
            )
            url = out.get("checkoutUrl")
            if not url:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Paddle Checkout not enabled yet. Finish onboarding at "
                        "https://vendors.paddle.com/authentication-v2 then enable Checkout."
                    ),
                )
            return BillingCheckoutResponse(ok=True, url=url, mode="paddle")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e)) from e

    if mode != "stripe":
        raise HTTPException(status_code=503, detail="billing mode not configured")

    # Stripe scaffold (optional): for local dev keep UAP_BILLING_MODE=mock
    try:
        import stripe  # type: ignore
    except Exception:
        raise HTTPException(status_code=503, detail="stripe dependency not available")

    stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="STRIPE_API_KEY missing")

    price_env = f"STRIPE_PRICE_ID_{body.plan.upper()}"
    price_id = os.environ.get(price_env, "")
    if not price_id:
        raise HTTPException(status_code=503, detail=f"missing env {price_env}")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=os.environ.get("STRIPE_SUCCESS_URL", "http://localhost:5173/console"),
        cancel_url=os.environ.get("STRIPE_CANCEL_URL", "http://localhost:5173/pricing"),
        metadata={"org_id": str(org.id), "plan": body.plan},
    )
    return BillingCheckoutResponse(ok=True, url=session.url, mode="stripe")


def get_crypto_mode() -> str:
    return os.environ.get("UAP_CRYPTO_MODE", "mock").lower()


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

    plan_price = plan_usd_price(body.plan)
    if plan_price <= 0:
        raise HTTPException(status_code=400, detail="plan is not payable by crypto")
    receiver_wallet = get_crypto_receiver_wallet()

    import hashlib

    invoice_src = f"{org.id}:{body.plan}:{asset}:{network}:{datetime.now(timezone.utc).timestamp()}"
    invoice_id = "inv_" + hashlib.sha256(invoice_src.encode()).hexdigest()[:16]
    expires = invoice_expires_at()
    amount_str = f"{plan_price:.2f}"
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
        plan=body.plan,
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
        org.plan = body.plan
        org.period_start_at = now_utc()
        org.events_in_period = 0
        invoice.status = "paid"
        invoice.tx_hash = "0xmock"
        invoice.paid_at = now_utc()
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
    mode = get_billing_mode()
    if mode != "stripe":
        raise HTTPException(status_code=404, detail="stripe billing not enabled")

    try:
        import stripe  # type: ignore
    except Exception:
        raise HTTPException(status_code=503, detail="stripe dependency not available")

    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET missing")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid webhook signature: {e}")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        session_data = session_obj.to_dict() if hasattr(session_obj, "to_dict") else dict(session_obj)
        metadata = dict(session_data.get("metadata") or {})
        kind = str(metadata.get("kind") or "subscription")
        org_id = metadata.get("org_id")
        session_id = session_data.get("id")

        if kind == "package" and org_id and metadata.get("package_id"):
            _fulfill_stripe_package_purchase(
                db=db,
                org_id=int(org_id),
                package_id=str(metadata["package_id"]),
                stripe_session_id=str(session_id) if session_id else None,
            )
        else:
            plan = metadata.get("plan")
            if org_id and plan:
                org = db.query(Organization).filter(Organization.id == int(org_id)).first()
                if org is not None:
                    org.plan = str(plan)
                    org.period_start_at = now_utc()
                    org.events_in_period = 0
                    org.gu_in_period = 0
                    db.commit()

    return {"ok": True}


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
    - Paid + stripe → Stripe Checkout; fulfill on webhook checkout.session.completed
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

    # Free packages: no card needed
    if price == 0:
        return _fulfill(status="free", mode_label="free")

    # Local / demo: simulate payment without card processor
    if mode == "mock":
        return _fulfill(status="mock", mode_label="mock")

    # ── Paddle Billing (preferred) ──
    if mode == "paddle":
        try:
            from .paddle_billing import create_package_checkout

            from .paddle_urls import paddle_success_url

            success = paddle_success_url("package")
            out = create_package_checkout(
                package_id=row.package_id,
                package_name=row.name,
                price_cents=price,
                org_id=org.id,
                take_rate_bps=bps,
                gu_charged=gu_charged,
                success_url=success,
            )
        except Exception as e:
            msg = str(e)
            if "transaction_checkout_not_enabled" in msg or "Checkout has not yet been enabled" in msg:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Paddle Checkout chưa bật trên account. Hoàn tất onboarding tại "
                        "https://vendors.paddle.com/authentication-v2 rồi bật Checkout "
                        "(Paddle Support nếu cần)."
                    ),
                ) from e
            raise HTTPException(status_code=503, detail=msg) from e

        txn_id = str(out.get("transactionId") or "")
        checkout_url = out.get("checkoutUrl")
        db.add(
            MarketplacePurchase(
                org_id=org.id,
                package_id=row.package_id,
                price_usd=price,
                take_rate_bps=bps,
                platform_cut_usd=platform_cut,
                author_cut_usd=author_cut,
                gu_charged=0,
                status="pending",
                stripe_session_id=txn_id,  # stores Paddle txn id (external payment ref)
            )
        )
        db.commit()
        if not checkout_url:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Paddle transaction created but checkout URL missing. "
                    "Enable Checkout in Paddle Dashboard / finish vendor onboarding."
                ),
            )
        return PackagePurchaseResponse(
            packageId=row.package_id,
            priceUsd=price,
            takeRateBps=bps,
            platformCutUsd=platform_cut,
            authorCutUsd=author_cut,
            guCharged=0,
            status="pending",
            mode="paddle",
            checkoutUrl=checkout_url,
            message=f"Redirect to Paddle Checkout for {row.name}",
        )

    if mode != "stripe":
        raise HTTPException(status_code=503, detail="billing mode not configured")

    try:
        import stripe  # type: ignore
    except Exception:
        raise HTTPException(status_code=503, detail="stripe dependency not available")

    stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="STRIPE_API_KEY missing")

    success = os.environ.get(
        "STRIPE_PACKAGE_SUCCESS_URL",
        os.environ.get("STRIPE_SUCCESS_URL", "http://localhost:5173/packages?paid=1"),
    )
    cancel = os.environ.get(
        "STRIPE_PACKAGE_CANCEL_URL",
        os.environ.get("STRIPE_CANCEL_URL", "http://localhost:5173/packages?canceled=1"),
    )
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": price,
                    "product_data": {
                        "name": row.name,
                        "description": f"NARNA Governance Package · {row.package_id} · take {bps / 100:.0f}%",
                    },
                },
                "quantity": 1,
            }
        ],
        success_url=f"{success}&packageId={row.package_id}&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{cancel}&packageId={row.package_id}",
        metadata={
            "kind": "package",
            "org_id": str(org.id),
            "package_id": row.package_id,
            "price_usd": str(price),
            "take_rate_bps": str(bps),
            "gu_charged": str(gu_charged),
        },
    )

    db.add(
        MarketplacePurchase(
            org_id=org.id,
            package_id=row.package_id,
            price_usd=price,
            take_rate_bps=bps,
            platform_cut_usd=platform_cut,
            author_cut_usd=author_cut,
            gu_charged=0,
            status="pending",
            stripe_session_id=session.id,
        )
    )
    db.commit()

    return PackagePurchaseResponse(
        packageId=row.package_id,
        priceUsd=price,
        takeRateBps=bps,
        platformCutUsd=platform_cut,
        authorCutUsd=author_cut,
        guCharged=0,
        status="pending",
        mode="stripe",
        checkoutUrl=session.url,
        message=f"Redirect to Stripe Checkout for {row.name}",
    )


@app.post("/v1/packages/verify-session", response_model=PackagePurchaseResponse)
def packages_verify_session(
    body: dict[str, Any],
    org: Organization = Depends(get_org_from_api_key),
    db: Session = Depends(get_db),
) -> PackagePurchaseResponse:
    """Confirm payment and fulfill package (Paddle txn id or Stripe session id)."""
    session_id = str(
        body.get("sessionId") or body.get("transactionId") or body.get("_ptxn") or ""
    ).strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId required")

    mode = get_billing_mode()

    if mode == "paddle" or session_id.startswith("txn_"):
        try:
            from .paddle_billing import get_transaction

            txn = get_transaction(session_id)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"cannot retrieve paddle transaction: {e}"
            ) from e

        custom = dict(txn.get("custom_data") or {})
        if str(custom.get("kind")) != "package":
            raise HTTPException(status_code=400, detail="transaction is not a package purchase")
        if str(custom.get("org_id")) != str(org.id):
            raise HTTPException(status_code=403, detail="transaction does not belong to this org")

        package_id = str(custom.get("package_id") or "")
        status = str(txn.get("status") or "")
        paid = status in {"paid", "completed", "billed"}
        if not paid:
            return PackagePurchaseResponse(
                packageId=package_id,
                priceUsd=int(custom.get("price_usd") or 0),
                takeRateBps=int(custom.get("take_rate_bps") or 2000),
                platformCutUsd=0,
                authorCutUsd=0,
                guCharged=0,
                status="pending",
                mode="paddle",
                message=f"Payment not completed yet (paddle status={status})",
            )

        _fulfill_stripe_package_purchase(
            db=db,
            org_id=org.id,
            package_id=package_id,
            stripe_session_id=session_id,
        )
        purchase = (
            db.query(MarketplacePurchase)
            .filter(
                MarketplacePurchase.org_id == org.id,
                MarketplacePurchase.package_id == package_id,
                MarketplacePurchase.status == "paid",
            )
            .order_by(MarketplacePurchase.id.desc())
            .first()
        )
        row = (
            db.query(RegistryGovernancePackage)
            .filter(RegistryGovernancePackage.package_id == package_id)
            .first()
        )
        name = row.name if row is not None else package_id
        return PackagePurchaseResponse(
            packageId=package_id,
            priceUsd=int(purchase.price_usd) if purchase else 0,
            takeRateBps=int(purchase.take_rate_bps) if purchase else 2000,
            platformCutUsd=int(purchase.platform_cut_usd) if purchase else 0,
            authorCutUsd=int(purchase.author_cut_usd) if purchase else 0,
            guCharged=int(purchase.gu_charged) if purchase else 0,
            status="paid",
            mode="paddle",
            message=f"Payment confirmed — {name} unlocked",
        )

    if mode != "stripe":
        raise HTTPException(
            status_code=400,
            detail=f"billing mode {mode} does not support verify-session",
        )

    try:
        import stripe  # type: ignore
    except Exception:
        raise HTTPException(status_code=503, detail="stripe dependency not available")

    stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="STRIPE_API_KEY missing")

    try:
        session_obj = stripe.checkout.Session.retrieve(session_id)
        session_data = session_obj.to_dict() if hasattr(session_obj, "to_dict") else dict(session_obj)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cannot retrieve session: {e}") from e

    metadata = dict(session_data.get("metadata") or {})
    if str(metadata.get("kind")) != "package":
        raise HTTPException(status_code=400, detail="session is not a package purchase")
    if str(metadata.get("org_id")) != str(org.id):
        raise HTTPException(status_code=403, detail="session does not belong to this org")

    package_id = str(metadata.get("package_id") or "")
    paid = session_data.get("payment_status") == "paid"
    if not paid:
        return PackagePurchaseResponse(
            packageId=package_id,
            priceUsd=int(metadata.get("price_usd") or 0),
            takeRateBps=int(metadata.get("take_rate_bps") or 2000),
            platformCutUsd=0,
            authorCutUsd=0,
            guCharged=0,
            status="pending",
            mode="stripe",
            message="Payment not completed yet",
        )

    _fulfill_stripe_package_purchase(
        db=db,
        org_id=org.id,
        package_id=package_id,
        stripe_session_id=session_id,
    )

    row = (
        db.query(RegistryGovernancePackage)
        .filter(RegistryGovernancePackage.package_id == package_id)
        .first()
    )
    purchase = (
        db.query(MarketplacePurchase)
        .filter(
            MarketplacePurchase.org_id == org.id,
            MarketplacePurchase.package_id == package_id,
            MarketplacePurchase.status == "paid",
        )
        .order_by(MarketplacePurchase.id.desc())
        .first()
    )
    name = row.name if row is not None else package_id
    return PackagePurchaseResponse(
        packageId=package_id,
        priceUsd=int(purchase.price_usd) if purchase else 0,
        takeRateBps=int(purchase.take_rate_bps) if purchase else 2000,
        platformCutUsd=int(purchase.platform_cut_usd) if purchase else 0,
        authorCutUsd=int(purchase.author_cut_usd) if purchase else 0,
        guCharged=int(purchase.gu_charged) if purchase else 0,
        status="paid",
        mode="stripe",
        message=f"Payment confirmed — {name} unlocked",
    )


@app.post("/v1/billing/paddle/webhook")
async def paddle_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Paddle Billing webhook — fulfill package / plan on transaction.completed."""
    if get_billing_mode() != "paddle":
        raise HTTPException(status_code=404, detail="paddle billing not enabled")

    # Optional shared-secret header check (set PADDLE_WEBHOOK_SECRET in Dashboard notification)
    expected = os.environ.get("PADDLE_WEBHOOK_SECRET", "").strip()
    if expected:
        got = request.headers.get("paddle-signature") or request.headers.get("Paddle-Signature") or ""
        # Paddle uses signed payloads; for MVP accept a static shared token header if configured.
        if expected not in got and request.headers.get("X-Paddle-Secret") != expected:
            # Still parse — production should verify HMAC; log soft warning
            logger.warning("paddle webhook secret mismatch (continuing for MVP)")

    payload = await request.json()
    event_type = str(payload.get("event_type") or payload.get("eventType") or "")
    data = payload.get("data") or {}

    if event_type in {
        "transaction.completed",
        "transaction.paid",
        "transaction.updated",
    }:
        custom = dict(data.get("custom_data") or {})
        status = str(data.get("status") or "")
        if status not in {"paid", "completed", "billed"} and event_type == "transaction.updated":
            return {"ok": True, "skipped": True}

        kind = str(custom.get("kind") or "")
        org_id = custom.get("org_id")
        txn_id = data.get("id")

        if kind == "package" and org_id and custom.get("package_id"):
            _fulfill_stripe_package_purchase(
                db=db,
                org_id=int(org_id),
                package_id=str(custom["package_id"]),
                stripe_session_id=str(txn_id) if txn_id else None,
            )
        elif kind == "subscription" and org_id and custom.get("plan"):
            org = db.query(Organization).filter(Organization.id == int(org_id)).first()
            if org is not None:
                org.plan = str(custom["plan"])
                org.period_start_at = now_utc()
                org.events_in_period = 0
                org.gu_in_period = 0
                db.commit()

    return {"ok": True, "event": event_type}


def _fulfill_stripe_package_purchase(
    *,
    db: Session,
    org_id: int,
    package_id: str,
    stripe_session_id: str | None,
) -> bool:
    """Mark pending package purchase as paid after Stripe webhook. Returns True if fulfilled."""
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
        # Idempotent: already paid
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

    gu = max(1, int(pending.price_usd or 0) // 100) if int(pending.price_usd or 0) > 0 else 1
    try:
        enforce_plan_limit(org=org, projected_events=0, projected_gu=gu)
    except HTTPException:
        # Still fulfill purchase (money taken); GU overage recorded as soft
        pass
    org.gu_in_period = int(org.gu_in_period) + gu
    pending.gu_charged = gu
    pending.status = "paid"
    if stripe_session_id:
        pending.stripe_session_id = stripe_session_id
    row.downloads = int(row.downloads or 0) + 1
    row.author_revenue_usd = int(row.author_revenue_usd or 0) + int(pending.author_cut_usd or 0)
    row.platform_revenue_usd = int(row.platform_revenue_usd or 0) + int(pending.platform_cut_usd or 0)
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

