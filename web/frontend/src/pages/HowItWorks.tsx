import { Link } from "react-router-dom";
import { BRAND } from "../brand";

export default function HowItWorks() {
  return (
    <div className="layout-wide how-page how-visual">
      <header className="page-header how-hero">
        <p className="pill-label">How it works</p>
        <h1>Agent bot model</h1>
        <p className="how-hero-lead">
          Desktop runs the bot · Phone remotes it · ADQA gates risky actions
        </p>
      </header>

      <section className="how-panel">
        <h2 className="how-panel-title">The loop</h2>
        <div className="how-flow">
          <div className="how-node">
            <span className="how-node-icon">💬</span>
            <strong>You chat</strong>
            <small>Phone / TG / Discord</small>
          </div>
          <div className="how-arrow" aria-hidden>
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" />
            </svg>
          </div>
          <div className="how-node">
            <span className="how-node-icon">🖥</span>
            <strong>Desktop bot</strong>
            <small>Claude / Codex / BYOK</small>
          </div>
          <div className="how-arrow" aria-hidden>
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" />
            </svg>
          </div>
          <div className="how-node how-node-accent">
            <span className="how-node-icon">✓</span>
            <strong>ADQA</strong>
            <small>ACT · REVIEW · REJECT</small>
          </div>
          <div className="how-arrow" aria-hidden>
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" />
            </svg>
          </div>
          <div className="how-node">
            <span className="how-node-icon">⚡</span>
            <strong>Act</strong>
            <small>Tools · shell · send</small>
          </div>
        </div>
      </section>

      <section className="how-panel">
        <h2 className="how-panel-title">Where the brain lives</h2>
        <div className="how-stack">
          <div className="how-box how-box-agent">
            <p className="how-box-sub">Path A · Default</p>
            <h3>Your AI on Desktop</h3>
            <p>
              Claude Code CLI or Codex CLI login with your subscription, or a BYOK API key stored
              under <code>~/.narna</code>. Mobile never logs into Claude/ChatGPT Pro inside the app.
            </p>
          </div>
          <div className="how-box how-box-adqa">
            <p className="how-box-sub">Path B · Optional</p>
            <h3>NARNA Pro cloud</h3>
            <p>
              Always-on hosting, sync, inbox, routines. Pro is not a Claude substitute — you still
              bring model access (BYOK) for tokens.
            </p>
          </div>
          <div className="how-box how-box-memory">
            <p className="how-box-sub">Safety layer</p>
            <h3>ADQA + Decision Memory</h3>
            <p>
              Score every proposed action. Keep outcomes so the next decision is better. This is
              what separates NARNA from a raw CLI bot.
            </p>
          </div>
        </div>
      </section>

      <section className="how-panel">
        <h2 className="how-panel-title">Start in 3 commands</h2>
        <pre className="code-block">{`pip install "narna[desktop]"
# claude login   or   codex login   or paste API key
narna desktop          # open Pairing → QR for phone`}</pre>
        <p className="section-desc" style={{ marginTop: "1rem" }}>
          Canonical write-up:{" "}
          <a href={BRAND.modelDoc} target="_blank" rel="noreferrer">
            docs/AGENT-BOT-MODEL.md
          </a>
        </p>
        <div className="land-cta" style={{ marginTop: "1.25rem" }}>
          <Link className="btn btn-primary" to="/download">
            Download Desktop
          </Link>
          <Link className="btn btn-secondary" to="/pricing">
            Pricing
          </Link>
          <a className="btn btn-secondary" href={BRAND.github} target="_blank" rel="noreferrer">
            GitHub
          </a>
        </div>
      </section>
    </div>
  );
}
