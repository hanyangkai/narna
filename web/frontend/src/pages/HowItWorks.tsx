import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { BRAND } from "../brand";

function FlowArrow({ label }: { label?: string }) {
  return (
    <div className="how-arrow" aria-hidden>
      {label ? <span>{label}</span> : null}
      <svg viewBox="0 0 24 24" width="20" height="20">
        <path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
    </div>
  );
}

function LayerBox({
  title,
  sub,
  tone,
  children,
}: {
  title: string;
  sub: string;
  tone: "agent" | "adqa" | "memory" | "llm" | "cmem";
  children?: ReactNode;
}) {
  return (
    <div className={`how-box how-box-${tone}`}>
      <p className="how-box-sub">{sub}</p>
      <h3>{title}</h3>
      {children}
    </div>
  );
}

export default function HowItWorks() {
  return (
    <div className="layout-wide how-page how-visual">
      <header className="page-header how-hero">
        <p className="pill-label">How it works</p>
        <h1>Act → Verify → Learn</h1>
        <p className="how-hero-lead">
          Agent does the work · ADQA scores quality · Memory keeps lessons
        </p>
      </header>

      <section className="how-panel">
        <h2 className="how-panel-title">The loop</h2>
        <div className="how-flow">
          <div className="how-node">
            <span className="how-node-icon">💬</span>
            <strong>Ask</strong>
          </div>
          <FlowArrow />
          <div className="how-node">
            <span className="how-node-icon">🧠</span>
            <strong>Reason</strong>
          </div>
          <FlowArrow />
          <div className="how-node how-node-accent">
            <span className="how-node-icon">✓</span>
            <strong>ADQA</strong>
            <small>DQS · Guardian</small>
          </div>
          <FlowArrow />
          <div className="how-node">
            <span className="how-node-icon">⚡</span>
            <strong>Act</strong>
          </div>
          <FlowArrow />
          <div className="how-node">
            <span className="how-node-icon">📚</span>
            <strong>Learn</strong>
          </div>
        </div>
      </section>

      <section className="how-panel">
        <h2 className="how-panel-title">Architecture</h2>
        <div className="how-stack">
          <LayerBox title="Your LLM" sub="Brain" tone="llm">
            <p>OpenRouter · OpenAI · Ollama · or web Ask</p>
          </LayerBox>
          <div className="how-stack-connector" />
          <LayerBox title="NARNA Agent" sub="Runtime" tone="agent">
            <p>Chat · tools · browser · gateway</p>
          </LayerBox>
          <div className="how-stack-row">
            <LayerBox title="Memory" sub="What to recall?" tone="memory">
              <p>MEMORY.md · FTS · lessons</p>
            </LayerBox>
            <LayerBox title="ADQA" sub="Good enough?" tone="adqa">
              <p>ACT · REVIEW · REJECT</p>
            </LayerBox>
            <LayerBox title="CMEM" sub="Optional" tone="cmem">
              <p>Cross-device sync</p>
            </LayerBox>
          </div>
        </div>
      </section>

      <section className="how-panel how-panel-memory">
        <h2 className="how-panel-title">Memory — 3 layers</h2>
        <div className="how-memory-lanes">
          <div className="how-lane">
            <span className="how-lane-tag">Today</span>
            <strong>Session + FTS</strong>
            <p>Every turn indexed · semantic search recall</p>
          </div>
          <div className="how-lane how-lane-mid">
            <span className="how-lane-tag">Long-term</span>
            <strong>MEMORY.md + lessons</strong>
            <p>DQS ≥ 60 → auto-save lessons · USER/PROJECT profile</p>
          </div>
          <div className="how-lane">
            <span className="how-lane-tag">Multi-device</span>
            <strong>CMEM bridge</strong>
            <p>
              <code>NARNA_CMEM_URL</code> ·{" "}
              <a href="https://cmem.ai/" target="_blank" rel="noreferrer">
                cmem.ai
              </a>
            </p>
          </div>
        </div>
        <p className="how-note">
          v0.2.9: higher FTS recall · recent lessons always injected into context
        </p>
      </section>

      <section className="how-panel">
        <h2 className="how-panel-title">Where to run</h2>
        <div className="how-devices">
          <div className="how-device how-device-ok">
            <span className="how-device-icon">🖥</span>
            <h3>Mac / Windows</h3>
            <p className="how-device-status">✓ Full agent</p>
            <ul>
              <li>Tools · shell · browser</li>
              <li>~50–200 MB app</li>
              <li>Data in ~/.narna</li>
            </ul>
            <Link to="/download" className="btn btn-primary btn-sm">
              Download
            </Link>
          </div>
          <div className="how-device how-device-partial">
            <span className="how-device-icon">📱</span>
            <h3>iPhone / iPad</h3>
            <p className="how-device-status">◐ PWA Ask</p>
            <ul>
              <li>Add to Home Screen → /ask</li>
              <li>BYOK key in Safari</li>
              <li>No Desktop binary</li>
            </ul>
            <Link to="/ask" className="btn btn-secondary btn-sm">
              Open Ask
            </Link>
          </div>
          <div className="how-device how-device-partial">
            <span className="how-device-icon">🌐</span>
            <h3>Browser only</h3>
            <p className="how-device-status">◐ Ask + ADQA</p>
            <ul>
              <li>No local LLM install</li>
              <li>API key or mock mode</li>
              <li>Fair-use cloud</li>
            </ul>
            <Link to="/ask" className="btn btn-secondary btn-sm">
              Try Ask
            </Link>
          </div>
        </div>
      </section>

      <section className="how-panel">
        <h2 className="how-panel-title">No LLM on your PC?</h2>
        <div className="how-llm-options">
          <div className="how-llm-card how-llm-yes">
            <h3>✓ Yes — via API</h3>
            <div className="how-llm-flow">
              <span>You</span>
              <FlowArrow />
              <span>NARNA Ask</span>
              <FlowArrow />
              <span>OpenRouter / OpenAI</span>
            </div>
            <p>Paste key once · pay per provider usage · no model download</p>
          </div>
          <div className="how-llm-card how-llm-no">
            <h3>✗ Not yet — drive ChatGPT web</h3>
            <p>
              NARNA does <strong>not</strong> log into ChatGPT.com / Claude.ai for you (anti-bot, ToS).
              Desktop <code>browser_navigate</code> opens pages you control — not a substitute for an LLM API.
            </p>
            <p className="how-note">Workaround: OpenRouter free tier · Ollama when you have GPU/RAM</p>
          </div>
        </div>
      </section>

      <section className="how-panel how-panel-compact">
        <h2 className="how-panel-title">MCP</h2>
        <div className="how-mcp-strip">
          <code>api.narna.org/mcp</code>
          <span>→</span>
          <span>ADQA · Ask · traces · CMEM enrich</span>
        </div>
        <Link to="/docs/integrations">Setup Cursor / OpenClaw →</Link>
      </section>

      <section className="how-cta-bar">
        <Link className="btn btn-primary" to="/download">
          Mac / Windows free
        </Link>
        <Link className="btn btn-secondary" to="/ask">
          iPhone / browser Ask
        </Link>
      </section>
    </div>
  );
}
