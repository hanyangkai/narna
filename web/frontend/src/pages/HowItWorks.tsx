import { Link } from "react-router-dom";
import { BRAND, SPEC } from "../brand";

const LOOP = [
  { step: "01", title: "Perceive", body: "User asks · agent gathers context · memory recalled (local or CMEM)." },
  { step: "02", title: "Reason", body: "LLM plans · tools run · evidence collected. Your key (BYOK) or mock mode." },
  { step: "03", title: "Verify (ADQA)", body: "Score DQS · check policy · risk · alignment. Guardian: ACT · REVIEW · REJECT." },
  { step: "04", title: "Decide & act", body: "Only high-quality decisions proceed. Shell / browser / MCP need approval when risky." },
  { step: "05", title: "Learn", body: "Outcome recorded · lesson saved to Decision Memory · MEMORY.md updated." },
] as const;

const LAYERS = [
  {
    id: "agent",
    name: "NARNA Agent",
    question: "What should we do?",
    items: ["Ask / Desktop / CLI", "Tools · browser · shell", "Model router (BYOK)", "Social gateway (optional)"],
    color: "var(--accent)",
  },
  {
    id: "adqa",
    name: "ADQA",
    question: "Is it good enough to act?",
    items: ["DQS score 0–100", "Evidence · policy · risk", "Decision Guardian", "Works on any agent"],
    color: "var(--ok)",
  },
  {
    id: "memory",
    name: "Decision Memory",
    question: "What did we learn?",
    items: ["Traces · replay", "Lessons · outcomes", "MEMORY.md + FTS", "Not chat logs"],
    color: "var(--warn)",
  },
] as const;

const PATHS = [
  {
    title: "Desktop (free)",
    best: "Mac / Windows · full agent on your machine",
    steps: ["Download zip", "Paste LLM key", "Chat + tools at 127.0.0.1", "Data in ~/.narna"],
    cta: "/download",
    ctaLabel: "Download free",
  },
  {
    title: "Ask in browser",
    best: "Try without install",
    steps: ["Open /ask", "BYOK in browser", "ADQA scores every turn", "Fair-use on hosted cloud"],
    cta: "/ask",
    ctaLabel: "Open Ask",
  },
  {
    title: "MCP (Cursor / OpenClaw)",
    best: "Decision quality beside your IDE agent",
    steps: ["Point MCP at api.narna.org/mcp", "Tools: adqa_check · agent_ask", "Pair with CMEM for recall", "Does not replace IDE tools"],
    cta: "/docs/integrations",
    ctaLabel: "MCP setup",
  },
] as const;

const MCP_TOOLS = [
  "narna_adqa_check",
  "narna_agent_ask",
  "narna_evaluate_action",
  "narna_dmemory_query",
  "narna_learning_prior",
  "narna_cmem_enrich",
  "narna_trace_get / list / replay",
  "narna_runtime_status",
] as const;

const MEMORY_STACK = [
  { layer: "Continuity (optional)", who: "CMEM / claude-mem", what: "Observations across sessions & machines" },
  { layer: "Agent notes (built-in)", who: "NARNA local", what: "MEMORY.md · USER.md · PROJECT.md · FTS search" },
  { layer: "Decision quality (built-in)", who: "NARNA ADQA", what: "DQS · traces · lessons · replay" },
  { layer: "Scoped context", who: "DurableMemory", what: "Per project / customer / contract JSON" },
] as const;

export default function HowItWorks() {
  return (
    <div className="layout-wide how-page">
      <header className="page-header">
        <p className="pill-label">How it works</p>
        <h1>AI agents act. NARNA makes them decide better.</h1>
        <p>
          One page — no jargon wall. {BRAND.name} is an open-source <strong>agent</strong> plus{" "}
          <strong>ADQA</strong> (decision quality) plus <strong>Decision Memory</strong> (learn from outcomes).
          Memory partners like <a href="https://cmem.ai/" target="_blank" rel="noreferrer">CMEM</a> are optional
          complements, not replacements.
        </p>
      </header>

      {/* Cognitive loop */}
      <section className="section" style={{ paddingTop: 0, borderTop: "none" }}>
        <h2>The loop — {BRAND.cognitive}</h2>
        <p className="section-desc">
          Every turn follows the same path. Other agents stop at “I have a plan.” NARNA adds verify + learn.
        </p>
        <ol className="how-loop">
          {LOOP.map((s) => (
            <li key={s.step} className="how-loop-item card">
              <span className="how-loop-n">{s.step}</span>
              <div>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* Three layers diagram */}
      <section className="section">
        <h2>Three layers — don&apos;t mix them up</h2>
        <pre className="code-block how-diagram" aria-label="Architecture diagram">
{`  ┌─────────────────────────────────────────────────────────┐
  │  YOUR LLM (OpenRouter / OpenAI / Ollama / local)        │
  └──────────────────────────┬──────────────────────────────┘
                             │
  ┌──────────────────────────▼──────────────────────────────┐
  │  NARNA AGENT — reason, tools, chat, gateway             │
  └──────────────────────────┬──────────────────────────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
  ┌────▼────┐          ┌─────▼─────┐         ┌─────▼──────┐
  │ Memory  │          │   ADQA    │         │  Decision  │
  │ feed    │─────────▶│  Guardian │────────▶│  Memory    │
  │ CMEM?   │          │  DQS      │         │  lessons   │
  └─────────┘          └───────────┘         └────────────┘`}
        </pre>
        <div className="feature-grid">
          {LAYERS.map((l) => (
            <div key={l.id} className="card feature-card how-layer-card">
              <p className="how-layer-q">{l.question}</p>
              <h3 style={{ color: l.color }}>{l.name}</h3>
              <ul className="land-price-features">
                {l.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Memory stack */}
      <section className="section">
        <h2>Memory — what remembers what?</h2>
        <p className="section-desc">
          NARNA ships enough memory for solo Desktop use. For cross-machine continuity, plug in CMEM — NARNA
          reads it as feedstock; it does not fork CMEM.
        </p>
        <div className="how-memory-table card">
          <table>
            <thead>
              <tr>
                <th>Layer</th>
                <th>System</th>
                <th>Stores</th>
              </tr>
            </thead>
            <tbody>
              {MEMORY_STACK.map((row) => (
                <tr key={row.layer}>
                  <td>{row.layer}</td>
                  <td className="mono">{row.who}</td>
                  <td>{row.what}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ marginTop: "1rem" }}>
          <Link to="/docs/integrations">CMEM bridge guide →</Link>
          {" · "}
          <code>export NARNA_CMEM_URL=https://mcp.cmem.ai/u/YOUR_LINK</code>
        </p>
      </section>

      {/* Three ways to use */}
      <section className="section">
        <h2>Three ways to use NARNA</h2>
        <div className="feature-grid">
          {PATHS.map((p) => (
            <div key={p.title} className="card feature-card">
              <h3>{p.title}</h3>
              <p className="section-desc">{p.best}</p>
              <ol className="how-path-steps">
                {p.steps.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ol>
              <Link to={p.cta} className="btn btn-secondary" style={{ marginTop: "0.75rem" }}>
                {p.ctaLabel}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* MCP status */}
      <section className="section" id="mcp">
        <h2>MCP — decision tools for any client</h2>
        <p className="section-desc">
          <strong>Status: v0.2 shipped.</strong> Cloud endpoint live at{" "}
          <code>https://api.narna.org/mcp</code>. JSON-RPC + SSE handshake. Ten tools for ADQA, Ask, traces,
          CMEM enrich — <em>not</em> the full 44-tool Desktop runtime (use Desktop for shell/browser loop).
        </p>
        <pre className="code-block">{`# Cursor / Claude Code / OpenClaw
{
  "mcp": {
    "servers": {
      "narna": {
        "url": "https://api.narna.org/mcp",
        "headers": { "Authorization": "Bearer uap_live_…" }
      }
    }
  }
}`}</pre>
        <h3 style={{ marginTop: "1.25rem" }}>MCP tools ({MCP_TOOLS.length})</h3>
        <ul className="how-mcp-tools mono">
          {MCP_TOOLS.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
        <p style={{ marginTop: "1rem" }}>
          Discovery:{" "}
          <a href="https://api.narna.org/mcp" target="_blank" rel="noreferrer">
            GET /mcp
          </a>
          {" · "}
          <Link to="/docs/drop-in-saas">Drop-in SaaS docs →</Link>
        </p>
      </section>

      {/* FAQ */}
      <section className="section">
        <h2>FAQ</h2>
        <div className="how-faq">
          <details className="card">
            <summary>Is MCP “done”?</summary>
            <p>
              <strong>Yes for ADQA + Ask surface</strong> — 10 tools, HTTP JSON-RPC, SSE, tenant auth, metering.
              Not done: exposing every Desktop tool (shell, browser, 44 tools) over MCP; use Desktop or gateway
              for that. Stdio MCP server for local IDE is roadmap.
            </p>
          </details>
          <details className="card">
            <summary>Do I need to upgrade memory?</summary>
            <p>
              <strong>Solo Desktop:</strong> built-in MEMORY.md + FTS + Decision Memory is enough to start.
              <strong> Multi-machine / team:</strong> add CMEM Cloud or your own MCP memory — set{" "}
              <code>NARNA_CMEM_URL</code>. NARNA will not build a CMEM clone; it scores decisions on top of
              whatever memory you bring.
            </p>
          </details>
          <details className="card">
            <summary>NARNA vs Hermes / OpenClaw?</summary>
            <p>
              Hermes/OpenClaw = do the work (tools, channels). NARNA = score whether the decision was good
              enough + learn. Use both: OpenClaw acts, NARNA ADQA via MCP.
            </p>
          </details>
          <details className="card">
            <summary>Is Pro required?</summary>
            <p>
              No. Desktop agent is free (Mac/Windows, BYOK). Cloud Ask has fair-use limits. Pro checkout is not
              launched yet — see <Link to="/pricing">pricing</Link>.
            </p>
          </details>
        </div>
      </section>

      {/* CTA */}
      <section className="section how-cta">
        <h2>Start in 30 seconds</h2>
        <div className="land-cta">
          <Link className="btn btn-primary" to="/download">
            Download free (Mac / Windows)
          </Link>
          <Link className="btn btn-secondary" to="/ask">
            Try Ask
          </Link>
          <Link className="btn btn-secondary" to="/docs">
            Read docs
          </Link>
        </div>
        <pre className="code-block" style={{ marginTop: "1.25rem" }}>
          {`${SPEC.install}\nnarna desktop   # or: narna ask`}
        </pre>
      </section>
    </div>
  );
}
