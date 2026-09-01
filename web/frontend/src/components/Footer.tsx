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
            {BRAND.tagline} Agent + ADQA + Decision Memory. {SPEC.install}.
          </p>
        </div>
        <div className="footer-col">
          <h4>Product</h4>
          <Link to="/signup">Sign up</Link>
          <Link to="/how-it-works">How it works</Link>
          <Link to="/ask">Ask Agent</Link>
          <Link to="/download">Desktop (Mac / Windows)</Link>
          <Link to="/pricing">Free</Link>
          <Link to="/settings/models">BYOK Models</Link>
          <Link to="/console/decision">Decision Console</Link>
        </div>
        <div className="footer-col">
          <h4>Developers</h4>
          <Link to="/docs">Docs</Link>
          <Link to="/sdk">SDK · evaluate()</Link>
          <Link to="/compatibility">Integrations</Link>
          <Link to="/benchmark">Benchmark</Link>
          <Link to="/specification">Specification</Link>
        </div>
        <div className="footer-col">
          <h4>Community</h4>
          <a href={BRAND.github} target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href={BRAND.discord} target="_blank" rel="noreferrer">
            Discord
          </a>
          <Link to="/docs/quickstart">Quickstart</Link>
        </div>
      </div>
      <div className="layout-wide footer-bottom">
        {BRAND.name} · {BRAND.primary} · MIT
      </div>
    </footer>
  );
}
