/** NARNA — Decision Quality Infrastructure. ADQA = Autonomous Decision Quality Assurance. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Rules Native Architecture",
  letters: ["Neural", "Autonomous", "Rules", "Native", "Architecture"] as const,
  /** Public category */
  tagline: "The Trust Layer for AI Decisions.",
  categoryFull: "Decision Quality Infrastructure for AI Agents",
  productCore: "ADQA",
  productCoreExpand: "Autonomous Decision Quality Assurance",
  altTagline: "Decision Quality Infrastructure for autonomous systems.",
  heroTitle: "NARNA",
  heroLead: "The Trust Layer for AI Decisions.",
  heroSub:
    "NARNA does not create decisions — it assures their quality and learns from outcomes. Memory layers remember; NARNA scores decisions (DQS) and compounds lessons over time.",
  northStar:
    "Every autonomous decision is evidence-based, policy-compliant, risk-aware, and human-aligned.",
  primary: "Govern Once. Run Anywhere.",
  oneLiner: "NARNA is the Decision Quality Infrastructure for AI Agents.",
  mission:
    "Assure the quality of every consequential AI decision — agents, models, robots, and enterprise decision engines.",
  vision:
    "Make ADQA the quality standard for autonomous decisions — the way SSL became the security standard for the Internet.",
  elevator:
    "Like CI for code and Stripe for payments, NARNA is ADQA for AI decisions — and Decision Memory so agents learn from outcomes, not only recall events. Complements memory layers (e.g. CMEM); does not replace them.",
  contrast:
    "Memory layers remember. Models generate. NARNA assures decision quality and learns from outcomes.",
  cognitive:
    "Remember better inputs. Decide better. Learn continuously.",
  adqa: "Autonomous Decision Quality Assurance — the product you sell.",
  decisionIntelligence: "Decision Intelligence OS — memory is feedstock; DQS is the KPI.",
  enterprise: "Trust Every Agentic Decision.",
  decisionOs: "Connect data. Score decisions. Keep humans in control.",
  guardian: "Decision Guardian: approve · revise · escalate · reject.",
  technical:
    "Evidence. Policy. Context. Memory. Risk. Alignment. Capability. Compliance. Confidence. Explanation.",
  community: "Open quality standard for autonomous decisions.",
  category:
    "Decision Intelligence OS — ADQA · Decision Memory · Guardian Network.",
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

/** Pricing — Agent-first: Free Ask · Personal $20 · Team. See docs/BUSINESS-MODEL.md */
export const PRICING = {
  tagline: "Ask NARNA free. Upgrade for Decision Memory everywhere.",
  subline:
    "NARNA Agent is free on the web. Personal unlocks BYO models and Cloud ADQA — Team shares one Decision Brain.",
  philosophy: "Ask is the funnel. ADQA Cloud is quality. Team is shared Decision Intelligence.",
  unit: "agent turns",
  plans: [
    {
      id: "free",
      name: "Free Ask",
      price: "Free",
      period: "",
      limit: "50 agent turns / month",
      retention: "Short session memory",
      features: [
        "Ask NARNA on the web — no install",
        "Basic ADQA · Decision Quality Score",
        "Hosted LLM (NARNA-routed)",
        "pip install narna for local OSS",
      ],
      cta: "Ask NARNA",
      ctaTo: "/ask",
      featured: false,
    },
    {
      id: "cloud",
      name: "Personal",
      price: "$20",
      period: "/month",
      limit: "Cancel anytime · USDC/USDT",
      retention: "Cloud Decision Memory + DQS history",
      features: [
        "Higher Ask quota",
        "Bring Your Own LLM (OpenAI · Claude · OpenRouter · Ollama)",
        "ADQA API (api.narna.org)",
        "Decision Memory sync · Outcome Learning",
      ],
      cta: "Get Personal",
      ctaTo: "/billing",
      featured: true,
    },
    {
      id: "team",
      name: "Team",
      price: "$99",
      period: "/seat/mo",
      limit: "3–50 seats",
      retention: "Shared Decision Brain",
      features: [
        "One Decision Brain for the team",
        "Shared policies & approvals",
        "Per-project scopes",
        "Roles · access · audit",
        "MCP / agent fleet hooks",
      ],
      cta: "Talk to us",
      ctaTo: "/enterprise",
      featured: false,
    },
  ],
  enterpriseNote: "Enterprise / on-prem · industry packages · SSO · SLA — custom ($10k–100k/yr).",
  revenueStreams: [
    "Personal ($20/mo)",
    "Team seats",
    "Enterprise Decision Runtime",
    "Decision Package Marketplace",
  ],
} as const;
