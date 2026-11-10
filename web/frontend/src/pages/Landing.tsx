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
    body: "Install NARNA on Mac or Windows. Login Claude Code CLI or Codex CLI — or paste a BYOK API key.",
  },
  {
    n: "02",
    title: "Phone is the remote",
    body: "iOS / Android app pairs by QR. Chat, Allow/Deny, routines — heavy work stays on the PC.",
  },
  {
    n: "03",
    title: "ADQA is the brake",
    body: "Risky tools score evidence · risk · policy → ACT / REVIEW / REJECT before they run.",
  },
] as const;

const APP_SHOTS = [
  { src: "/store/01-onboarding.png", label: "Onboarding" },
  { src: "/store/02-bots.png", label: "Bots" },
  { src: "/store/03-inbox.png", label: "Inbox · Allow/Deny" },
  { src: "/store/04-chat.png", label: "Chat" },
] as const;

const TRACE_STEPS = [
  { label: "Bot got your message", detail: "phone" },
  { label: "Plan proposed", detail: "rm file" },
  { label: "ADQA risk", detail: "high" },
  { label: "Waiting Allow", detail: "Inbox" },
  { label: "Done", detail: "" },
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
        <p className="land-trace-user-label">You · phone app</p>
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
          <div className="land-trace-actions">
            <span className="land-chip">Deny</span>
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
              Agent bot on Desktop.
              <br />
              <span className="land-headline-accent">Remote from iOS &amp; Android.</span>
            </h1>
            <p className="land-lede">
              MausBot-style: Claude / Codex CLI on your PC (or BYOK). Phone app pairs by QR —
              chat, approve, routines. ADQA stops bad actions first.
            </p>
            <div className="land-cta">
              <a className="btn btn-primary" href="#get-app">
                Get the app
              </a>
              <Link className="btn btn-secondary" to="/download">
                Download Desktop
              </Link>
              <a className="btn land-btn-ghost" href={BRAND.github} target="_blank" rel="noreferrer">
                GitHub
              </a>
            </div>
            <p className="land-hero-meta">
              Free Desktop forever · App Store &amp; Google Play listing ready · Pro optional
            </p>
          </motion.div>

          <div className="land-hero-stage">
            <div className="land-hero-phones" aria-hidden>
              <img
                className="land-phone-shot land-phone-shot-back"
                src="/store/03-inbox.png"
                alt=""
                width={220}
                height={440}
              />
              <img
                className="land-phone-shot land-phone-shot-front"
                src="/store/02-bots.png"
                alt="NARNA mobile bots screen"
                width={240}
                height={480}
              />
            </div>
            <div className="land-hero-hud">
              <LiveBotPanel />
            </div>
          </div>
        </div>
      </section>

      {/* App UI gallery */}
      <section className="land-section" id="app-ui">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Bot app UI</p>
            <h2 className="land-h2 land-h2-wide">What you get on the phone</h2>
            <p className="land-desc">
              Onboarding (Desktop AI vs NARNA Pro) · Bots · Inbox Allow/Deny · Chat — same companion
              on iOS and Android.
            </p>
          </Reveal>
          <RevealStagger className="land-shot-row" stagger={0.08}>
            {APP_SHOTS.map((s) => (
              <RevealItem key={s.src} className="land-shot-card">
                <img src={s.src} alt={s.label} width={270} height={480} loading="lazy" />
                <p>{s.label}</p>
              </RevealItem>
            ))}
          </RevealStagger>
        </div>
      </section>

      {/* Get the app — iOS / Play / Desktop */}
      <section className="land-section land-get-app" id="get-app">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Download</p>
            <h2 className="land-h2 land-h2-wide">Get NARNA on every device</h2>
          </Reveal>
          <RevealStagger className="land-store-grid" stagger={0.1}>
            <RevealItem className="land-store-card">
              <p className="land-strip-label">iOS</p>
              <h3>App Store</h3>
              <p className="land-desc">
                Bundle <code>{BRAND.bundleId}</code>. Listing assets ready — submit from your Apple
                account to go live.
              </p>
              <a className="btn btn-primary" href={BRAND.appStoreUrl} target="_blank" rel="noreferrer">
                Open App Store search
              </a>
              <p className="land-store-note">Status: ready to upload · awaiting Submit for Review</p>
            </RevealItem>
            <RevealItem className="land-store-card">
              <p className="land-strip-label">Android</p>
              <h3>Google Play</h3>
              <p className="land-desc">
                Package <code>{BRAND.bundleId}</code>. Feature graphic + screenshots packed in repo.
              </p>
              <a className="btn btn-primary" href={BRAND.playStoreUrl} target="_blank" rel="noreferrer">
                Open Play listing
              </a>
              <p className="land-store-note">Status: ready to upload · awaiting Send for review</p>
            </RevealItem>
            <RevealItem className="land-store-card land-store-card-accent">
              <p className="land-strip-label">Desktop · available now</p>
              <h3>Mac &amp; Windows bot</h3>
              <p className="land-desc">
                The brain of the agent. Claude CLI / Codex / BYOK. Pair the phone after install.
              </p>
              <Link className="btn btn-secondary" to="/download">
                Download Desktop →
              </Link>
              <p className="land-store-note">Free forever · no NARNA fee</p>
            </RevealItem>
          </RevealStagger>
        </div>
      </section>

      <section className="land-section">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">The model</p>
            <h2 className="land-h2 land-h2-wide">Desktop bot · phone remote · ADQA gate</h2>
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

      <section className="land-section land-models-sec">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Intelligence</p>
            <h2 className="land-h2 land-h2-wide">Two paths. You pick the brain.</h2>
          </Reveal>
          <RevealStagger className="land-products" stagger={0.12}>
            <RevealItem>
              <div className="land-product">
                <p className="land-strip-label">Path A · Default</p>
                <h3>Your AI on Desktop</h3>
                <p className="land-desc" style={{ marginBottom: "1rem" }}>
                  Claude Code CLI or Codex CLI with your subscription — or BYOK. Phone never logs
                  into Claude inside the app.
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
                <h3>NARNA Pro</h3>
                <p className="land-desc" style={{ marginBottom: "1rem" }}>
                  Always-on cloud via App Store / Play IAP. Hosting only — model tokens stay BYOK.
                </p>
                <Link className="btn btn-secondary" to="/pricing">
                  See Pro $20 →
                </Link>
              </div>
            </RevealItem>
          </RevealStagger>
        </div>
      </section>

      <section className="land-section land-dev">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Open source</p>
            <h2 className="land-h2 land-h2-wide">MIT. Bot + ADQA + mobile in one repo.</h2>
          </Reveal>
          <RevealStagger className="land-dev-grid" stagger={0.08}>
            <RevealItem>
              <pre className="code-block">{SPEC.install}
narna desktop</pre>
            </RevealItem>
            <RevealItem>
              <pre className="code-block">{`# Pair phone QR
# Inbox Allow / Deny`}</pre>
            </RevealItem>
            <RevealItem>
              <pre className="code-block">{`pip / GitHub
apps/mobile-ios · android`}</pre>
            </RevealItem>
          </RevealStagger>
        </div>
      </section>

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

      <section className="land-final-strong">
        <ParticleNetwork className="fx-final-particles" />
        <div className="layout-wide land-center fx-final-content">
          <Reveal y={16}>
            <h2 className="land-final-h">
              Desktop brain. Phone remote.
              <br />
              <span className="land-final-accent">ADQA before it acts.</span>
            </h2>
            <div className="land-cta land-center-cta">
              <a className="btn btn-primary" href="#get-app">
                Get the app
              </a>
              <Link className="btn land-btn-ghost" to="/download">
                Desktop
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
