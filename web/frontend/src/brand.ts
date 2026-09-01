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

/** Pricing — Desktop free forever; Pro = Cloud Brain */
export const PRICING = {
  tagline: "Desktop agent free forever. Pro is your cloud brain.",
  subline:
    "Full agent on Mac/Windows — unlimited, BYOK, no account. Pro adds backup, sync, hosted MCP, and always-on cloud.",
  philosophy: "Local agent free. Pro unlocks connectivity — not features removed from Desktop.",
  unit: "agent turns",
  freeFirst: true,
  plans: [
    {
      id: "free",
      name: "Free",
      price: "$0",
      period: "",
      limit: "Desktop unlimited · Cloud 200 Ask/mo",
      retention: "Local ~/.narna · forever",
      features: [
        "Full Desktop agent (Mac + Windows)",
        "All tools · ADQA · Decision Memory · BYOK",
        "Cloud Ask (200 turns/mo)",
        "Hosted MCP (100 ADQA/mo)",
      ],
      cta: "Download free",
      ctaTo: "/download",
      featured: true,
    },
    {
      id: "cloud",
      name: "Pro",
      price: "$20",
      period: "/mo",
      limit: "USDC / USDT · 5 EVM chains",
      retention: "Cloud backup · 1yr traces · multi-device",
      features: [
        "Cloud Memory Backup & sync (Desktop ↔ cloud)",
        "Hosted MCP — Cursor / Claude Code ADQA",
        "Quality & Critical modes on web Ask",
        "Recurring cloud jobs · always-on channels",
        "20k Ask turns/mo · 10k ADQA/mo",
      ],
      cta: "Pay with USDC",
      ctaTo: "/checkout",
      featured: false,
      comingSoon: false,
    },
    {
      id: "team",
      name: "Team",
      price: "Soon",
      period: "",
      limit: "Enterprise / multi-seat — later",
      retention: "Shared Decision Brain (roadmap)",
      features: [
        "Shared policies",
        "Team memory",
        "Agent governance",
        "Talk to us for early access",
      ],
      cta: "Contact",
      ctaTo: "/enterprise",
      featured: false,
      comingSoon: true,
    },
  ],
  enterpriseNote: "Enterprise — private deployment · SSO · audit · SLA — contact when ready.",
  whyUpgrade: [
    "Desktop stays free: full agent, unlimited local use, BYOK — no license ever.",
    "Pro = Cloud Brain: backup ~/.narna, sync phone + PC, hosted MCP for your IDE.",
    "Pro unlocks Quality/Critical on web Ask, recurring cloud jobs, always-on Telegram/Discord.",
    "Free cloud: 200 Ask turns/mo. Pro: 20k turns, 30 sync backups/mo, 1yr trace history.",
  ],
  revenueStreams: [
    "Pro ($20/mo crypto)",
    "Team seats (later)",
    "Enterprise Decision Runtime",
    "Decision Package Marketplace",
  ],
} as const;
