import { Link } from "react-router-dom";
import { BRAND } from "../brand";

export default function Support() {
  return (
    <div className="layout-wide" style={{ maxWidth: 720, paddingTop: "2.5rem", paddingBottom: "4rem" }}>
      <header className="page-header">
        <p className="pill-label">Help</p>
        <h1>Support</h1>
        <p>Get the NARNA agent bot running — Desktop, phone, and Pro.</p>
      </header>

      <section className="section">
        <h2>Quick links</h2>
        <ul>
          <li>
            <Link to="/how-it-works">How the agent bot works</Link>
          </li>
          <li>
            <Link to="/download">Download Desktop</Link>
          </li>
          <li>
            <a href={BRAND.modelDoc} target="_blank" rel="noreferrer">
              AGENT-BOT-MODEL.md
            </a>
          </li>
          <li>
            <Link to="/docs">Docs</Link>
          </li>
          <li>
            <a href={BRAND.github} target="_blank" rel="noreferrer">
              GitHub issues
            </a>
          </li>
          <li>
            <a href={BRAND.discord} target="_blank" rel="noreferrer">
              Discord
            </a>
          </li>
        </ul>
      </section>

      <section className="section">
        <h2>Common setup</h2>
        <ol>
          <li>
            Install Desktop → login <strong>Claude CLI</strong> / <strong>Codex CLI</strong> or paste
            a BYOK key.
          </li>
          <li>
            Open Pairing → scan QR with the NARNA iOS/Android app.
          </li>
          <li>Chat and approve risky actions from the phone Inbox.</li>
          <li>
            Optional: subscribe to <strong>NARNA Pro</strong> in the App Store / Play for cloud
            always-on (still BYOK for model tokens).
          </li>
        </ol>
      </section>

      <section className="section">
        <h2>Billing</h2>
        <p>
          Manage mobile subscriptions in{" "}
          <a href="https://apps.apple.com/account/subscriptions" target="_blank" rel="noreferrer">
            Apple Subscriptions
          </a>{" "}
          or{" "}
          <a href="https://play.google.com/store/account/subscriptions" target="_blank" rel="noreferrer">
            Google Play Subscriptions
          </a>
          . Web Pro uses crypto checkout on narna.org only.
        </p>
      </section>

      <section className="section">
        <h2>Contact</h2>
        <p>
          Email{" "}
          <a href={`mailto:${BRAND.emailEnterprise}`}>{BRAND.emailEnterprise}</a> with your device,
          OS version, and a short description. For security issues, prefer a private GitHub security
          advisory when available.
        </p>
      </section>

      <p className="section-desc">
        <Link to="/privacy">Privacy Policy</Link> · <Link to="/">Home</Link>
      </p>
    </div>
  );
}
