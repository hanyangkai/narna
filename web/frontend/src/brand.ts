/** NARNA brand — Universal AI Governance Runtime. UAP = protocol. VAP = trust engine. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Rules Native Architecture",
  // R = Rules (constitution). Governance Runtime is the USP — not agent executor.
  letters: ["Neural", "Autonomous", "Rules", "Native", "Architecture"] as const,
  tagline: "The Governance Runtime for Autonomous AI.",
  mission:
    "Load, enforce, and prove Governance Packages — constitutions, compliance, and org policy — above any model or framework.",
  elevator:
    "NARNA is the Governance Runtime for Autonomous AI — portable Governance Packages that load, enforce, and prove across any model or agent framework.",
  contrast:
    "OpenTelemetry records what AI did. NARNA proves what AI was allowed to do.",
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
  "NARNA Governance Runtime",
  "NARNA Constitution Runtime",
  "NARNA Governance Packages",
  "NARNA Constitution Marketplace",
  "NARNA Identity",
  "NARNA Passport",
  "NARNA Evidence / VAP",
  "NARNA Certification",
  "NARNA Registry",
  "NARNA Fleet Governance",
  "NARNA Cloud",
  "NARNA SDK",
  "UAP Specification",
] as const;
