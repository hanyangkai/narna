import { Link } from "react-router-dom";
import { BRAND, PRICING, SPEC } from "../brand";

const steps = [
  {
    n: "01",
    title: "Ask the agent",
    desc: "Chat in plain language. Tools, memory, skills, and BYOK models — like Hermes, with decision quality built in.",
    code: "narna.org/ask",
  },
  {
    n: "02",
    title: "ADQA scores the decision",
    desc: "Before you act: evidence, risk, policy, and confidence collapse into one Decision Quality Score + ACT / REVIEW / REJECT.",
    code: "POST /v1/adqa/evaluate → dqs + verdict",
  },
  {
    n: "03",
    title: "Trace · outcome · learn",
    desc: "Every answer becomes a Decision Trace. Record what happened. Replay with today's knowledge. The agent gets better.",
    code: "narna replay <traceId>",
  },
];

const layers = [
  {
    title: "NARNA Agent",
    role: "Do the work",
    points: ["Chat · tools · browser · code", "Skills · cron · multi-channel", "BYOK OpenRouter / OpenAI / Ollama"],
  },
  {
    title: "NARNA ADQA",
    role: "Make it better",
    points: ["Decision Quality Score", "Guardian verdicts", "Wrap Hermes / LangGraph / custom agents"],
  },
  {
    title: "Decision Memory",
    role: "Compound learning",
    points: ["Decision Traces", "Outcome learning", "Replay past decisions"],
  },
];

const attributes = [
  "Evidence",
  "Policy",
  "Context",
  "Memory",
  "Risk",
  "Alignment",
  "Capability",
  "Compliance",
  "Confidence",
  "Explanation",
];

export default function Landing() {
  return (
    <>
      <section className="hero hero-navy land-hero">
        <div className="layout-wide land-hero-inner">
          <p className="land-kicker">Open-source AI agent · Decision quality built in</p>
          <h1 className="land-brand">{BRAND.name}</h1>
          <p className="land-headline">An AI agent that gets better at making decisions.</p>
          <p className="land-lede">
            Borrow the agent runtime. Own the decision layer. NARNA routes models, runs tools, scores
            every answer with ADQA, and learns from outcomes — free, BYOK, no install required.
          </p>
          <div className="land-cta">
            <Link className="btn btn-primary" to="/ask">
              Try the agent
            </Link>
            <a className="btn land-btn-ghost" href={BRAND.github} target="_blank" rel="noreferrer">
              Star on GitHub
            </a>
          </div>
          <p className="land-hero-meta">
            Free forever · Bring your own key · Decision Trace + Replay
          </p>
        </div>
      </section>

      <section className="land-strip">
        <div className="layout-wide land-strip-grid">
          <div>
            <p className="land-strip-label">Typical agents</p>
            <p className="land-strip-q">More tools. More models. More chat.</p>
          </div>
          <div className="land-strip-vs" aria-hidden>
            →
          </div>
          <div>
            <p className="land-strip-label">NARNA</p>
            <p className="land-strip-q land-strip-q-accent">
              Was this decision actually good enough to act on?
            </p>
          </div>
        </div>
      </section>

      <div className="layout-wide">
        <section className="land-section">
          <p className="section-label">Three layers</p>
          <h2 className="land-h2">Agent · ADQA · Memory</h2>
          <p className="land-desc">
            The agent is distribution. ADQA + Decision Traces + Outcome Learning are the moat.
          </p>
          <div className="land-layers">
            {layers.map((L) => (
              <div key={L.title} className="land-layer">
                <p className="land-strip-label">{L.role}</p>
                <h3>{L.title}</h3>
                <ul>
                  {L.points.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section className="land-section">
          <p className="section-label">How it works</p>
          <h2 className="land-h2">Ask. Score. Learn.</h2>
          <ol className="land-howto">
            {steps.map((s) => (
              <li key={s.n} className="land-howto-item">
                <div className="land-howto-copy">
                  <span className="land-step-n">{s.n}</span>
                  <h3>{s.title}</h3>
                  <p>{s.desc}</p>
                </div>
                <pre className="code-block land-howto-term">{s.code}</pre>
              </li>
            ))}
          </ol>
        </section>

        <section className="land-section">
          <p className="section-label">ADQA</p>
          <h2 className="land-h2">Ten checks. One score. One verdict.</h2>
          <p className="land-desc">
            Wrap any agent — Hermes, Claude, LangGraph, or your own — with{" "}
            <code>narna.evaluate()</code>. You keep your stack. NARNA checks the decision.
          </p>
          <div className="land-attr-row">
            {attributes.map((a) => (
              <span key={a} className="land-attr">
                {a}
              </span>
            ))}
          </div>
          <pre className="code-block">{`from narna import evaluate
out = evaluate(action="contract.sign", evidence=["contract.reviewed"])
# → { "dqs": 89, "verdict": "ACT" | "REVIEW" | "REJECT" }`}</pre>
        </section>

        <section className="land-section land-split">
          <div>
            <p className="section-label">Why NARNA</p>
            <h2 className="land-h2">Not another Hermes clone.</h2>
            <p className="land-desc">
              Hermes already wins on tools and gateways. NARNA wins on whether the decision was good
              — and whether next time is better. Bring your own intelligence. We own quality.
            </p>
          </div>
          <div className="land-compare">
            <div>
              <p className="land-strip-label">You bring</p>
              <ul className="land-diy">
                <li>OpenRouter / OpenAI / Ollama keys</li>
                <li>Your existing agent stack (optional)</li>
                <li>Outcomes: did it work?</li>
              </ul>
            </div>
            <div className="land-compare-win">
              <p className="land-strip-label">NARNA adds</p>
              <pre className="code-block">{`Ask → tools → ADQA → Trace
Outcome → Learn → Replay
${SPEC.install}`}</pre>
            </div>
          </div>
        </section>

        <section className="land-section" id="pricing">
          <p className="section-label">Pricing</p>
          <h2 className="land-h2">Agent free forever. Quality scales.</h2>
          <p className="land-desc">{PRICING.subline}</p>
          <div className="land-price-row land-price-row-3">
            {PRICING.plans.map((p) => (
              <div
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
              </div>
            ))}
          </div>
          <p className="land-desc">{PRICING.enterpriseNote}</p>
        </section>

        <section className="land-section land-final">
          <h2 className="land-h2">Decision quality is the agent&apos;s superpower.</h2>
          <p className="land-desc">
            Use Hermes to work. Use Claude to think. Use NARNA to check whether the decision was good.
          </p>
          <div className="land-cta">
            <Link className="btn btn-primary" to="/ask">
              Try Ask NARNA
            </Link>
            <Link className="btn btn-secondary" to="/docs">
              Read the docs
            </Link>
          </div>
        </section>
      </div>
    </>
  );
}
