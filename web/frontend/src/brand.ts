/** NARNA — Better decisions for AI agents. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Rules Native Architecture",
  letters: ["Neural", "Autonomous", "Rules", "Native", "Architecture"] as const,
  /** Public category */
  tagline: "AI Agents can act. NARNA makes them decide better.",
  categoryFull: "Decision Quality Infrastructure for AI Agents",
  productCore: "ADQA",
  productCoreExpand: "Autonomous Decision Quality Assurance",
  altTagline: "NARNA Agent — better decisions. NARNA ADQA — for any agent.",
  heroTitle: "NARNA",
  heroLead: "AI Agents can act. NARNA makes them decide better.",
  heroSub:
    "Open-source AI Agent and Decision Quality Assurance infrastructure that helps agents reason, verify, evaluate risk, and learn from outcomes.",
  northStar:
    "Every autonomous decision is evidence-based, policy-compliant, risk-aware, and human-aligned.",
  primary: "Sell better decisions. Agent is the door. ADQA is the difference.",
  oneLiner:
    "NARNA is an AI Agent that can quality-check its own decisions — and ADQA can protect other agents too.",
  mission:
    "Make Decision Quality the standard for AI agents — the way CI became the standard for shipping code.",
  vision:
    "Make ADQA the quality standard for autonomous decisions — the way SSL became the security standard for the Internet.",
  elevator:
    "NARNA Agent does the work. NARNA ADQA scores whether the decision was good enough to act on. Decision Memory compounds lessons. Use NARNA Agent — or bring your own.",
  contrast:
    "Other agents optimize for tool count. NARNA optimizes for decision quality.",
  cognitive: "Think → Verify → Decide → Learn.",
  adqa: "Autonomous Decision Quality Assurance — wrap any agent.",
  decisionIntelligence: "Decision Intelligence — DQS is the KPI.",
  enterprise: "Trust Every Agentic Decision.",
  decisionOs: "Connect data. Score decisions. Keep humans in control.",
  guardian: "Decision Guardian: ACT · REVIEW · REJECT.",
  technical:
    "Evidence. Policy. Context. Memory. Risk. Alignment. Capability. Compliance. Confidence. Explanation.",
  community: "Open quality standard for autonomous decisions.",
  category: "AI Agent + ADQA + Decision Memory — Trace · Replay · Learn.",
  closing:
    "The next generation of AI won't just act. It will know when it should.",
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

export const ADQA_ATTRIBUTES = [
  "Evidence",
  "Policy",
  "Context",
  "Memory",
  "Risk",
  "Alignment",
  "Capability",
  "Compliance",
  "Confidence",
  "Explanation",
] as const;

export const AGENTIC_TREND = [
  { year: "2023", label: "LLM" },
  { year: "2024", label: "RAG" },
  { year: "2025", label: "AI Agents" },
  { year: "2026+", label: "Decision Quality" },
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
  "Is this decision evidence-based?",
  "What is the DQS?",
  "Who may approve?",
  "What is the risk?",
  "Who is accountable?",
] as const;

export const ADAPTERS = [
  "narna-openai",
  "narna-anthropic",
  "narna-google",
  "narna-langgraph",
  "narna-crewai",
  "narna-autogen",
  "narna-semantic-kernel",
  "narna-llamaindex",
  "narna-mcp",
  "narna-cmem",
  "narna-moltbook",
  "narna-opentelemetry",
] as const;

export const MARKETPLACE_PACKAGES = [
  "Legal Decision Package",
  "Procurement Decision Package",
  "Finance Decision Package",
  "Healthcare Package",
  "EU AI Act Package",
  "Banking Package",
] as const;

export const POSITIONING = [
  { company: "OpenAI", owns: "Intelligence" },
  { company: "Anthropic", owns: "Safety models" },
  { company: "NVIDIA", owns: "Compute" },
  { company: "LangGraph", owns: "Agent orchestration" },
  { company: "CrewAI", owns: "Multi-agent crews" },
  { company: "n8n", owns: "Workflow automation" },
  { company: "Docker", owns: "Containers" },
  { company: "Kubernetes", owns: "Orchestration" },
  { company: "OpenTelemetry", owns: "Observability" },
  { company: "MCP", owns: "Tool protocol" },
  { company: "NARNA", owns: "Decision Quality (ADQA)" },
] as const;

export const PRODUCT_FAMILY = [
  "ADQA Core (DQS)",
  "Decision Guardian",
  "Decision OS",
  "Decision Packages",
  "NARNA Runtime",
  "NARNA SDK / CLI",
  "Guardian Network",
  "UGS Passport",
  "NARNA Cloud",
  "NARNA Enterprise",
] as const;

export const COMPATIBILITY = [
  "OpenAI",
  "Anthropic",
  "Google",
  "LangGraph",
  "CrewAI",
  "AutoGen",
  "Semantic Kernel",
  "LlamaIndex",
  "MCP",
  "CMEM",
  "OpenTelemetry",
  "OpenClaw",
  "Docker",
  "Kubernetes",
] as const;

/** Pricing — Free · Pro · Team · Enterprise. See docs/NARNA-MARKET-PLAN.md */
export const PRICING = {
  tagline: "Start free. Scale decision quality when you need it.",
  subline: "For everyone. Upgrade for advanced ADQA, Decision Replay, and team governance.",
  philosophy: "Agent is distribution. ADQA + Trace + Replay is the moat.",
  unit: "agent turns",
  plans: [
    {
      id: "free",
      name: "Free",
      price: "$0",
      period: "",
      limit: "For everyone",
      retention: "Local MEMORY.md · Decision Traces",
      features: [
        "NARNA Agent",
        "Basic ADQA",
        "Memory",
        "Limited cloud usage",
      ],
      cta: "Try free",
      ctaTo: "/ask",
      featured: false,
    },
    {
      id: "cloud",
      name: "Pro",
      price: "$19",
      period: "/mo",
      limit: "Cancel anytime · USDC/USDT",
      retention: "Cloud Decision Memory + Trace history",
      features: [
        "Advanced ADQA",
        "Decision Replay",
        "More memory",
        "Multi-model · more usage",
      ],
      cta: "Get Pro",
      ctaTo: "/billing",
      featured: true,
    },
    {
      id: "team",
      name: "Team",
      price: "$99+",
      period: "/mo",
      limit: "Shared policies & analytics",
      retention: "Shared Decision Brain",
      features: [
        "Shared policies",
        "Team memory",
        "Agent governance",
        "Decision analytics",
      ],
      cta: "Talk to us",
      ctaTo: "/enterprise",
      featured: false,
    },
  ],
  enterpriseNote: "Enterprise — private deployment · SSO · audit · SLA — custom.",
  revenueStreams: [
    "Pro ($19/mo)",
    "Team seats",
    "Enterprise Decision Runtime",
    "Decision Package Marketplace",
  ],
} as const;
