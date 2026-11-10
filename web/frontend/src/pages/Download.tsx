import { Link } from "react-router-dom";
import { BRAND, SPEC } from "../brand";

const steps = [
  {
    title: "Download Desktop",
    win: "macOS or Windows zip — no Python needed",
    unix: `Or: ${SPEC.install}`,
    alt: "This machine is the agent bot",
  },
  {
    title: "Connect AI",
    win: "Claude Code CLI or Codex CLI → login with your subscription",
    unix: "Or paste OpenAI / Anthropic / OpenRouter / Ollama key",
    alt: "Keys stay under ~/.narna — BYOK",
  },
  {
    title: "Install phone app",
    win: "iOS App Store / Google Play — package org.narna.mobile",
    unix: "Or build from apps/mobile-ios · apps/mobile-android",
    alt: "Phone remotes the bot — does not login Claude",
  },
  {
    title: "Pair + approve",
    win: "Desktop → Pairing → QR → chat & Inbox Allow/Deny",
    unix: "ADQA scores risky tools before they run",
    alt: "Optional: narna gateway run for Telegram",
  },
];

export default function Download() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Download · Agent bot</p>
        <h1>Desktop bot + iOS / Android remote</h1>
        <p>
          Desktop is the brain. The phone app is the remote. Use{" "}
          <strong>Claude CLI / Codex CLI</strong> or BYOK on the PC, then pair by QR.
        </p>
      </header>

      <section className="section" id="mobile">
        <h2>Mobile companion</h2>
        <div className="land-store-grid" style={{ marginTop: "1rem" }}>
          <article className="land-store-card">
            <p className="land-strip-label">iOS</p>
            <h3>App Store</h3>
            <p className="section-desc">
              Bundle ID <code>{BRAND.bundleId}</code>. Screenshots &amp; metadata in repo — submit
              from App Store Connect.
            </p>
            <a className="btn btn-primary" href={BRAND.appStoreUrl} target="_blank" rel="noreferrer">
              App Store search
            </a>
          </article>
          <article className="land-store-card">
            <p className="land-strip-label">Android</p>
            <h3>Google Play</h3>
            <p className="section-desc">
              Package <code>{BRAND.bundleId}</code>. Feature graphic + phone shots ready to upload.
            </p>
            <a className="btn btn-primary" href={BRAND.playStoreUrl} target="_blank" rel="noreferrer">
              Play listing
            </a>
          </article>
          <article className="land-store-card land-store-card-accent">
            <p className="land-strip-label">See the UI</p>
            <h3>App screenshots</h3>
            <p className="section-desc">Onboarding · Bots · Inbox · Chat</p>
            <Link className="btn btn-secondary" to="/#app-ui">
              View on homepage →
            </Link>
          </article>
        </div>
      </section>

      <section className="section">
        <h2>Desktop (available now)</h2>
        <div className="land-cta" style={{ marginBottom: "1.5rem" }}>
          <a
            className="btn btn-primary"
            href="https://github.com/hanyangkai/narna/releases/latest/download/NARNA-Desktop-macos.zip"
            target="_blank"
            rel="noreferrer"
          >
            Download for Mac
          </a>
          <a
            className="btn btn-primary"
            href="https://github.com/hanyangkai/narna/releases/latest/download/NARNA-Desktop-windows.zip"
            target="_blank"
            rel="noreferrer"
          >
            Download for Windows
          </a>
          <a className="btn btn-secondary" href={BRAND.github} target="_blank" rel="noreferrer">
            Source on GitHub
          </a>
        </div>

        <div className="download-steps">
          {steps.map((s) => (
            <article key={s.title} className="card feature-card">
              <h3>{s.title}</h3>
              <p>{s.win}</p>
              <p className="section-desc">{s.unix}</p>
              <p className="section-desc">
                <em>{s.alt}</em>
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>CLI</h2>
        <pre className="code-block">{`${SPEC.install}
narna desktop
narna gateway status`}</pre>
        <p className="section-desc" style={{ marginTop: "1rem" }}>
          Model:{" "}
          <a href={BRAND.modelDoc} target="_blank" rel="noreferrer">
            AGENT-BOT-MODEL.md
          </a>{" "}
          · <Link to="/how-it-works">How it works</Link> · <Link to="/privacy">Privacy</Link>
        </p>
      </section>
    </div>
  );
}
