import { Link } from "react-router-dom";
import { BRAND, PRICING, SPEC } from "../brand";

const steps = [
  {
    n: "01",
    title: "Ask NARNA",
    desc: "Type a question in plain language. No MCP, no RAG jargon, no model picker.",
    code: "narna.org/ask",
  },
  {
    n: "02",
    title: "It reasons and checks quality",
    desc: "Model Router picks an LLM. ADQA scores the proposed answer — evidence, risk, policy, DQS.",
    code: "POST /v1/agent/ask → dqs + guardian",
  },
  {
    n: "03",
    title: "It remembers outcomes",
    desc: "Decision Memory stores what was decided and what happened — so the next ask is sharper.",
    code: "POST /v1/dmemory/{id}/outcome",
  },
];

const whyDiy = [
  "Policy engine + risk scoring",
  "Evidence & approval graphs",
  "Decision Memory store",
  "Outcome learning loop",
  "Model-agnostic router",
  "Cloud sync & API keys",
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
          <p className="land-kicker">New · Ask NARNA is live</p>
          <h1 className="land-brand">{BRAND.name}</h1>
          <p className="land-headline">Your AI agent that checks its own decisions.</p>
          <p className="land-lede">
            Ask anything. NARNA routes models, scores decision quality, and learns from outcomes —
            without making you install anything.
          </p>
          <div className="land-cta">
            <Link className="btn btn-primary" to="/ask">
              Ask NARNA
            </Link>
            <Link className="btn land-btn-ghost" to="/docs/install">
              {SPEC.install}
            </Link>
          </div>
          <p className="land-hero-meta">
            Free Ask · Personal $20/mo · Decision Quality Score
          </p>
        </div>
      </section>

      <section className="land-strip">
        <div className="layout-wide land-strip-grid">
          <div>
            <p className="land-strip-label">Chatbots</p>
            <p className="land-strip-q">Generate an answer.</p>
          </div>
          <div className="land-strip-vs" aria-hidden>
            →
          </div>
          <div>
            <p className="land-strip-label">NARNA Agent</p>
            <p className="land-strip-q land-strip-q-accent">
              Answer — then prove it is good enough to act on.
            </p>
          </div>
        </div>
      </section>

      <div className="layout-wide">
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
          <h2 className="land-h2">Ten checks. One score.</h2>
          <p className="land-desc">
            Behind Ask NARNA is Autonomous Decision Quality Assurance — the trust layer, not another
            chatbot.
          </p>
          <div className="land-attr-row">
            {attributes.map((a) => (
              <span key={a} className="land-attr">
                {a}
              </span>
            ))}
          </div>
          <pre className="code-block">{`{
  "dqs": 89,
  "guardian": "escalate",
  "attributes": { "evidence": 92, "policy": 100, "risk": 65 }
}`}</pre>
        </section>

        <section className="land-section land-split">
          <div>
            <p className="section-label">Why NARNA</p>
            <h2 className="land-h2">Model-agnostic. Quality-obsessed.</h2>
            <p className="land-desc">
              Bring your own LLM or use ours. NARNA owns routing, ADQA, and Decision Memory — not the
              foundation model.
            </p>
          </div>
          <div className="land-compare">
            <div>
              <p className="land-strip-label">Roll it yourself</p>
              <ul className="land-diy">
                {whyDiy.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div className="land-compare-win">
              <p className="land-strip-label">narna.org</p>
              <pre className="code-block">{`Ask NARNA → DQS
# or ${SPEC.install}
# ADQA · Decision Memory · Cloud`}</pre>
            </div>
          </div>
        </section>

        <section className="land-section" id="pricing">
          <p className="section-label">Pricing</p>
          <h2 className="land-h2">Start free on the web</h2>
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
          <h2 className="land-h2">Decision quality is your agent&apos;s superpower.</h2>
          <p className="land-desc">
            Ask once. See the DQS. Upgrade when you need memory everywhere and your own models.
          </p>
          <div className="land-cta">
            <Link className="btn btn-primary" to="/ask">
              Ask NARNA — free
            </Link>
            <a className="btn btn-secondary" href={BRAND.github} target="_blank" rel="noreferrer">
              Star on GitHub
            </a>
          </div>
        </section>
      </div>
    </>
  );
}
