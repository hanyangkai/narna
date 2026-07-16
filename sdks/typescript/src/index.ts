/**
 * NARNA TypeScript reference SDK (stub).
 * Never Replace. Always Extend. — Specs are source of truth.
 */

export type Manifest = {
  apiVersion: "narna.ai/v1alpha1";
  kind: "Manifest";
  metadata?: { name?: string; owner?: string };
  identity: { id: string; version?: string };
  capabilities?: string[];
  permissions?: Array<string | { name: string; mode?: string }>;
  policies?: string[];
  trust?: { minimum_score?: number };
  compatibility?: string[];
};

export type CertificationLevel = "L1" | "L2" | "L3" | "none";

export const BADGES = {
  L1: "NARNA Certified",
  L2: "NARNA Certified+",
  L3: "Enterprise Ready",
} as const;

/** Minimal compile: Manifest → Constitution-like object (TS stub). */
export function compileManifest(manifest: Manifest): Record<string, unknown> {
  const entityId = manifest.identity.id.startsWith("agent_")
    ? manifest.identity.id
    : `agent_${manifest.identity.id.replace(/-/g, "_")}`;
  const supports = (manifest.capabilities || ["general"]).map((c) =>
    c.toLowerCase().replace(/[.-]/g, "_")
  );
  return {
    apiVersion: "narna.ai/v1alpha1",
    kind: "Constitution",
    metadata: {
      name: `${manifest.metadata?.name || entityId} Constitution`,
      entityKind: "Agent",
      entityId,
      owner: manifest.metadata?.owner || "local",
      version: manifest.identity.version || "0.1.0",
    },
    spec: {
      identity: {
        id: entityId,
        owner: manifest.metadata?.owner || "local",
        version: manifest.identity.version || "0.1.0",
      },
      capability: { supports },
      trust: {
        algorithm: "vap-trust-v0",
        minScore: manifest.trust?.minimum_score ?? 0.7,
      },
    },
  };
}

export function badgeForLevel(level: CertificationLevel): string | null {
  if (level === "none") return null;
  return BADGES[level];
}

export const VERSION = "0.1.0";
