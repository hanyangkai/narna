import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { BRAND, PRICING, SPEC } from "../brand";
import ParticleNetwork from "../components/effects/ParticleNetwork";
import Reveal, { RevealItem, RevealStagger } from "../components/effects/Reveal";

const BOT_STEPS = [
  {
    n: "01",
    title: "Desktop is the bot",
    body: "Install NARNA on Mac or Windows. Login Claude Code CLI or Codex CLI with your subscription — or paste a BYOK API key.",
  },
  {
    n: "02",
    title: "Phone is the remote",
    body: "Scan the pairing QR. Chat, approve, and steer from iOS/Android while the heavy work stays on your PC.",
  },
  {
    n: "03",
    title: "ADQA is the brake",
    body: "Before shell, spend, or send-class actions, NARNA scores evidence · risk · policy → ACT / REVIEW / REJECT.",
  },
] as const;

const CHANNELS = [
  "Telegram",
  "WhatsApp",
  "Discord",
  "Slack",
  "X",
  "YouTube",
  "Desktop",
  "Mobile",
] as const;

const TRACE_STEPS = [
  { label: "Bot received message", detail: "Telegram" },
  { label: "Plan proposed", detail: "rm invoice.pdf" },
  { label: "ADQA risk check", detail: "high" },
  { label: "Human approval", detail: "phone" },
  { label: "Action executed", detail: "" },
] as const;

function LiveBotPanel() {
  const [step, setStep] = useState(0);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (step >= TRACE_STEPS.length + 1) {
      const reset = window.setTimeout(() => setStep(0), 2600);
      return () => window.clearTimeout(reset);
    }
    const t = window.setTimeout(() => setStep((s) => s + 1), step === 0 ? 500 : 700);
    return () => window.clearTimeout(t);
  }, [step]);

  const done = step > TRACE_STEPS.length;

  return (
    <motion.div
      className="land-trace"
      aria-label="Live agent bot demonstration"
      initial={reduce ? false : { opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: 0.15 }}
    >
      <div className="land-trace-bar">
        <span className="land-trace-dot" />
        <span>NARNA BOT</span>
        <span className="land-trace-live">LIVE</span>
      </div>
      <div className="land-trace-body">
        <p className="land-trace-user-label">You · phone</p>
        <p className="land-trace-user">&ldquo;Clean up the old invoice file.&rdquo;</p>
        <ul className="land-trace-checks">
          {TRACE_STEPS.map((s, i) => {
            const on = step > i;
            return (
              <li key={s.label} className={on ? "on" : ""}>
                <span className="land-check">{on ? "✓" : "·"}</span>
                <span>{s.label}</span>
                {s.detail ? <span className="land-trace-meta">{s.detail}</span> : null}
              </li>
            );
          })}
        </ul>
        <div className={`land-trace-verdict${done ? " land-trace-verdict-on" : ""}`}>
          <p className="land-strip-label">Decision Quality</p>
          <p className="land-dqs">{done ? "74" : "—"} <span>/ 100</span></p>
          <p className="land-rec">
            Recommendation: <strong>{done ? "REVIEW" : "…"}</strong>
          </p>
          <p className="land-conf">Delete needs your Allow on phone</p>
          <div className="land-trace-actions">
            <span className="land-chip">Reject</span>
            <span className="land-chip land-chip-accent">Allow</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function Landing() {
  const reduce = useReducedMotion();

  return (
    <>
      {/* Hero — agent bot first */}
      <section className="hero hero-navy land-hero fx-hero">
        <ParticleNetwork className="fx-hero-particles" />
        <div className="layout-wide land-hero-grid fx-hero-content">
          <motion.div
            className="land-hero-copy"
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="fx-status-pill">
              <span className="fx-status-dot" />
              Open-source AI agent bot
            </p>
            <p className="land-brand-mark" aria-hidden>
              NARNA
            </p>
            <h1 className="land-headline-main">
              Your AI agent bot.
              <br />
              <span className="land-headline-accent">Desktop brain. Phone remote.</span>
            </h1>
            <p className="land-lede">
              Run Claude or Codex on your PC with your subscription — or BYOK. Pair the phone.
              ADQA stops bad actions before they run. MIT open source.
            </p>
            <div className="land-cta">
              <Link className="btn btn-primary" to="/download">
                Download Desktop
              </Link>
              <a className="btn btn-secondary" href={BRAND.github} target="_blank" rel="noreferrer">
                GitHub
              </a>
              <Link className="btn land-btn-ghost" to="/how-it-works">
                How the bot works
              </Link>
            </div>
            <p className="land-hero-meta">
              Free forever on Desktop · Claude CLI / Codex CLI / BYOK · Pro = always-on cloud
            </p>
          </motion.div>

          <div className="land-hero-stage">
            <div className="land-hero-hud land-hero-hud-solo">
              <LiveBotPanel />
            </div>
          </div>
        </div>
      </section>

      {/* Model — 3 steps */}
      <section className="land-section">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">The model</p>
            <h2 className="land-h2 land-h2-wide">Same shape as MausBot — with a decision gate.</h2>
            <p className="land-desc">
              The bot lives on Desktop. Your phone (or Telegram / Discord) is the remote. ADQA is
              why NARNA is safer than a raw CLI agent.
            </p>
          </Reveal>
          <RevealStagger className="land-bot-steps" stagger={0.1}>
            {BOT_STEPS.map((s) => (
              <RevealItem key={s.n} className="land-bot-step">
                <span className="land-bot-n">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </RevealItem>
            ))}
          </RevealStagger>
        </div>
      </section>

      {/* Two paths */}
      <section className="land-section land-models-sec">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Intelligence</p>
            <h2 className="land-h2 land-h2-wide">Two paths. You pick who runs the brain.</h2>
          </Reveal>
          <RevealStagger className="land-products" stagger={0.12}>
            <RevealItem>
              <div className="land-product">
                <p className="land-strip-label">Path A · Default</p>
                <h3>Your AI on Desktop</h3>
                <p className="land-desc" style={{ marginBottom: "1rem" }}>
                  Login <strong>Claude Code CLI</strong> or <strong>Codex CLI</strong> with your
                  Pro subscription — or paste an API key. Phone only pairs; it never logs into
                  Claude inside the app.
                </p>
                <Link className="btn btn-primary" to="/download">
                  Setup Desktop →
                </Link>
              </div>
            </RevealItem>
            <p className="land-products-bridge">or</p>
            <RevealItem>
              <div className="land-product land-product-adqa">
                <p className="land-strip-label">Path B · Optional</p>
                <h3>NARNA Pro cloud</h3>
                <p className="land-desc" style={{ marginBottom: "1rem" }}>
                  Always-on when the PC is off: inbox, routines, sync. Still BYOK for model
                  tokens — Pro is hosting, not a Claude substitute.
                </p>
                <Link className="btn btn-secondary" to="/pricing">
                  See Pro $20 →
                </Link>
              </div>
            </RevealItem>
          </RevealStagger>
        </div>
      </section>

      {/* Channels */}
      <section className="land-section">
        <div className="layout-wide land-center">
          <Reveal>
            <p className="section-label">Everywhere</p>
            <h2 className="land-h2 land-h2-wide land-center-text">One bot. Many doors.</h2>
            <p className="land-lede-dark">Talk to the same agent from desktop, phone, or social.</p>
          </Reveal>
          <RevealStagger className="land-logo-grid" stagger={0.04}>
            {CHANNELS.map((c) => (
              <RevealItem key={c}>
                <span className="land-logo-cell">{c}</span>
              </RevealItem>
            ))}
          </RevealStagger>
        </div>
      </section>

      {/* Open source */}
      <section className="land-section land-dev">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Open source</p>
            <h2 className="land-h2 land-h2-wide">MIT. Inspect the bot. Fork the gate.</h2>
            <p className="land-desc">
              Runtime, ADQA, Desktop, gateway, and mobile companion live in one public repo.
              Read the canonical model:{" "}
              <a href={BRAND.modelDoc} target="_blank" rel="noreferrer">
                docs/AGENT-BOT-MODEL.md
              </a>
              .
            </p>
          </Reveal>
          <RevealStagger className="land-dev-grid" stagger={0.08}>
            <RevealItem>
              <pre className="code-block">{SPEC.install}
narna desktop
# Claude CLI / Codex CLI login → Pair QR</pre>
            </RevealItem>
            <RevealItem>
              <pre className="code-block">{`narna gateway run
# Telegram · Discord · Slack · …`}</pre>
            </RevealItem>
            <RevealItem>
              <pre className="code-block">{`# ADQA before act
ACT · REVIEW · REJECT`}</pre>
            </RevealItem>
          </RevealStagger>
          <Reveal delay={0.1}>
            <div className="land-cta">
              <a className="btn btn-primary" href={BRAND.github} target="_blank" rel="noreferrer">
                Star on GitHub
              </a>
              <Link className="btn btn-secondary" to="/docs">
                Docs
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      {/* Pricing */}
      <section className="land-section" id="pricing">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Pricing</p>
            <h2 className="land-h2">Bot free. Cloud optional.</h2>
            <p className="land-desc">{PRICING.philosophy}</p>
          </Reveal>
          <RevealStagger className="land-price-row land-price-row-3" stagger={0.08}>
            {PRICING.plans.map((p) => (
              <RevealItem
                key={p.id}
                className={`land-price${p.featured ? " land-price-featured" : ""}`}
              >
                <h3>{p.name}</h3>
                <p className="land-price-amt">
                  {p.price}
                  {p.period ? <span>{p.period}</span> : null}
                </p>
                <p className="land-price-limit">{p.limit}</p>
                <ul className="land-price-features">
                  {p.features.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
                <Link
                  to={p.ctaTo}
                  className={`btn ${p.featured ? "btn-primary" : "btn-secondary"}`}
                >
                  {p.cta}
                </Link>
              </RevealItem>
            ))}
          </RevealStagger>
        </div>
      </section>

      {/* Final */}
      <section className="land-final-strong">
        <ParticleNetwork className="fx-final-particles" />
        <div className="layout-wide land-center fx-final-content">
          <Reveal y={16}>
            <h2 className="land-final-h">
              An agent that can act —
              <br />
              <span className="land-final-accent">and knows when to wait for you.</span>
            </h2>
            <div className="land-cta land-center-cta">
              <Link className="btn btn-primary" to="/download">
                Download Desktop
              </Link>
              <a className="btn land-btn-ghost" href={BRAND.github} target="_blank" rel="noreferrer">
                GitHub
              </a>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
