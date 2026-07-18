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
    "Portable UGS identity, Governance Packages (EU AI Act, HIPAA…), evidence, and GU metering — across OpenAI, Anthropic, LangGraph, CrewAI, MCP, and OpenTelemetry.",
  northStar:
    "Every Agentic AI system gets Identity, Governance, and Trust — NARNA governs AI. Others execute it.",
  primary: "Govern Once. Run Anywhere.",
  oneLiner: "NARNA governs AI. Others execute it.",
  mission:
    "Standardize how Agentic AI is identified, governed, verified, and trusted — across multi-agent workflows without replacing existing frameworks.",
  vision:
    "Build the universal governance layer that enables every agentic system — multi-agent, long-running, tool-calling — to operate safely and portably across any AI stack.",
  elevator:
    "NARNA is compliance & trust infrastructure for Agentic AI — UGS, Governance Packages, and GU metering. Others execute agents; NARNA makes fleets governable.",
  contrast:
    "OpenTelemetry records what AI did. Identity-only passports prove who signed. NARNA proves what was allowed — with portable compliance packages.",
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
  "narna-moltbook",
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
  "UGS Passport",
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

/** Pricing — governance assets, not events. See docs/BUSINESS-MODEL.md */
export const PRICING = {
  tagline: "Runtime is free. Trust is the product.",
  subline:
    "Like Docker: OSS engine is open. NARNA Cloud sells Registry, Passport, Verification, and Compliance.",
  philosophy: "Trust as a Service — metered by Governance Units (GU)",
  unit: "GU",
  plans: [
    {
      id: "developer",
      name: "Developer",
      price: "Free",
      period: "",
      limit: "Unlimited local runtime",
      retention: "Local only",
      features: [
        "OSS SDK + CLI",
        "Local GU metering + Governor",
        "Community registry",
        "No account required",
      ],
      cta: "Get Started",
      ctaTo: "/docs/install",
      featured: false,
    },
    {
      id: "pro",
      name: "Cloud Pro",
      price: "$19",
      period: "/mo",
      limit: "100,000 GU / month",
      retention: "90-day history",
      features: [
        "Private registry",
        "Agent Passport + verification API",
        "Governor + Cost Guard",
        "Governance dashboard",
      ],
      cta: "Subscribe",
      ctaTo: "/billing",
      featured: true,
    },
    {
      id: "team",
      name: "Cloud Team",
      price: "$49",
      period: "/mo",
      limit: "500,000 GU / month",
      retention: "365-day history",
      features: [
        "Organization + shared registry",
        "RBAC + Evidence Center",
        "Loop & recursion detection",
        "Priority support",
      ],
      cta: "Subscribe",
      ctaTo: "/billing",
      featured: false,
    },
    {
      id: "enterprise",
      name: "Enterprise",
      price: "Contact",
      period: "",
      limit: "Unlimited GU",
      retention: "Custom",
      features: ["SSO", "SOC2", "On-prem", "Compliance packages", "Dedicated support"],
      cta: "Contact",
      ctaTo: "/enterprise",
      featured: false,
    },
  ],
  revenueStreams: [
    "Cloud subscription",
    "Private registry",
    "Passport Verification API",
    "Certification",
    "Governance Package Marketplace (20% take)",
    "Enterprise support",
  ],
} as const;
