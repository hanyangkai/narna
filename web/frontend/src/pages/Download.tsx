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
    title: "Pair phone",
    win: "Desktop → Pairing → show QR",
    unix: "iOS / Android NARNA app scans QR",
    alt: "Phone remotes the bot — does not login Claude",
  },
  {
    title: "Chat + approve",
    win: "Tools, browser, memory, ADQA scoring",
    unix: "Risky actions need Allow on phone",
    alt: "Optional: narna gateway run for Telegram",
  },
];

export default function Download() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Desktop · Agent bot</p>
        <h1>Install the bot on your machine</h1>
        <p>
          NARNA Desktop is the <strong>agent bot</strong>. Use{" "}
          <strong>Claude CLI / Codex CLI</strong> (your subscription) or BYOK. Pair the phone with
          QR. No NARNA Pro fee required for local use.
        </p>
      </header>

      <section className="section">
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

        <h2>Setup</h2>
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
          Model explained:{" "}
          <a href={BRAND.modelDoc} target="_blank" rel="noreferrer">
            AGENT-BOT-MODEL.md
          </a>{" "}
          · AI connect:{" "}
          <Link to="/docs">docs</Link> ·{" "}
          <Link to="/how-it-works">How it works</Link>
        </p>
      </section>

      <section className="section">
        <h2>MacBook / Windows — portable</h2>
        <p className="section-desc">
          Grab zips from{" "}
          <a
            href="https://github.com/hanyangkai/narna/releases/latest"
            target="_blank"
            rel="noreferrer"
          >
            GitHub Releases
          </a>
          . Runs on <code>127.0.0.1</code> — Ask, tools, ADQA, Decision Memory.
        </p>
      </section>
    </div>
  );
}
