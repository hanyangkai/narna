from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    agentId: str
    agentName: str = ""
    runId: str
    state: str = "Unknown"
    tipHash: str = ""
    sessionId: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    proofBundle: dict[str, Any] | None = None
    trustScore: dict[str, Any] | None = None


class IngestResponse(BaseModel):
    ok: bool = True
    runId: str
    eventsIngested: int
    guIngested: int = 0
    sessionId: str | None = None
    url: str


class RunSummary(BaseModel):
    runId: str
    agentId: str
    agentName: str
    state: str
    tipHash: str
    trustScore: float | None
    eventCount: int
    updatedAt: str
    sessionId: str | None = None
    totalGu: int = 0


class RunDetail(RunSummary):
    events: list[dict[str, Any]]
    proofBundle: dict[str, Any] | None = None


class SessionSummary(BaseModel):
    sessionId: str
    logicalAgentId: str
    state: str
    totalGu: int
    runCount: int = 0
    createdAt: str
    closedAt: str | None = None
    terminateReason: str | None = None


class SessionDetail(SessionSummary):
    graph: dict[str, Any] = Field(default_factory=dict)
    runs: list[RunSummary] = Field(default_factory=list)
    units: list[dict[str, Any]] = Field(default_factory=list)


class ApiKeyResponse(BaseModel):
    apiKey: str
    prefix: str
    label: str
    message: str


class BillingCheckoutRequest(BaseModel):
    plan: str


class BillingCheckoutResponse(BaseModel):
    ok: bool = True
    url: str
    mode: str


class BillingMockSetPlanRequest(BaseModel):
    plan: str


class BillingStatusResponse(BaseModel):
    plan: str
    periodStartAt: str
    eventsInPeriod: int
    eventsLimit: int | None
    guInPeriod: int = 0
    guLimit: int | None = None
    billingMode: str


class BillingCryptoCheckoutRequest(BaseModel):
    plan: str
    asset: str = "usdc"  # expected: usdc | usdt
    network: str = "ethereum"


class BillingCryptoCheckoutResponse(BaseModel):
    ok: bool = True
    url: str
    mode: str
    invoiceId: str
    plan: str
    asset: str
    network: str
    recipientWallet: str
    expectedAmount: str
    expiresAt: str
    qrPayload: str


class BillingInvoiceResponse(BaseModel):
    invoiceId: str
    kind: str
    plan: str
    asset: str
    network: str
    recipientWallet: str
    expectedAmount: str
    status: str
    txHash: str | None = None
    createdAt: str
    expiresAt: str | None = None
    paidAt: str | None = None


class BillingCryptoNetworkResponse(BaseModel):
    id: str
    name: str
    chainId: int
    assets: list[str]
    rpcConfigured: bool


class RegistryPublishRequest(BaseModel):
    agentId: str
    name: str
    version: str = "0.1.0"
    creator: str = "local"
    capabilities: list[str] = Field(default_factory=list)
    category: str = "general"
    trustScore: float | None = None
    stars: int = 0
    downloads: int = 0
    executions: int = 0
    passport: dict[str, Any] | None = None
    identity: dict[str, Any] | None = None


class RegistryAgentSummary(BaseModel):
    agentId: str
    name: str
    version: str
    creator: str
    category: str
    capabilities: list[str]
    trustScore: float | None = None
    stars: int = 0
    downloads: int = 0
    executions: int = 0
    publishedAt: str
    passportUrl: str
    verified: bool = False
    badge: str | None = None
    level: str | None = None
    levelLabel: str | None = None


class RegistryPublishResponse(BaseModel):
    ok: bool = True
    agentId: str
    passportUrl: str
    registryUrl: str
    status: str = "published"


class CertificationSubmitRequest(BaseModel):
    agentId: str
    certificationId: str
    status: str
    level: str | None = None
    targetLevel: str | None = None
    badge: str | None = None
    levelLabel: str | None = None
    algorithm: str = "narna-cert-v1"
    issuedAt: str
    expiresAt: str | None = None
    trustScore: float | None = None
    checks: list[dict[str, Any]] | None = None
    runId: str | None = None
    proofHash: str | None = None
    passportHash: str | None = None
    constitutionId: str | None = None
    constitutionHash: str | None = None


class CertificationSubmitResponse(BaseModel):
    ok: bool = True
    agentId: str
    verified: bool
    badge: str | None = None
    level: str | None = None
    levelLabel: str | None = None
    passportUrl: str
    status: str


class PluginPublishRequest(BaseModel):
    pluginId: str
    name: str
    version: str = "0.1.0"
    license: str = "MIT"
    spec: dict[str, Any] = Field(default_factory=dict)
    stars: int = 0
    downloads: int = 0


class PluginSummary(BaseModel):
    pluginId: str
    name: str
    version: str
    license: str
    spec: dict[str, Any] = Field(default_factory=dict)
    stars: int = 0
    downloads: int = 0
    publishedAt: str


class PluginPublishResponse(BaseModel):
    ok: bool = True
    pluginId: str
    status: str = "published"
    registryUrl: str


class PackagePublishRequest(BaseModel):
    packageId: str
    name: str
    version: str = "0.1.0"
    provider: str = "local"
    packageKind: str = "Compliance"
    license: str = "MIT"
    disclaimer: str = ""
    spec: dict[str, Any] = Field(default_factory=dict)
    packageHash: str | None = None
    priceUsd: int = 0
    takeRateBps: int = 2000
    stars: int = 0
    downloads: int = 0


class PackageSummary(BaseModel):
    packageId: str
    name: str
    version: str
    provider: str
    packageKind: str
    license: str
    disclaimer: str = ""
    packageHash: str = ""
    spec: dict[str, Any] = Field(default_factory=dict)
    priceUsd: int = 0
    takeRateBps: int = 2000
    authorRevenueUsd: int = 0
    platformRevenueUsd: int = 0
    stars: int = 0
    downloads: int = 0
    publishedAt: str


class PackagePublishResponse(BaseModel):
    ok: bool = True
    packageId: str
    status: str = "published"
    registryUrl: str


class PackagePurchaseRequest(BaseModel):
    packageId: str


class PackagePurchaseResponse(BaseModel):
    ok: bool = True
    packageId: str
    priceUsd: int
    takeRateBps: int
    platformCutUsd: int
    authorCutUsd: int
    guCharged: int
    status: str = "paid"  # pending | paid | free | mock
    mode: str = "mock"  # mock | stripe | free
    checkoutUrl: str | None = None
    message: str = "Purchase recorded"


class TelemetryConsentRequest(BaseModel):
    telemetryOptIn: bool = False
    trainOptIn: bool = False


class TelemetryConsentResponse(BaseModel):
    ok: bool = True
    telemetryOptIn: bool
    trainOptIn: bool
    message: str = "Consent updated"


class TelemetryContributeRequest(BaseModel):
    """Accepts either a prebuilt contribution or raw events to sanitize server-side."""

    contribution: dict[str, Any] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    agentId: str = ""
    agentName: str = ""
    trustScore: float | None = None
    runId: str | None = None


class TelemetryContributeResponse(BaseModel):
    ok: bool = True
    contributionId: int
    nodeCount: int
    guTotal: int
    message: str = "Contribution accepted"


class TelemetryAggregateRow(BaseModel):
    agentClass: str
    capabilityFamily: str
    humanApprovalRate: float
    denyRate: float
    loopFailureRate: float
    avgGu: float
    tenantCount: int
    sampleNodes: int


class TelemetryAggregateResponse(BaseModel):
    ok: bool = True
    k: int = 5
    rows: list[TelemetryAggregateRow] = Field(default_factory=list)
    description: str = (
        "k-anonymous Governance Intelligence aggregates — no prompts, no tenant IDs."
    )