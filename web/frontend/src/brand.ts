/** NARNA — Open-source AI agent bot. */

export const BRAND = {
  name: "NARNA",
  expand: "Neural Autonomous Rules Native Architecture",
  letters: ["Neural", "Autonomous", "Rules", "Native", "Architecture"] as const,
  /** Public category — agent bot first */
  tagline: "Open-source AI agent bot. Desktop brain. Phone remote. ADQA before it acts.",
  categoryFull: "Open-source AI Agent Bot + Decision Quality (ADQA)",
  productCore: "ADQA",
  productCoreExpand: "Autonomous Decision Quality Assurance",
  altTagline: "Run Claude / Codex on Desktop. Control from your phone. Every action scored.",
  heroTitle: "NARNA",
  heroLead: "Your AI agent bot — on your machine.",
  heroSub:
    "Like MausBot: Desktop runs Claude CLI or Codex CLI (your subscription) or BYOK. Pair the phone. ADQA scores risky actions before they execute.",
  northStar:
    "Every autonomous action is evidence-based, policy-compliant, risk-aware, and human-approved when needed.",
  primary: "Ship the agent bot. ADQA is why it is safer than a raw CLI.",
  oneLiner:
    "NARNA is an open-source agent bot: Desktop engines + mobile remote + ADQA decision gate.",
  mission:
    "Make open agent bots usable day-to-day — with decision quality as the default safety layer.",
  vision:
    "Every personal and team agent bot verifies before it acts — the way CI verifies before you ship.",
  elevator:
    "Install NARNA Desktop. Login Claude or Codex CLI (or paste an API key). Pair your phone. The bot works; ADQA decides when to ask you first.",
  contrast:
    "Other bots maximize tools. NARNA bots maximize correct action — ACT / REVIEW / REJECT.",
  cognitive: "Chat → Plan → ADQA → Act → Learn.",
  adqa: "Autonomous Decision Quality Assurance — brake before shell, spend, or send.",
  decisionIntelligence: "Decision Intelligence — DQS is the KPI.",
  enterprise: "Trust every agentic action.",
  decisionOs: "Connect channels. Score decisions. Keep humans in control.",
  guardian: "Decision Guardian: ACT · REVIEW · REJECT.",
  technical:
    "Evidence. Policy. Context. Memory. Risk. Alignment. Capability. Compliance. Confidence. Explanation.",
  community: "MIT open-source agent bot — Desktop, gateway, ADQA, mobile companion.",
  category: "Agent Bot · Desktop CLI · Mobile Remote · ADQA · Social Gateway.",
  closing: "An agent that can act — and knows when to wait for you.",
  github: "https://github.com/hanyangkai/narna",
  discord: "https://discord.gg/narna",
  emailEnterprise: "enterprise@narna.ai",
  modelDoc: "https://github.com/hanyangkai/narna/blob/main/docs/AGENT-BOT-MODEL.md",
  /** Public store destinations (package reserved; listing goes live after review). */
  appStoreUrl: "https://apps.apple.com/search?term=NARNA%20Mobile",
  playStoreUrl: "https://play.google.com/store/apps/details?id=org.narna.mobile",
  bundleId: "org.narna.mobile",
} as const;

/** Open standard (public). Formerly UAP workflow name. */
export const SPEC = {
  name: "UGS",
  expand: "Universal Governance Specification",
  install: 'pip install "narna[desktop]"',
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
  { year: "2026+", label: "Agent Bots + Decision Quality" },
] as const;

export const AGENTIC_TRAITS = [
  "Desktop Bot",
  "Mobile Remote",
  "CLI Subscription Path",
  "BYOK",
  "Human Approval",
  "Tool Calling",
  "Social Channels",
] as const;

export const AGENTIC_QUESTIONS = [
  "Is this action safe to run?",
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
  { company: "MausBot", owns: "Mobile remote + CLI engines" },
  { company: "Hermes / OpenClaw", owns: "Agent runtimes" },
  { company: "LangGraph", owns: "Agent orchestration" },
  { company: "MCP", owns: "Tool protocol" },
  { company: "NARNA", owns: "Agent bot + ADQA decision gate" },
] as const;

export const PRODUCT_FAMILY = [
  "NARNA Desktop Bot",
  "Mobile Companion",
  "ADQA Core (DQS)",
  "Decision Guardian",
  "Social Gateway",
  "NARNA SDK / CLI",
  "Hosted MCP",
  "NARNA Cloud (Pro)",
  "NARNA Enterprise",
] as const;

export const COMPATIBILITY = [
  "Claude Code CLI",
  "Codex CLI",
  "OpenAI",
  "Anthropic",
  "Google",
  "LangGraph",
  "CrewAI",
  "MCP",
  "OpenClaw",
  "Hermes",
  "Telegram",
  "WhatsApp",
  "Discord",
  "Docker",
] as const;

/** Pricing — Desktop free forever; Pro = Cloud Brain */
export const PRICING = {
  tagline: "Desktop agent bot free forever. Pro keeps it always-on.",
  subline:
    "Full bot on Mac/Windows — Claude CLI, Codex CLI, or BYOK. Phone pairs by QR. Pro adds cloud brain, sync, and always-on channels.",
  philosophy:
    "Local bot free. Model cost stays with your Claude/GPT subscription or API key. Pro unlocks cloud — not a Claude substitute.",
  unit: "agent turns",
  freeFirst: true,
  plans: [
    {
      id: "free",
      name: "Free",
      price: "$0",
      period: "",
      limit: "Desktop unlimited · pair phone · BYOK / CLI",
      retention: "Local ~/.narna · forever",
      features: [
        "Full Desktop agent bot (Mac + Windows)",
        "Claude CLI · Codex CLI · BYOK keys",
        "ADQA · Decision Memory · tools",
        "Mobile pair (QR) · social gateway",
      ],
      cta: "Download Desktop",
      ctaTo: "/download",
      featured: true,
    },
    {
      id: "cloud",
      name: "Pro",
      price: "$20",
      period: "/mo",
      limit: "Web USDC/USDT · App Store / Play on mobile",
      retention: "Cloud backup · sync · always-on",
      features: [
        "Cloud brain when PC is off",
        "Inbox · routines · voice · push",
        "Hosted MCP for Cursor / Claude Code",
        "Still BYOK for model tokens",
      ],
      cta: "Get Pro",
      ctaTo: "/checkout",
      featured: false,
      comingSoon: false,
    },
    {
      id: "team",
      name: "Team",
      price: "$99",
      period: "/seat/mo",
      limit: "Min 3 seats · max 50",
      retention: "Shared bots · org inbox",
      features: [
        "Everything in Pro",
        "Shared bots + cross-seat approvals",
        "Org cloud quotas",
        "Mobile + web same entitlement",
      ],
      cta: "Get Team",
      ctaTo: "/billing",
      featured: false,
      comingSoon: false,
    },
  ],
  enterpriseNote:
    "Business $199/mo · Enterprise custom (SSO · on-prem · SLA). Same plan IDs on web and mobile — see docs/PRICING-UNIFIED.md.",
  whyUpgrade: [
    "Desktop stays free: full agent bot, CLI or BYOK — no NARNA license fee.",
    "Claude / ChatGPT Pro subscriptions work via Desktop CLI — not inside the mobile app.",
    "Pro $20/mo = cloud brain: always-on, sync phone + PC, hosted MCP, routines.",
    "Team $99/seat = shared bots + org approvals.",
  ],
  revenueStreams: [
    "Pro $20/mo — web USDC/USDT · iOS App Store · Android Play Billing",
    "Pro annual ~$160 — App Store / Play only",
    "Team $99/seat — web crypto · in-app via Apple/Google only (no crypto in apps)",
    "Business $199/mo · Enterprise custom (web)",
  ],
} as const;
