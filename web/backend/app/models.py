from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(32), default="free")
    # Billing enforcement (monthly, simplified)
    period_start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    events_in_period: Mapped[int] = mapped_column(Integer, default=0)
    gu_in_period: Mapped[int] = mapped_column(Integer, default=0)
    # Stripe optional (for P6 integration)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    stripe_subscription_status: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    # Privacy-preserving Governance Telemetry (default OFF)
    telemetry_opt_in: Mapped[int] = mapped_column(Integer, default=0)  # 0/1
    train_opt_in: Mapped[int] = mapped_column(Integer, default=0)  # 0/1
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="organization")
    runs: Mapped[list["Run"]] = relationship(back_populates="organization")
    invoices: Mapped[list["PaymentInvoice"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    key_prefix: Mapped[str] = mapped_column(String(16))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    label: Mapped[str] = mapped_column(String(128), default="default")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="api_keys")


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (UniqueConstraint("org_id", "run_id", name="uq_org_run"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_name: Mapped[str] = mapped_column(String(255), default="")
    state: Mapped[str] = mapped_column(String(32), default="Unknown")
    tip_hash: Mapped[str] = mapped_column(String(80), default="")
    trust_score: Mapped[float | None] = mapped_column(nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    total_gu: Mapped[int] = mapped_column(Integer, default=0)
    proof_bundle_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="runs")
    events: Mapped[list["RunEvent"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class RunEvent(Base):
    __tablename__ = "run_events"
    __table_args__ = (UniqueConstraint("run_pk", "event_id", name="uq_run_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_pk: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    event_id: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(64))
    sequence: Mapped[int] = mapped_column(Integer)
    ts: Mapped[str] = mapped_column(String(40))
    payload_json: Mapped[str] = mapped_column(Text)
    event_hash: Mapped[str] = mapped_column(String(80), default="")

    run: Mapped["Run"] = relationship(back_populates="events")


class PaymentInvoice(Base):
    __tablename__ = "payment_invoices"
    __table_args__ = (
        UniqueConstraint("org_id", "invoice_id", name="uq_org_invoice"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    invoice_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="crypto")  # crypto|card
    plan: Mapped[str] = mapped_column(String(32), default="free")
    asset: Mapped[str] = mapped_column(String(16), default="usdc")
    network: Mapped[str] = mapped_column(String(32), default="ethereum")
    recipient_wallet: Mapped[str] = mapped_column(String(64), default="")
    expected_amount: Mapped[str] = mapped_column(String(40), default="0")
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|paid|expired|failed
    tx_hash: Mapped[str | None] = mapped_column(String(80), nullable=True)
    block_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship(back_populates="invoices")


class RegistryAgent(Base):
    """Public Agent Registry listing (Phase 3)."""

    __tablename__ = "registry_agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    version: Mapped[str] = mapped_column(String(64), default="0.1.0")
    creator: Mapped[str] = mapped_column(String(255), default="local")
    category: Mapped[str] = mapped_column(String(64), default="general", index=True)
    capabilities_json: Mapped[str] = mapped_column(Text, default="[]")
    trust_score: Mapped[float | None] = mapped_column(nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    executions: Mapped[int] = mapped_column(Integer, default=0)
    passport_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    identity_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    certification_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified: Mapped[int] = mapped_column(Integer, default=0)  # 0|1
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class RegistryPlugin(Base):
    """Community plugin listing."""

    __tablename__ = "registry_plugins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plugin_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    version: Mapped[str] = mapped_column(String(64), default="0.1.0")
    license: Mapped[str] = mapped_column(String(64), default="MIT")
    spec_json: Mapped[str] = mapped_column(Text, default="{}")
    stars: Mapped[int] = mapped_column(Integer, default=0)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class RegistryGovernancePackage(Base):
    """Governance Package marketplace listing."""

    __tablename__ = "registry_governance_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    version: Mapped[str] = mapped_column(String(64), default="0.1.0")
    provider: Mapped[str] = mapped_column(String(128), default="local", index=True)
    package_kind: Mapped[str] = mapped_column(String(64), default="Compliance")
    license: Mapped[str] = mapped_column(String(64), default="MIT")
    disclaimer: Mapped[str] = mapped_column(Text, default="")
    package_hash: Mapped[str] = mapped_column(String(128), default="")
    spec_json: Mapped[str] = mapped_column(Text, default="{}")
    price_usd: Mapped[int] = mapped_column(Integer, default=0)  # cents; 0 = free
    take_rate_bps: Mapped[int] = mapped_column(Integer, default=2000)  # 20% = 2000 bps
    author_revenue_usd: Mapped[int] = mapped_column(Integer, default=0)
    platform_revenue_usd: Mapped[int] = mapped_column(Integer, default=0)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    downloads: Mapped[int] = mapped_column(Integer, default=0)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class GovernanceSessionRow(Base):
    """Cloud-side Governance Session for Console graph view."""

    __tablename__ = "governance_sessions"
    __table_args__ = (UniqueConstraint("org_id", "session_id", name="uq_org_session"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    logical_agent_id: Mapped[str] = mapped_column(String(128), default="")
    state: Mapped[str] = mapped_column(String(32), default="open")
    total_gu: Mapped[int] = mapped_column(Integer, default=0)
    graph_json: Mapped[str] = mapped_column(Text, default="{}")
    terminate_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketplacePurchase(Base):
    """Governance Package purchase with NARNA take-rate split."""

    __tablename__ = "marketplace_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    package_id: Mapped[str] = mapped_column(String(128), index=True)
    price_usd: Mapped[int] = mapped_column(Integer, default=0)
    take_rate_bps: Mapped[int] = mapped_column(Integer, default=2000)
    platform_cut_usd: Mapped[int] = mapped_column(Integer, default=0)
    author_cut_usd: Mapped[int] = mapped_column(Integer, default=0)
    gu_charged: Mapped[int] = mapped_column(Integer, default=0)
    # pending | paid | free | mock
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TelemetryContribution(Base):
    """Sanitized, hashed Governance Telemetry contribution (no prompts / PII)."""

    __tablename__ = "telemetry_contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), index=True)
    tenant_hash: Mapped[str] = mapped_column(String(64), index=True)
    session_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    train_opt_in: Mapped[int] = mapped_column(Integer, default=0)
    nodes_json: Mapped[str] = mapped_column(Text, default="[]")
    edges_json: Mapped[str] = mapped_column(Text, default="[]")
    totals_json: Mapped[str] = mapped_column(Text, default="{}")
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    gu_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


def generate_api_key() -> tuple[str, str, str]:
    """Returns (full_key, prefix, sha256_hex_hash)."""
    import hashlib

    token = secrets.token_urlsafe(32)
    full = f"uap_live_{token}"
    prefix = full[:16]
    key_hash = hashlib.sha256(full.encode()).hexdigest()
    return full, prefix, key_hash
