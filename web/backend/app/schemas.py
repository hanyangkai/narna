from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    agentId: str
    agentName: str = ""
    runId: str
    state: str = "Unknown"
    tipHash: str = ""
    events: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    proofBundle: dict[str, Any] | None = None
    trustScore: dict[str, Any] | None = None


class IngestResponse(BaseModel):
    ok: bool = True
    runId: str
    eventsIngested: int
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


class RunDetail(RunSummary):
    events: list[dict[str, Any]]
    proofBundle: dict[str, Any] | None = None


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
    badge: str | None = None
    algorithm: str = "narna-cert-v0"
    issuedAt: str
    expiresAt: str | None = None
    trustScore: float | None = None
    checks: list[dict[str, Any]] | None = None
    runId: str | None = None
    proofHash: str | None = None
    passportHash: str | None = None


class CertificationSubmitResponse(BaseModel):
    ok: bool = True
    agentId: str
    verified: bool
    badge: str | None = None
    passportUrl: str
    status: str
