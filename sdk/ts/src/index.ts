/**
 * @narna/client — thin TypeScript client for NARNA Cloud Governance API
 * OpenAPI: specs/governance-api/openapi.yaml
 */

export type NarnaClientOptions = {
  baseUrl?: string;
  apiKey?: string;
};

export class NarnaClient {
  readonly baseUrl: string;
  readonly apiKey?: string;

  constructor(opts: NarnaClientOptions = {}) {
    this.baseUrl = (opts.baseUrl || "https://api.narna.org").replace(/\/$/, "");
    this.apiKey = opts.apiKey;
  }

  private headers(): HeadersInit {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (this.apiKey) h["Authorization"] = `Bearer ${this.apiKey}`;
    return h;
  }

  async health(): Promise<{ status: string; service: string }> {
    const res = await fetch(`${this.baseUrl}/v1/health`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async getPassport(agentId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/v1/passport/${encodeURIComponent(agentId)}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async verifyPassport(agentId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/v1/passport/${encodeURIComponent(agentId)}/verify`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async listPackages(q?: string): Promise<unknown[]> {
    const params = q ? `?q=${encodeURIComponent(q)}` : "";
    const res = await fetch(`${this.baseUrl}/v1/packages${params}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async purchasePackage(packageId: string): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/v1/packages/purchase`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ packageId }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async ingest(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/v1/ingest`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async telemetryConsent(telemetryOptIn: boolean, trainOptIn = false): Promise<Record<string, unknown>> {
    const res = await fetch(`${this.baseUrl}/v1/telemetry/consent`, {
      method: "POST",
      headers: this.headers(),
      body: JSON.stringify({ telemetryOptIn, trainOptIn }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
}

export default NarnaClient;
