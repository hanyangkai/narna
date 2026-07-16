import { Link } from "react-router-dom";
import { BRAND, PROTOCOL } from "../brand";

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="layout-wide footer-inner">
        <div className="footer-brand">
          <strong>{BRAND.name}</strong>
          <p>
            {BRAND.tagline} Built on the {PROTOCOL.name} protocol and {PROTOCOL.expand}.
          </p>
        </div>
        <div className="footer-col">
          <h4>Standard</h4>
          <Link to="/specification">UAP Specification</Link>
          <Link to="/docs">Documentation</Link>
          <Link to="/sdk">NARNA SDK</Link>
          <Link to="/docs/examples">Examples</Link>
        </div>
        <div className="footer-col">
          <h4>Product</h4>
          <Link to="/console">NARNA Cloud</Link>
          <Link to="/pricing">Pricing</Link>
          <Link to="/enterprise">Enterprise</Link>
          <Link to="/billing">Billing</Link>
        </div>
        <div className="footer-col">
          <h4>Community</h4>
          <a href={BRAND.github} target="_blank" rel="noreferrer">GitHub</a>
          <a href={BRAND.discord} target="_blank" rel="noreferrer">Discord</a>
          <Link to="/docs/quickstart">Quickstart</Link>
        </div>
      </div>
      <div className="layout-wide footer-bottom">
        {BRAND.name} · {PROTOCOL.name} Spec v0.1 · MIT · {PROTOCOL.expand}
      </div>
    </footer>
  );
}
