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
              style={{ height: 48, width: "auto", marginBottom: 8 }}
            />
          </Link>
          <p>
            {BRAND.primary} {BRAND.tagline} {SPEC.name}: {SPEC.expand}.
          </p>
        </div>
        <div className="footer-col">
          <h4>Learn</h4>
          <Link to="/docs/what-is-narna">What is NARNA?</Link>
          <Link to="/docs/ugs">UGS Spec</Link>
          <Link to="/docs/constitution">Constitution</Link>
          <Link to="/specification">Specification</Link>
          <Link to="/compatibility">Compatibility</Link>
          <Link to="/benchmark">Benchmark</Link>
          <Link to="/sdk">SDK</Link>
          <Link to="/registry">Registry</Link>
          <Link to="/plugins">Plugins</Link>
          <Link to="/packages">Packages</Link>
        </div>
        <div className="footer-col">
          <h4>Product</h4>
          <Link to="/console">Cloud Console</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/enterprise">Enterprise</Link>
          <Link to="/billing">Billing</Link>
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
        {BRAND.name} · {BRAND.primary} · {SPEC.name} v0.1 · MIT
      </div>
    </footer>
  );
}
