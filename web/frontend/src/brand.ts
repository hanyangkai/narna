/** NARNA — governance infrastructure for Agentic AI. UGS = open spec. VAP = trust engine. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Rules Native Architecture",
  letters: ["Neural", "Autonomous", "Rules", "Native", "Architecture"] as const,
  tagline: "The Governance Infrastructure for Agentic AI.",
  altTagline: "The Universal Governance Layer for Agentic AI.",
  heroTitle: "Build Agentic AI that Enterprises Can Trust",
  heroLead: "One governance layer. Every model. Every framework. Every runtime.",
  heroSub:
    "NARNA provides portable identity, governance, evidence, and trust for autonomous AI systems. Compatible with OpenAI, Anthropic, LangGraph, CrewAI, MCP, and OpenTelemetry.",
  northStar:
    "Every Agentic AI system gets Identity, Governance, and Trust — NARNA governs AI. Others execute it.",
  primary: "Govern Once. Run Anywhere.",
  oneLiner: "NARNA governs AI. Others execute it.",
  mission:
    "Standardize how Agentic AI is identified, governed, verified, and trusted — across multi-agent workflows without replacing existing frameworks.",
  vision:
    "Build the universal governance layer that enables every agentic system — multi-agent, long-running, tool-calling — to operate safely and portably across any AI stack.",
  elevator:
    "NARNA is the Governance Infrastructure for Agentic AI — portable Identity, Governance, Evidence, Trust, and Certification across LangGraph, CrewAI, OpenAI SDK, and every model.",
  contrast:
    "OpenTelemetry records what AI did. NARNA proves what AI was allowed to do.",
  enterprise: "Trust Every Agentic Decision.",
  technical: "Identity. Governance. Evidence. Trust.",
  community: "Open Governance for the Agentic AI Era.",
  category:
    "Governance infrastructure for Agentic AI — peer to Docker, Kubernetes, Git, OpenTelemetry.",
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

export const AGENTIC_TREND = [
  { year: "2023", label: "LLM" },
  { year: "2024", label: "RAG" },
  { year: "2025", label: "AI Agents" },
  { year: "2026+", label: "Agentic AI" },
] as const;

export const AGENTIC_TRAITS = [
  "Multi-Agent",
  "Long-running Tasks",
  "Memory",
  "Planning",
  "Human Approval",
  "Tool Calling",
  "Autonomous Workflow",
] as const;

export const AGENTIC_QUESTIONS = [
  "Which agent is allowed to do what?",
  "Which agent is trustworthy?",
  "Which agent deleted data?",
  "Which agent sent email?",
  "Which agent used GPT-5?",
] as const;

export const ADAPTERS = [
  "narna-langgraph",
  "narna-crewai",
  "narna-autogen",
  "narna-openai",
  "narna-anthropic",
  "narna-semantic-kernel",
] as const;

export const MARKETPLACE_PACKAGES = [
  "Healthcare Package",
  "Finance Package",
  "EU AI Act Package",
  "Banking Package",
  "Startup Package",
] as const;

export const POSITIONING = [
  { company: "OpenAI", owns: "Intelligence" },
  { company: "Anthropic", owns: "Safety models" },
  { company: "NVIDIA", owns: "Compute" },
  { company: "LangGraph", owns: "Agent orchestration" },
  { company: "CrewAI", owns: "Multi-agent crews" },
  { company: "Docker", owns: "Containers" },
  { company: "Kubernetes", owns: "Orchestration" },
  { company: "OpenTelemetry", owns: "Observability" },
  { company: "MCP", owns: "Tool protocol" },
  { company: "NARNA", owns: "Agentic AI Governance" },
] as const;

export const PRODUCT_FAMILY = [
  "NARNA Runtime",
  "NARNA SDK",
  "NARNA CLI",
  "Agent Passport",
  "Governance Package Marketplace",
  "NARNA Registry",
  "NARNA Identity",
  "NARNA Trust",
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
