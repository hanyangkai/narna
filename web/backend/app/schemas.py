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
    cryptoMode: str = "mock"
    mockPlanAllowed: bool = False
    planExpiresAt: str | None = None
    adqaChecksInPeriod: int = 0
    adqaSoftCap: int | None = None
    adqaHardCap: int | None = None
    agentTurnsInPeriod: int = 0
    agentTurnsHardCap: int | None = None
    seatCount: int = 1
    byoLlmAllowed: bool = False


class AgentAskRequest(BaseModel):
    message: str
    sessionId: str | None = None
    challenge: bool = False
    files: list[dict[str, Any]] = Field(default_factory=list)
    # Hermes-style BYOK — optional per-request LLM (never stored unless /models)
    llmProvider: str | None = None
    llmApiKey: str | None = None
    llmBaseUrl: str | None = None
    llmModel: str | None = None
    # cheap | quality | critical — multi-model consensus (NGS-0028 modes)
    mode: str | None = None


class AgentOutcomeRequest(BaseModel):
    decisionId: str
    status: str = "success"
    detail: str | None = None
    successScore: float | None = None
    lesson: str | None = None
    skillId: str | None = None


class AgentJobCreateRequest(BaseModel):
    prompt: str
    everyMinutes: int | None = None
    runAt: str | None = None
    enabled: bool = True
    # Hermes-like NL: "every day remind me to …" / "in 10 minutes …"
    schedule: str | None = None
    channel: str | None = None
    deliverTo: str | None = None


class AgentSkillHubPublishRequest(BaseModel):
    name: str
    body: str
    tags: list[str] = Field(default_factory=list)
    author: str | None = None


class AgentSkillHubInstallRequest(BaseModel):
    skillId: str


class AgentSkillHubSyncRequest(BaseModel):
    url: str | None = None


class AgentSkillMarkdownImportRequest(BaseModel):
    markdown: str


class AgentModelsPutRequest(BaseModel):
    provider: str = "openrouter"  # openrouter|openai|ollama|mock
    apiKey: str | None = None
    baseUrl: str | None = None
    modelCheap: str | None = None
    modelReason: str | None = None
    modelChallenge: str | None = None


class RouterCompleteRequest(BaseModel):
    messages: list[dict[str, str]]
    task: str = "reason"
    temperature: float = 0.2
    maxTokens: int = 1024


class BillingCryptoCheckoutRequest(BaseModel):
    plan: str
    asset: str = "usdc"  # expected: usdc | usdt
    network: str = "ethereum"
    seats: int | None = None  # team: 3–50


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
    seatCount: int = 1


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
    seatCount: int = 1


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