/** NARNA brand — company. UAP = protocol. VAP = trust engine. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Runtime Architecture",
  // Second N read as Native (protocol-native contracts) — not Network.
  letters: ["Neural", "Autonomous", "Runtime", "Native", "Architecture"] as const,
  tagline: "The Open Runtime for Trusted AI Agents.",
  mission:
    "Build the open infrastructure that enables every AI Agent to operate safely, transparently, and verifiably.",
  elevator:
    "NARNA is an open runtime and trust layer for AI Agents. It provides identity, permissions, policies, execution tracing, evidence, and verification — on top of any LLM.",
  github: "https://github.com/narna-ai/narna",
  discord: "https://discord.gg/narna",
  emailEnterprise: "enterprise@narna.ai",
} as const;

export const PROTOCOL = {
  name: "UAP",
  expand: "Understand · Act · Prove",
  steps: ["Understand", "Act", "Prove"] as const,
  install: "pip install uap",
  sdkPackage: "uap",
} as const;

export const TRUST = {
  name: "VAP",
  expand: "Verify · Audit · Prove",
  steps: ["Verify", "Audit", "Prove"] as const,
} as const;

export const PRODUCT_FAMILY = [
  "NARNA SDK",
  "NARNA Runtime",
  "NARNA Identity",
  "NARNA Passport",
  "NARNA Policy",
  "NARNA Registry",
  "NARNA Cloud",
  "NARNA Enterprise",
  "UAP Specification",
  "VAP Engine",
] as const;
