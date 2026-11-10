import { Link } from "react-router-dom";
import { BRAND } from "../brand";

export default function Privacy() {
  return (
    <div className="layout-wide" style={{ maxWidth: 720, paddingTop: "2.5rem", paddingBottom: "4rem" }}>
      <header className="page-header">
        <p className="pill-label">Legal</p>
        <h1>Privacy Policy</h1>
        <p>Last updated: 10 November 2026 (Asia/Saigon)</p>
      </header>

      <section className="section">
        <h2>Who we are</h2>
        <p>
          NARNA ({BRAND.name}) is an open-source AI agent bot. Website:{" "}
          <a href="https://narna.org">narna.org</a>. Source:{" "}
          <a href={BRAND.github} target="_blank" rel="noreferrer">
            GitHub
          </a>
          . Contact:{" "}
          <a href={`mailto:${BRAND.emailEnterprise}`}>{BRAND.emailEnterprise}</a>.
        </p>
      </section>

      <section className="section">
        <h2>What the mobile apps collect</h2>
        <ul>
          <li>
            <strong>Account / pairing tokens</strong> — to link your phone to a Desktop or cloud
            bot (stored in Keychain / EncryptedSharedPreferences).
          </li>
          <li>
            <strong>Chat and approval traffic</strong> — messages and Allow/Deny actions you send
            through the paired bot or NARNA cloud API you configure.
          </li>
          <li>
            <strong>Purchase receipts</strong> — App Store / Google Play transaction tokens only,
            to unlock NARNA Pro hosting. We do not receive your full card number.
          </li>
          <li>
            <strong>Diagnostics (optional)</strong> — crash or connectivity errors if you enable
            them; no advertising ID sale.
          </li>
        </ul>
      </section>

      <section className="section">
        <h2>What we do not do</h2>
        <ul>
          <li>We do not sell personal data.</li>
          <li>
            We do not log into your Claude or ChatGPT account inside the mobile app. Model
            subscriptions stay on Desktop CLI or your own API keys (BYOK).
          </li>
          <li>We do not show crypto checkout inside iOS/Android apps.</li>
        </ul>
      </section>

      <section className="section">
        <h2>Where data lives</h2>
        <p>
          <strong>Desktop / Free path:</strong> keys and memory stay on your machine under{" "}
          <code>~/.narna</code> unless you enable cloud sync.
        </p>
        <p>
          <strong>NARNA Pro / cloud:</strong> bot state, inbox, and sync may be stored on NARNA
          hosted infrastructure you opt into, for the purpose of running the agent when your PC is
          off.
        </p>
      </section>

      <section className="section">
        <h2>Third parties</h2>
        <ul>
          <li>Apple App Store / Google Play — billing and entitlement.</li>
          <li>LLM providers you choose (Anthropic, OpenAI, etc.) — when you use BYOK or CLI.</li>
          <li>Optional channel providers (Telegram, Discord, …) when you enable the gateway.</li>
        </ul>
      </section>

      <section className="section">
        <h2>Your choices</h2>
        <p>
          Unpair the device, delete local app data, cancel Pro in the store subscription settings,
          or self-host and stop using NARNA cloud. For deletion requests email{" "}
          <a href={`mailto:${BRAND.emailEnterprise}`}>{BRAND.emailEnterprise}</a>.
        </p>
      </section>

      <section className="section">
        <h2>Children</h2>
        <p>NARNA is not directed at children under 13 (or the age required in your country).</p>
      </section>

      <p className="section-desc">
        <Link to="/support">Support</Link> · <Link to="/">Home</Link>
      </p>
    </div>
  );
}
