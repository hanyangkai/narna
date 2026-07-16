/** NARNA brand — Constitution Layer. UAP = protocol. VAP = trust engine. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Rules Native Architecture",
  // R = Rules (constitution). Second N = Native (protocol-native) — not Network.
  letters: ["Neural", "Autonomous", "Rules", "Native", "Architecture"] as const,
  tagline: "The Constitution Layer for Autonomous AI.",
  mission:
    "Define who autonomous AI is, what it may do, and why others can trust it — above any model or framework.",
  elevator:
    "NARNA is the Constitution Layer for Autonomous AI — portable identity, policy, evidence, trust, passport, and certification across any model or agent framework.",
  contrast:
    "OpenTelemetry records what AI did. NARNA defines who AI is, what it is allowed to do, and why others can trust it.",
  github: "https://github.com/hanyangkai/narna",
  discord: "https://discord.gg/narna",
  emailEnterprise: "enterprise@narna.ai",
} as const;

export const PROTOCOL = {
  name: "UAP",
  expand: "Understand · Act · Prove",
  steps: ["Understand", "Act", "Prove"] as const,
  install: "pip install narna",
  sdkPackage: "narna",
} as const;

export const TRUST = {
  name: "VAP",
  expand: "Verify · Audit · Prove",
  steps: ["Verify", "Audit", "Prove"] as const,
} as const;

export const PRODUCT_FAMILY = [
  "NARNA Constitution",
  "NARNA Identity",
  "NARNA Passport",
  "NARNA Policy",
  "NARNA Evidence / VAP",
  "NARNA Certification",
  "NARNA Registry",
  "NARNA Governance",
  "NARNA Cloud",
  "NARNA SDK",
  "UAP Specification",
] as const;
