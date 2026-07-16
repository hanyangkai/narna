import { Link, useParams } from "react-router-dom";
import { useMemo, useState } from "react";
import { BRAND, PROTOCOL } from "../brand";

type DocPage = {
  title: string;
  lead: string;
  sections: Array<{ heading?: string; body?: string; code?: string }>;
};

const DOCS: Record<string, DocPage> = {
  "borrow-the-wave": {
    title: "Borrow the Wave",
    lead: "Never Replace. Always Extend. — turn Big Tech releases into NARNA growth.",
    sections: [
      {
        body: "Do not compete with OpenAI, Anthropic, Google, or NVIDIA on runtimes or models. Sit above them. When they ship something new, ship an adapter and a certification path.",
      },
      {
        heading: "One-line integration",
        code: `from narna import wrap, track

agent = wrap(my_openai_agent, vap=True)

@track
def research(query: str) -> str:
    return call_llm(query)`,
      },
      {
        heading: "Default metadata",
        body: "Every agent should ship narna.yaml (like Dockerfile). It compiles to constitution.yaml.",
        code: "narna manifest --compile",
      },
      {
        heading: "Read more",
        body: "docs/BORROW-THE-WAVE.md · rfcs/ · Compatibility Program badges: NARNA Certified · UAP Compatible · Enterprise Ready.",
      },
    ],
  },
  adapters: {
    title: "Adapters",
    lead: "Adapter First — narna-openai, narna-mcp, narna-langgraph, …",
    sections: [
      {
        body: "Adapters extend host frameworks. They never replace them. Available now: narna-openai, narna-langgraph, narna-mcp, narna-opentelemetry, narna-crewai.",
        code: `from narna import wrap, ADAPTER_CATALOG

agent = wrap(my_langgraph_app, vap=True)
print(agent._adapter)  # hooks installed on invoke/…
print(ADAPTER_CATALOG)`,
      },
    ],
  },
  "what-is-narna": {
    title: "What is NARNA?",
    lead: "The Constitution Layer for Autonomous AI — in plain language.",
    sections: [
      {
        body: `${BRAND.contrast}`,
      },
      {
        heading: "Simple analogy",
        body: "OpenTelemetry is like a dashcam — it records what happened. NARNA is like a driver’s license + traffic law — it says who the agent is, what it is allowed to do, and why others can trust it.",
      },
      {
        heading: "What NARNA is not",
        body: "Not a model. Not LangGraph/CrewAI. Not a replacement for MCP or OpenTelemetry. Those systems execute and observe. NARNA governs.",
      },
      {
        heading: "Three names to remember",
        body: "NARNA = brand (Constitution Layer). UAP = protocol (Understand · Act · Prove). VAP = trust engine (Verify · Audit · Prove). Developer metadata = narna.yaml (compiles to constitution.yaml).",
      },
    ],
  },
  constitution: {
    title: "Constitution",
    lead: "constitution.yaml — the charter every autonomous entity should carry.",
    sections: [
      {
        body: "Prompts instruct. Runtimes execute. Constitutions govern. A Constitution declares identity, capability, permissions, policy rules, evidence requirements, and trust thresholds — independent of OpenAI, Claude, or any framework.",
        code: `apiVersion: narna.ai/v1alpha1
kind: Constitution
metadata:
  entityKind: Agent
  entityId: agent_…
spec:
  identity: { id, owner, version }
  capability: { supports: [browser, sql] }
  permission: { grants: […] }
  policy:
    rules:
      - id: no_money_transfer
        effect: deny
        action: wallet.transfer
  evidence: { mustProve: [side_effects] }
  trust: { algorithm: vap-trust-v0, minScore: 0.7 }`,
      },
      {
        heading: "Load in Python",
        body: "Validate against the normative schema.",
        code: `from narna import load_constitution, Agent

c = load_constitution("constitution.yaml")
agent = Agent("Researcher")
print(agent.constitution()["metadata"]["id"])`,
      },
      {
        heading: "CLI",
        code: "narna constitution\nnarna constitution --path constitution.yaml",
      },
    ],
  },
  install: {
    title: "Install",
    lead: "Install the NARNA reference SDK (virus entry — not the USP).",
    sections: [
      {
        body: "Python 3.11+. Offline by default — no account, no cloud. The SDK helps you try Constitution → Identity → Passport locally.",
        code: "pip install narna\n\n# Or from source\ngit clone https://github.com/hanyangkai/narna\ncd narna\npip install -e .",
      },
      {
        heading: "30-second hello",
        body: "Creates Agent + constitution.yaml automatically.",
        code: "from narna import Agent\n\nagent = Agent()\nagent.run()\nprint(agent.constitution()['kind'])",
      },
      {
        heading: "Verify installation",
        code: "narna doctor\nnarna constitution",
      },
    ],
  },
  quickstart: {
    title: "Quickstart",
    lead: "Constitution → VAP → Passport → Certify in a few minutes.",
    sections: [
      {
        heading: "1. Create an agent (writes constitution.yaml)",
        code: 'from narna import Agent\nagent = Agent("Researcher")\nprint(agent.constitution()["metadata"]["entityId"])',
      },
      {
        heading: "2. Enable trust (VAP)",
        body: "Verify → Audit → Prove on actions and at run end.",
        code: 'agent.enable_vap()\nresult = agent.run("btc price")\nprint(result.trust_score)',
      },
      {
        heading: "3. Passport cites Constitution",
        code: 'passport = agent.passport(refresh=True)\nprint(passport["constitution"])',
      },
      {
        heading: "4. Certify (levels)",
        body: "L1 charter · L2 proof · L3 enterprise.",
        code: 'cert = agent.certify(level="L2", remote=False)\nprint(cert["level"], cert["badge"])',
      },
      {
        heading: "CLI",
        code: "narna init\nnarna run --vap --input \"btc price\"\nnarna constitution\nnarna certify --vap --level L3 --local",
      },
    ],
  },
  identity: {
    title: "Universal Identity",
    lead: "Every AI entity gets a portable birth record — not just agents.",
    sections: [
      {
        body: "Agent, Tool, MCP Server, Workflow, Prompt, Dataset, Plugin, Memory, ModelBinding — same identity shape. Change the model vendor tomorrow; keep the same entityId if the charter is unchanged (Portable Trust).",
        code: `from narna import IdentityStore
from uap.hashing import sha256_obj

store = IdentityStore(workspace=".")
identity = store.issue_entity(
    kind="Tool",
    entity_id="tool_browser_01",
    owner="did:narna:org:acme",
    version="1.0.0",
    content_hash=sha256_obj({"name": "browser"}),
)
print(identity["identityId"], identity["kind"])`,
      },
      {
        heading: "Agent path (automatic)",
        body: "Agent() issues Agent identity and links it to constitution.yaml.",
        code: "agent = Agent('Researcher')\n# → .uap/identity/entities/<agentId>.json",
      },
    ],
  },
  policy: {
    title: "Policy",
    lead: "Android-style permissions + Constitution rules.",
    sections: [
      {
        body: "Policy lives in constitution.yaml (and optional AgentSpec). Deny by default. Effects: allow, deny, ask, require.",
        code: `policy:
  rules:
    - id: no_money_transfer
      effect: deny
      action: wallet.transfer
    - id: human_for_irreversible
      effect: ask
      when: irreversible == true`,
      },
    ],
  },
  evidence: {
    title: "Evidence",
    lead: "Proof packages — not mere traces.",
    sections: [
      {
        body: "OpenTelemetry records spans. NARNA Evidence is hashed, provenance-aware material that VAP can verify. Missing evidence lowers trust.",
        code: `evidence:
  source: coinbase.api
  content_hash: sha256:...
  timestamp: "2026-01-01T00:00:00Z"`,
      },
    ],
  },
  passport: {
    title: "Passport",
    lead: "Public trust view — like a verified badge for an AI entity.",
    sections: [
      {
        body: "Passport aggregates identity, capability, history, trust, and (C1) a citation to the Constitution id + hash.",
        code: 'passport = agent.passport(refresh=True)\nprint(passport["trust"]["score"])\nprint(passport["constitution"])',
      },
      {
        heading: "On the web",
        body: "Browse published agents at /registry and open /passport/:agentId.",
      },
    ],
  },
  compatibility: {
    title: "Compatibility",
    lead: "Sit above frameworks — never replace them.",
    sections: [
      {
        body: "NARNA integrates with OpenTelemetry, MCP, OpenAI Agents, LangGraph, CrewAI, OpenShell, Docker, and Kubernetes. Use narna.wrap() as a thin adapter while deeper adapters ship.",
        code: `from narna import wrap\nagent = wrap(my_langgraph_app, name="Researcher")\nagent.enable_vap()\nagent.run("summarize")`,
      },
    ],
  },
  certification: {
    title: "Certification",
    lead: "L1 · L2 · Enterprise Ready — like Kubernetes Certified for agents.",
    sections: [
      {
        body: "Certification is rule-based against your Constitution. It does not use “AI grades AI” as the sole authority.",
      },
      {
        heading: "Levels (easy map)",
        body: "L1 NARNA Certified = charter + identity + passport. L2 NARNA Certified+ = L1 + VAP proof + trust threshold. L3 Enterprise Ready = L2 + governance, retention ≥90d, human review, hard policy rules.",
        code: `agent.enable_vap()
agent.run("btc price")
cert = agent.certify(level="L3")
print(cert["level"], cert["badge"])
# L3  Enterprise Ready`,
      },
      {
        heading: "CLI",
        code: "narna certify --level L1 --local\nnarna certify --vap --level L2 --local\nnarna certify --vap --level L3 --local",
      },
    ],
  },
  examples: {
    title: "Examples",
    lead: "Specs and sample agents in the repository.",
    sections: [
      {
        heading: "Constitution example",
        body: "See specs/examples/constitution.yaml",
        code: "narna constitution --path specs/examples/constitution.yaml",
      },
      {
        heading: "Trading agent",
        code: "narna run --spec specs/examples/trading-agent.yaml --input 'btc price'",
      },
      {
        heading: "Self-host cloud (optional)",
        code: "docker compose up --build",
      },
    ],
  },
  "api-reference": {
    title: "API Reference",
    lead: "Optional cloud: registry, passport, certification, ingest.",
    sections: [
      {
        heading: "Registry & Passport",
        body: "POST /v1/registry/publish · GET /v1/passport/{agentId} · POST /v1/certification/submit",
      },
      {
        heading: "Ingest",
        body: "POST /v1/ingest — push run events and proof bundles (optional telemetry).",
        code: `curl -X POST http://localhost:8000/v1/ingest \\
  -H "Authorization: Bearer uap_live_..." \\
  -d '{"runId":"...","events":[...],"proofBundle":{...}}'`,
      },
    ],
  },
};

const SIDEBAR = [
  {
    group: "Start here",
    items: [
      { slug: "what-is-narna", label: "What is NARNA?" },
      { slug: "borrow-the-wave", label: "Borrow the Wave" },
      { slug: "constitution", label: "Constitution" },
      { slug: "install", label: "Install" },
      { slug: "quickstart", label: "Quickstart" },
    ],
  },
  {
    group: "Constitution Layer",
    items: [
      { slug: "identity", label: "Universal Identity" },
      { slug: "policy", label: "Policy" },
      { slug: "evidence", label: "Evidence" },
      { slug: "passport", label: "Passport" },
      { slug: "certification", label: "Certification" },
      { slug: "adapters", label: "Adapters" },
      { slug: "compatibility", label: "Compatibility" },
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
    </aside>
  );
}

export default function Docs() {
  const { slug } = useParams();
  const active = slug || "what-is-narna";
  const [query, setQuery] = useState("");
  const page = DOCS[active] || DOCS["what-is-narna"];

  const filteredHint = useMemo(() => {
    if (!query.trim()) return null;
    return `Filtering sidebar for “${query.trim()}”`;
  }, [query]);

  return (
    <div className="layout-wide docs-layout">
      <DocsSidebar active={active} query={query} />
      <article className="docs-content">
        <div className="docs-search">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search docs…"
            aria-label="Search docs"
          />
          {filteredHint && (
            <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{filteredHint}</p>
          )}
        </div>
        <header className="page-header" style={{ border: "none", paddingTop: 0 }}>
          <p className="pill-label">{BRAND.name} Docs · {PROTOCOL.name}</p>
          <h1>{page.title}</h1>
          <p>{page.lead}</p>
        </header>
        {page.sections.map((s, i) => (
          <section key={i} className="docs-section">
            {s.heading && <h2>{s.heading}</h2>}
            {s.body && <p>{s.body}</p>}
            {s.code && <pre className="code-block mono">{s.code}</pre>}
          </section>
        ))}
        <p style={{ marginTop: "2rem", color: "var(--muted)", fontSize: "0.9rem" }}>
          Strategy lock: <Link to="/specification">Specification</Link> ·{" "}
          <a href={`${BRAND.github}/blob/main/docs/STRATEGY.md`} target="_blank" rel="noreferrer">
            STRATEGY.md
          </a>
        </p>
      </article>
    </div>
  );
}
