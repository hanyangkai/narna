from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .auth import get_org_from_api_key
from .billing import now_utc, plan_event_limit, plan_usd_price, reset_if_new_period
from .crypto_bot import start_background_bot
from .crypto_chains import build_pay_uri, list_supported_networks, validate_crypto_payment
from .invoice_utils import build_qr_payload, expire_pending_invoices, invoice_expires_at
from .database import get_db, init_db
from .metrics import METRICS
from .models import (
    ApiKey,
    Organization,
    PaymentInvoice,
    RegistryAgent,
    RegistryPlugin,
    Run,
    RunEvent,
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
    RegistryAgentSummary,
    RegistryPublishRequest,
    RegistryPublishResponse,
    RunDetail,
    RunSummary,
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


@app.get("/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "uap-cloud", "version": "0.1.0"}


def get_billing_mode() -> str:
    return os.environ.get("UAP_BILLING_MODE", "mock").lower()


def enforce_plan_limit(*, org: Organization, projected_events: int) -> None:
    now = now_utc()
    if org.period_start_at is None or reset_if_new_period(
        period_start_at=org.period_start_at, now=now
    ):
        org.period_start_at = now
        org.events_in_period = 0

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
    enforce_plan_limit(org=org, projected_events=len(body.events))

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
    if body.trustScore:
        run.trust_score = body.trustScore.get("score")
    if body.proofBundle:
        run.proof_bundle_json = json.dumps(body.proofBundle)
    run.updated_at = datetime.now(timezone.utc)

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
    METRICS.inc_ingest()
    METRICS.inc_ingest_accepted()
    db.commit()

    return IngestResponse(
        runId=body.runId,
        eventsIngested=ingested,
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
            )
        )
    return out


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
        db.commit()
        return BillingCheckoutResponse(
            ok=True, url="mock://checkout/success", mode="mock"
        )

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
        metadata = session_obj.get("metadata") or {}
        org_id = metadata.get("org_id")
        plan = metadata.get("plan")
        if org_id and plan:
            org = db.query(Organization).filter(Organization.id == int(org_id)).first()
            if org is not None:
                org.plan = str(plan)
                org.period_start_at = now_utc()
                org.events_in_period = 0
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


@app.post("/v1/certification/submit", response_model=CertificationSubmitResponse)
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
            {"id": "uap-compatible", "title": "UAP Compatible", "path": "/badges/uap-compatible.svg"},
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

