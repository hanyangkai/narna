/** NARNA — infrastructure layer. UGS = open governance spec. VAP = trust engine. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Rules Native Architecture",
  letters: ["Neural", "Autonomous", "Rules", "Native", "Architecture"] as const,
  tagline: "The Governance Runtime for Autonomous Intelligence.",
  primary: "Govern Once. Run Anywhere.",
  oneLiner: "NARNA governs AI. Others execute it.",
  mission:
    "Standardize how autonomous AI is identified, governed, verified, and trusted — without replacing existing frameworks.",
  vision:
    "Build the universal governance layer that enables every autonomous system to operate safely, transparently, and across any AI stack.",
  elevator:
    "NARNA is the Universal AI Governance Runtime — portable Identity, Governance, Evidence, Trust, and Certification across every AI stack.",
  contrast:
    "OpenTelemetry records what AI did. NARNA proves what AI was allowed to do.",
  enterprise: "Trust Every Autonomous Decision.",
  technical: "Identity. Governance. Evidence. Trust.",
  community: "Open Governance for the AI Era.",
  category: "Infrastructure layer — peer to Docker, Kubernetes, Git, OpenTelemetry.",
  github: "https://github.com/hanyangkai/narna",
  discord: "https://discord.gg/narna",
  emailEnterprise: "enterprise@narna.ai",
} as const;

/** Open standard (public). Formerly UAP workflow name. */
export const SPEC = {
  name: "UGS",
  expand: "Universal Governance Specification",
  install: "pip install narna",
  sdkPackage: "narna",
  pillars: ["Identity", "Governance", "Evidence", "Trust"] as const,
} as const;

/** @deprecated Use SPEC (UGS). Kept for transitional imports. */
export const PROTOCOL = {
  name: SPEC.name,
  expand: SPEC.expand,
  steps: SPEC.pillars,
  install: SPEC.install,
  sdkPackage: SPEC.sdkPackage,
} as const;

export const TRUST = {
  name: "VAP",
  expand: "Verify · Audit · Prove",
  steps: ["Verify", "Audit", "Prove"] as const,
} as const;

export const POSITIONING = [
  { company: "OpenAI", owns: "Intelligence" },
  { company: "Anthropic", owns: "Safety models" },
  { company: "NVIDIA", owns: "Compute" },
  { company: "Docker", owns: "Containers" },
  { company: "Kubernetes", owns: "Orchestration" },
  { company: "OpenTelemetry", owns: "Observability" },
  { company: "MCP", owns: "Tool protocol" },
  { company: "NARNA", owns: "AI Governance" },
] as const;

export const PRODUCT_FAMILY = [
  "NARNA Runtime",
  "NARNA SDK",
  "NARNA CLI",
  "NARNA Registry",
  "NARNA Identity",
  "NARNA Trust",
  "NARNA Passport",
  "NARNA Policy",
  "NARNA Evidence",
  "NARNA Certification",
  "NARNA Cloud",
  "NARNA Enterprise",
  "UGS Specification",
] as const;

export const COMPATIBILITY = [
  "OpenAI",
  "Anthropic",
  "Google",
  "NVIDIA",
  "MCP",
  "OpenTelemetry",
  "LangGraph",
  "CrewAI",
  "AutoGen",
  "Docker",
  "Kubernetes",
  "OpenShell",
] as const;
