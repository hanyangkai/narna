import { Link } from "react-router-dom";
import { BRAND, SPEC } from "../brand";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="layout-wide footer-inner">
        <div className="footer-brand">
          <Link to="/" style={{ textDecoration: "none" }}>
            <img
              src="/brand/narna-logo.png"
              alt="NARNA"
              style={{ height: 56, width: "auto", marginBottom: 8 }}
            />
          </Link>
          <p>
            {BRAND.oneLiner} {SPEC.install}. MIT open source.
          </p>
        </div>
        <div className="footer-col">
          <h4>Product</h4>
          <Link to="/how-it-works">Agent bot model</Link>
          <Link to="/download">Desktop bot</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/ask">Ask (browser)</Link>
          <Link to="/console/decision">Decision Console</Link>
        </div>
        <div className="footer-col">
          <h4>Open source</h4>
          <a href={BRAND.github} target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href={BRAND.modelDoc} target="_blank" rel="noreferrer">
            AGENT-BOT-MODEL.md
          </a>
          <Link to="/docs">Docs</Link>
          <Link to="/sdk">SDK</Link>
          <Link to="/compatibility">Integrations</Link>
        </div>
        <div className="footer-col">
          <h4>Community</h4>
          <a href={BRAND.discord} target="_blank" rel="noreferrer">
            Discord
          </a>
          <Link to="/docs/quickstart">Quickstart</Link>
          <Link to="/privacy">Privacy</Link>
          <Link to="/support">Support</Link>
          <Link to="/enterprise">Enterprise</Link>
        </div>
      </div>
      <div className="layout-wide footer-bottom">
        {BRAND.name} · Open-source AI agent bot · MIT
      </div>
      <div className="layout-wide footer-disclaimer">
        <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "1rem", textAlign: "center" }}>
          Provided as-is for research and open-source use. Claude / ChatGPT subscriptions are billed
          by Anthropic / OpenAI via Desktop CLI or API keys — NARNA Pro is hosting only.
        </p>
      </div>
    </footer>
  );
}
