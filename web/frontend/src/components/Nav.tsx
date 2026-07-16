import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { BRAND } from "../brand";

const links = [
  { to: "/docs", label: "Docs" },
  { to: "/sdk", label: "SDK" },
  { to: "/specification", label: "Specification" },
  { to: "/enterprise", label: "Enterprise" },
  { to: "/pricing", label: "Pricing" },
];

export default function Nav() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const isConsole = pathname.startsWith("/console") || pathname.startsWith("/billing");

  return (
    <header className="site-header">
      <div className="layout nav">
        <Link to="/" className="nav-brand" onClick={() => setOpen(false)}>
          {BRAND.name}
        </Link>

        <button
          type="button"
          className="nav-toggle"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "✕" : "☰"}
        </button>

        {!isConsole && (
          <div className={`nav-links ${open ? "nav-links-open" : ""}`}>
            {links.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className={pathname === l.to || pathname.startsWith(l.to + "/") ? "active" : ""}
                onClick={() => setOpen(false)}
              >
                {l.label}
              </Link>
            ))}
            <a href={BRAND.github} target="_blank" rel="noreferrer" onClick={() => setOpen(false)}>
              GitHub
            </a>
          </div>
        )}
        {isConsole && (
          <div className={`nav-links ${open ? "nav-links-open" : ""}`}>
            <Link to="/docs" onClick={() => setOpen(false)}>Docs</Link>
            <Link to="/console" onClick={() => setOpen(false)}>Console</Link>
            <Link to="/billing" onClick={() => setOpen(false)}>Billing</Link>
          </div>
        )}
        <div className="nav-actions">
          <Link to="/docs/install" className="btn btn-primary" onClick={() => setOpen(false)}>
            Get Started
          </Link>
          <a href={BRAND.github} target="_blank" rel="noreferrer" className="btn btn-secondary nav-github-btn">
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
