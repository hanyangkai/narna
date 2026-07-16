import { Link, useParams } from "react-router-dom";
import { useMemo, useState } from "react";

type DocPage = {
  title: string;
  lead: string;
  sections: Array<{ heading?: string; body: string; code?: string }>;
};

const DOCS: Record<string, DocPage> = {
  install: {
    title: "Install",
    lead: "Install the UAP Python SDK and verify your environment.",
    sections: [
      {
        body: "UAP requires Python 3.10+. Install from PyPI or from source in this repository.",
        code: "pip install uap\n\n# Or from source\ngit clone https://github.com/uap-standard/uap\ncd uap\npip install -e .",
      },
      {
        heading: "Verify installation",
        body: "Run the doctor command to check your environment and spec conformance.",
        code: "uap doctor\nuap doctor --full",
      },
    ],
  },
  quickstart: {
    title: "Quickstart",
    lead: "Create your first verifiable agent in five minutes.",
    sections: [
      {
        heading: "1. Initialize workspace",
        body: "Create a new agent workspace with a default AgentSpec.",
        code: "uap init\n# Creates agent.yaml, policies/, and .uap/ workspace",
      },
      {
        heading: "2. Define your agent",
        body: "AgentSpec is the declarative contract. Identity, permissions, tools, and policy are declared in YAML.",
        code: `agent:
  id: trading-agent
  name: Trading Agent
  version: "0.1.0"
  capability: [trade, search]
  permissions:
    - wallet.transfer
    - browser.open
  tools: [coinbase.spot, binance.ticker]
  policy: policies/trading-default.yaml`,
      },
      {
        heading: "3. Run and prove",
        body: "Every execution produces a hash-chained event log. Prove generates a ProofBundle.",
        code: 'uap run --input "btc price"\nuap prove --run <runId>\nuap verify --run <runId>',
      },
      {
        heading: "4. Optional: push to cloud",
        body: "Telemetry export is opt-in. Self-host or use UAP Cloud.",
        code: "uap push --run <runId> --cloud-key <api_key>",
      },
    ],
  },
  runtime: {
    title: "Runtime",
    lead: "The UAP runtime manages execution lifecycle, permission gating, and event logging.",
    sections: [
      {
        body: "The runtime enforces the UAP-Execution spec. Every tool call passes through the policy engine before execution. Denied actions are logged and never executed.",
      },
      {
        heading: "Run states",
        body: "Runs follow a deterministic state machine: CREATED → STARTING → RUNNING → COMPLETING → COMPLETED (or FAILED/ABORTED).",
        code: "from uap import Agent\n\nagent = Agent.from_spec('agent.yaml')\nresult = agent.run(input='check btc price')\nagent.prove(result.run_id)",
      },
    ],
  },
  policy: {
    title: "Policy",
    lead: "Android-style permissions with parameter-aware constraints.",
    sections: [
      {
        body: "Policy packs define allow/deny rules. The engine evaluates every action against declared permissions and constraints before execution.",
        code: `permissions:
  - id: wallet.transfer
    constraints:
      max_amount_usd: 1000
      allowed_recipients: ["0x..."]`,
      },
      {
        heading: "Deny by default",
        body: "If a permission is not explicitly granted in AgentSpec and allowed by policy, the action is denied and recorded in the audit trail.",
      },
    ],
  },
  identity: {
    title: "Identity",
    lead: "Every agent receives an immutable birth record signed by its creator.",
    sections: [
      {
        body: "Identity is cryptographic (Ed25519). Each agent has a unique AgentID, creator, version, and signature — similar to a git commit.",
        code: "from uap import IdentityStore\n\nstore = IdentityStore(workspace='.uap')\nidentity = store.issue(agent_spec)\nprint(identity.agent_id, identity.signature)",
      },
    ],
  },
  evidence: {
    title: "Evidence",
    lead: "Verifiable data attached to every action.",
    sections: [
      {
        body: "Evidence objects include content hash, schema validation, provenance, and freshness checks. Missing evidence reduces trust score.",
        code: `evidence:
  source: coinbase.api
  content_hash: sha256:...
  timestamp: "2026-01-01T00:00:00Z"
  schema: evidence.api-response.v1`,
      },
    ],
  },
  passport: {
    title: "Passport",
    lead: "A materialized view of agent identity, capability, history, and trust.",
    sections: [
      {
        body: "The passport aggregates run history, observed capabilities, and latest trust scores. It is the public-facing trust artifact for an agent.",
        code: "passport = agent.passport()\nprint(passport.trust_score, passport.history)",
      },
    ],
  },
  examples: {
    title: "Examples",
    lead: "Reference integrations and sample agents.",
    sections: [
      {
        heading: "Trading agent",
        body: "A policy-gated trading agent with multi-source price evidence.",
        code: "uap run --spec specs/examples/trading-agent.yaml --input 'btc price'",
      },
      {
        heading: "LangGraph / CrewAI",
        body: "Wrap any orchestrator with UAP SDK. The runtime tracks tool calls and generates evidence regardless of the underlying framework.",
      },
      {
        heading: "Self-host cloud",
        body: "Run the full stack locally with Docker.",
        code: "docker compose up --build",
      },
    ],
  },
  "api-reference": {
    title: "API Reference",
    lead: "Cloud export protocol and REST API for hosted telemetry.",
    sections: [
      {
        heading: "Ingest",
        body: "POST /v1/ingest — push run events and proof bundles to UAP Cloud.",
        code: `curl -X POST https://api.uap.dev/v1/ingest \\
  -H "Authorization: Bearer uap_live_..." \\
  -d '{"runId":"...","events":[...],"proofBundle":{...}}'`,
      },
      {
        heading: "Runs",
        body: "GET /v1/runs — list runs. GET /v1/runs/{id} — run detail with events.",
      },
      {
        heading: "Billing",
        body: "GET /v1/billing/status — plan and usage. POST /v1/billing/crypto/checkout-session — multi-chain stablecoin payment.",
      },
    ],
  },
};

const SIDEBAR = [
  {
    group: "Getting Started",
    items: [
      { slug: "install", label: "Install" },
      { slug: "quickstart", label: "Quickstart" },
    ],
  },
  {
    group: "SDK",
    items: [
      { slug: "runtime", label: "Runtime" },
      { slug: "policy", label: "Policy" },
      { slug: "identity", label: "Identity" },
      { slug: "evidence", label: "Evidence" },
      { slug: "passport", label: "Passport" },
    ],
  },
  {
    group: "Reference",
    items: [
      { slug: "api-reference", label: "API Reference" },
      { slug: "examples", label: "Examples" },
    ],
  },
];

function DocsSidebar({ active, query }: { active: string; query: string }) {
  const q = query.trim().toLowerCase();
  return (
    <aside className="docs-sidebar">
      {SIDEBAR.map((g) => {
        const items = g.items.filter(
          (item) => !q || item.label.toLowerCase().includes(q) || item.slug.includes(q)
        );
        if (items.length === 0) return null;
        return (
          <div key={g.group}>
            <h4>{g.group}</h4>
            {items.map((item) => (
              <Link
                key={item.slug}
                to={`/docs/${item.slug}`}
                className={active === item.slug ? "active" : ""}
              >
                {item.label}
              </Link>
            ))}
          </div>
        );
      })}
      <div style={{ marginTop: "1.5rem" }}>
        <Link to="/specification">→ Specification</Link>
      </div>
    </aside>
  );
}

export default function Docs() {
  const { slug } = useParams();
  const [query, setQuery] = useState("");
  const page = DOCS[slug ?? "quickstart"] ?? DOCS.quickstart;
  const active = slug ?? "quickstart";

  const contentHits = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    const hay = [page.title, page.lead, ...page.sections.flatMap((s) => [s.heading ?? "", s.body, s.code ?? ""])].join(" ").toLowerCase();
    return hay.includes(q);
  }, [page, query]);

  return (
    <div className="layout-wide docs-layout">
      <DocsSidebar active={active} query={query} />
      <article className="docs-content">
        <div className="docs-search">
          <input
            type="search"
            placeholder="Search docs..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search documentation"
          />
        </div>
        {!contentHits && query && (
          <p style={{ color: "var(--muted)" }}>No matches on this page for &quot;{query}&quot;.</p>
        )}
        {(contentHits || !query) && (
          <>
            <h1>{page.title}</h1>
            <p className="lead">{page.lead}</p>
            {page.sections.map((s, i) => (
              <div key={i}>
                {s.heading && <h2>{s.heading}</h2>}
                <p>{s.body}</p>
                {s.code && <pre className="code-block mono">{s.code}</pre>}
              </div>
            ))}
          </>
        )}
      </article>
    </div>
  );
}
