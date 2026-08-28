import { lazy, Suspense, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { BRAND, PRICING, SPEC } from "../brand";
import ParticleNetwork from "../components/effects/ParticleNetwork";
import ScanGrid from "../components/effects/ScanGrid";
import GlitchText from "../components/effects/GlitchText";
import AuroraOrbs from "../components/effects/AuroraOrbs";
import DataStream from "../components/effects/DataStream";
import Reveal, { RevealItem, RevealStagger } from "../components/effects/Reveal";

const HeroDecision3D = lazy(() => import("../components/effects/HeroDecision3D"));

const TRACE_STEPS = [
  { label: "Context collected", detail: "" },
  { label: "Evidence verified", detail: "12/12" },
  { label: "Policy checked", detail: "8/8" },
  { label: "Risk assessed", detail: "" },
  { label: "Alternatives evaluated", detail: "" },
] as const;

const PROBLEM_LINES = [
  { text: '"I have a plan."', ok: true },
  { text: '"I have tools."', ok: true },
  { text: '"I can act."', ok: true },
  { text: "But is it right?", ok: false },
] as const;

const AGENT_CAPS = [
  "Reason",
  "Research",
  "Remember",
  "Use tools",
  "Browse",
  "Code",
  "MCP",
  "Delegate",
  "Act",
] as const;

const ADQA_CAPS = [
  "Evidence",
  "Context",
  "Reasoning",
  "Risk",
  "Policy",
  "Alignment",
  "Confidence",
  "Outcome",
] as const;

const MODELS = [
  "GPT",
  "Claude",
  "Gemini",
  "DeepSeek",
  "Qwen",
  "Llama",
  "Mistral",
  "Your Model",
] as const;

const EXTERNAL_AGENTS = [
  "Hermes Agent",
  "Custom Agent",
  "LangGraph",
  "CrewAI",
  "Your Agent",
  "Enterprise Agent",
] as const;

const DEMO_SCORES = [
  { key: "Evidence", score: 92 },
  { key: "Context", score: 97 },
  { key: "Policy", score: 100 },
  { key: "Risk", score: 63 },
  { key: "Alignment", score: 91 },
  { key: "Confidence", score: 82 },
] as const;

const MEMORY_FLOW = [
  "Decision",
  "Action",
  "Outcome",
  "Success / Failure",
  "Decision Memory",
  "Future Decision",
] as const;

const REPLAY_STEPS = [
  "Original decision",
  "Original evidence",
  "Actual outcome",
  "What went wrong?",
  "Replay with current knowledge",
  "Would NARNA decide differently?",
] as const;

const ARCH_STEPS = [
  { label: "USER", kind: "node" as const },
  { label: "NARNA AGENT", kind: "node" as const },
  { label: "Memory · Tools · MCP", kind: "row" as const },
  { label: "REASONING → PROPOSED ACTION", kind: "node" as const },
  {
    label: "NARNA ADQA — Evidence · Context · Risk · Policy · Alignment · Confidence",
    kind: "highlight" as const,
  },
  { label: "APPROVE · REVIEW → ACT", kind: "node" as const },
  { label: "OUTCOME → DECISION MEMORY → LEARN", kind: "node" as const },
];

function DecisionTracePanel() {
  const [step, setStep] = useState(0);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (step >= TRACE_STEPS.length + 1) {
      const reset = window.setTimeout(() => setStep(0), 2800);
      return () => window.clearTimeout(reset);
    }
    const t = window.setTimeout(() => setStep((s) => s + 1), step === 0 ? 600 : 700);
    return () => window.clearTimeout(t);
  }, [step]);

  const done = step > TRACE_STEPS.length;

  const panel = (
    <div className="land-trace" aria-label="Live decision trace demonstration">
      <div className="land-trace-bar">
        <span className="land-trace-dot" />
        <span>NARNA AGENT</span>
        <span className="land-trace-live">LIVE</span>
      </div>
      <div className="land-trace-body">
        <p className="land-trace-user-label">User</p>
        <p className="land-trace-user">&ldquo;Should we approve this invoice?&rdquo;</p>
        <ul className="land-trace-checks">
          {TRACE_STEPS.map((s, i) => {
            const on = step > i;
            return (
              <motion.li
                key={s.label}
                className={on ? "on" : ""}
                animate={on ? { opacity: 1, x: 0 } : { opacity: 0.45, x: -4 }}
                transition={{ duration: 0.25 }}
              >
                <span className="land-check">{on ? "✓" : "·"}</span>
                <span>{s.label}</span>
                {s.detail ? <span className="land-trace-meta">{s.detail}</span> : null}
              </motion.li>
            );
          })}
        </ul>
        <motion.div
          className={`land-trace-verdict${done ? " land-trace-verdict-on" : ""}`}
          animate={done ? { scale: [0.98, 1.02, 1], opacity: 1 } : { opacity: 0.35 }}
          transition={{ duration: 0.45 }}
        >
          <p className="land-strip-label">Decision Quality</p>
          <p className="land-dqs">{done ? "91" : "—"} <span>/ 100</span></p>
          <p className="land-rec">
            Recommendation: <strong>{done ? "APPROVE" : "…"}</strong>
          </p>
          <p className="land-conf">Confidence: {done ? "94%" : "—"}</p>
          <div className="land-trace-actions">
            <span className="land-chip">View reasoning</span>
            <span className="land-chip land-chip-accent">Execute</span>
          </div>
        </motion.div>
      </div>
    </div>
  );

  if (reduce) return panel;

  return (
    <motion.div
      initial={{ opacity: 0, y: 32, rotateX: 8 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ duration: 0.85, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
      style={{ perspective: 900 }}
    >
      {panel}
    </motion.div>
  );
}

function ProblemFlow() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = window.setInterval(() => setI((v) => (v + 1) % (PROBLEM_LINES.length + 2)), 1100);
    return () => window.clearInterval(t);
  }, []);

  return (
    <div className="land-problem-anim" aria-hidden>
      <p className="land-problem-agent">AI Agent</p>
      {PROBLEM_LINES.map((line, idx) => (
        <div key={line.text} className={`land-problem-line${i > idx ? " on" : ""}${!line.ok ? " bad" : ""}`}>
          {!line.ok && i > idx ? <span className="land-x">✕</span> : null}
          <span>{line.text}</span>
        </div>
      ))}
    </div>
  );
}

function AdqaDemo() {
  const [prompt, setPrompt] = useState("Should I approve this $50,000 payment?");
  const [phase, setPhase] = useState<"idle" | "running" | "done">("idle");
  const [reveal, setReveal] = useState(0);

  function run() {
    setPhase("running");
    setReveal(0);
    let n = 0;
    const id = window.setInterval(() => {
      n += 1;
      setReveal(n);
      if (n >= DEMO_SCORES.length) {
        window.clearInterval(id);
        setPhase("done");
      }
    }, 220);
  }

  return (
    <div className="land-demo">
      <label className="land-demo-label" htmlFor="adqa-demo-input">
        Ask a decision
      </label>
      <div className="land-demo-row">
        <input
          id="adqa-demo-input"
          className="land-demo-input"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") run();
          }}
        />
        <button type="button" className="btn btn-primary" onClick={run} disabled={phase === "running"}>
          {phase === "running" ? "Scoring…" : "Run ADQA"}
        </button>
      </div>
      <div className="land-demo-bars">
        {DEMO_SCORES.map((s, idx) => {
          const show = reveal > idx;
          const width = show ? s.score : 0;
          return (
            <div key={s.key} className="land-bar">
              <span className="land-bar-key">{s.key}</span>
              <div className="land-bar-track">
                <motion.div
                  className={`land-bar-fill${s.score < 70 ? " warn" : ""}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${width}%` }}
                  transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
              <span className="land-bar-score mono">{show ? s.score : "—"}</span>
            </div>
          );
        })}
      </div>
      {phase === "done" ? (
        <motion.div
          className="land-demo-result"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <p className="land-dqs land-dqs-sm">
            Decision Quality: <strong>87</strong> / 100
          </p>
          <p className="land-verdict-badge review">REVIEW REQUIRED</p>
          <p className="land-demo-note">High risk due to unusual bank-account change.</p>
        </motion.div>
      ) : (
        <p className="land-demo-hint">Watch ADQA score evidence, policy, risk, and confidence in real time.</p>
      )}
    </div>
  );
}

function ReplayDemo() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!open) return;
    if (step >= REPLAY_STEPS.length) return;
    const t = window.setTimeout(() => setStep((s) => s + 1), 650);
    return () => window.clearTimeout(t);
  }, [open, step]);

  function start() {
    setOpen(true);
    setStep(0);
  }

  return (
    <div className="land-replay">
      <p className="land-replay-story">
        30 days ago, NARNA recommended <strong>supplier A</strong>.
      </p>
      <button type="button" className="btn btn-primary" onClick={start}>
        Replay Decision
      </button>
      {open ? (
        <ol className="land-replay-steps">
          {REPLAY_STEPS.map((s, i) => (
            <li key={s} className={step > i ? "on" : ""}>
              <span className="land-step-n">{String(i + 1).padStart(2, "0")}</span>
              {s}
            </li>
          ))}
        </ol>
      ) : null}
      {open && step >= REPLAY_STEPS.length ? (
        <p className="land-replay-out">
          With today&apos;s outcome data: <strong>REVIEW</strong> — supplier A missed SLA. Prefer supplier B.
        </p>
      ) : null}
    </div>
  );
}

export default function Landing() {
  const reduce = useReducedMotion();

  return (
    <>
      {/* 1. Hero — Decision first + live trace */}
      <section className="hero hero-navy land-hero fx-hero">
        <ParticleNetwork className="fx-hero-particles" />
        <div className="layout-wide land-hero-grid fx-hero-content">
          <motion.div
            className="land-hero-copy"
            initial={reduce ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          >
            <p className="fx-status-pill">
              <span className="fx-status-dot" />
              Decision quality infrastructure
            </p>
            <h1 className="land-headline-main">
              AI Agents can act.
              <br />
              <span className="land-headline-accent">NARNA makes them decide better.</span>
            </h1>
            <p className="land-lede">
              NARNA is an open-source AI Agent and Decision Quality Assurance infrastructure that helps
              AI agents reason, verify, evaluate risk, and learn from outcomes.
            </p>
            <div className="land-cta">
              <Link className="btn btn-primary" to="/ask">
                Try NARNA Free
              </Link>
              <Link className="btn btn-secondary" to="/download">
                Download Desktop
              </Link>
              <a
                className="btn land-btn-ghost"
                href={BRAND.github}
                target="_blank"
                rel="noreferrer"
              >
                GitHub →
              </a>
            </div>
            <p className="land-hero-meta">
              Hermes / OpenClaw for work — NARNA scores whether the decision was good.
            </p>
            <p className="land-model-row">
              GPT · Claude · Gemini · DeepSeek · Qwen · Local Models
            </p>
          </motion.div>

          <div className="land-hero-stage">
            {!reduce ? (
              <Suspense fallback={<div className="land-hero-3d fx-r3f-fallback" />}>
                <HeroDecision3D className="land-hero-3d" />
              </Suspense>
            ) : null}
            <div className="land-hero-hud">
              <DecisionTracePanel />
            </div>
          </div>
        </div>
      </section>

      {/* 3. The problem — core story */}
      <section className="land-problem">
        <div className="layout-wide">
          <Reveal>
            <h2 className="land-h2 land-h2-wide">
              AI can be intelligent and still make bad decisions.
            </h2>
          </Reveal>
          <div className="land-problem-grid">
            <Reveal delay={0.1}>
              <ProblemFlow />
            </Reveal>
            <Reveal delay={0.2}>
              <div className="land-problem-fix">
                <h3 className="land-h3">That&apos;s where NARNA comes in.</h3>
                <ol className="land-flow-list">
                  <li>Agent</li>
                  <li>Proposed Decision</li>
                  <li className="accent">NARNA ADQA</li>
                  <li>Verify · Challenge · Score</li>
                  <li className="strong">ACT / REVIEW / REJECT</li>
                </ol>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* 4. Two products */}
      <section className="land-section">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Products</p>
            <h2 className="land-h2 land-h2-wide">Two layers. One job: better decisions.</h2>
          </Reveal>
          <RevealStagger className="land-products" stagger={0.12}>
            <RevealItem>
              <div className="land-product">
                <p className="land-strip-label">NARNA Agent</p>
                <h3>An agent that works.</h3>
                <div className="land-cap-cloud">
                  {AGENT_CAPS.map((c) => (
                    <span key={c}>{c}</span>
                  ))}
                </div>
                <Link className="btn btn-primary" to="/ask">
                  Try NARNA Agent →
                </Link>
              </div>
            </RevealItem>
            <p className="land-products-bridge">Use NARNA Agent. Or bring your own agent.</p>
            <RevealItem>
              <div className="land-product land-product-adqa">
                <p className="land-strip-label">NARNA ADQA</p>
                <h3>A decision layer for every agent.</h3>
                <div className="land-cap-cloud">
                  {ADQA_CAPS.map((c) => (
                    <span key={c}>{c}</span>
                  ))}
                </div>
                <Link className="btn btn-secondary" to="/console/decision">
                  Explore ADQA →
                </Link>
              </div>
            </RevealItem>
          </RevealStagger>
        </div>
      </section>

      {/* 5. Architecture diagram */}
      <section className="land-arch-section">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">How NARNA works</p>
            <h2 className="land-h2 land-h2-wide">Think → Verify → Decide → Learn</h2>
            <p className="land-desc">
              The agent proposes. ADQA scores. Outcomes become Decision Memory. Next time is better.
            </p>
          </Reveal>
          <RevealStagger as="ol" className="land-arch" stagger={0.07} aria-label="NARNA architecture">
            {ARCH_STEPS.map((n) => (
              <RevealItem
                key={n.label}
                as="li"
                className={`land-arch-step land-arch-${n.kind}`}
              >
                {n.label}
              </RevealItem>
            ))}
          </RevealStagger>
        </div>
      </section>

      {/* 6. Doesn't replace your AI */}
      <section className="land-section land-models-sec">
        <div className="layout-wide land-center">
          <Reveal>
            <h2 className="land-h2 land-h2-wide land-center-text">
              NARNA doesn&apos;t replace your AI.
            </h2>
            <p className="land-lede-dark">
              Bring the intelligence you trust.
              <br />
              NARNA improves how it decides.
            </p>
          </Reveal>
          <RevealStagger className="land-logo-grid" stagger={0.05}>
            {MODELS.map((m) => (
              <RevealItem key={m}>
                <span className="land-logo-cell">{m}</span>
              </RevealItem>
            ))}
          </RevealStagger>
          <Reveal delay={0.15}>
            <div className="land-stack-arrow" aria-hidden>
              ↓
            </div>
            <p className="land-stack-mid">NARNA ADQA</p>
            <div className="land-stack-arrow" aria-hidden>
              ↓
            </div>
            <p className="land-stack-end">Better Decisions</p>
          </Reveal>
        </div>
      </section>

      {/* 7. Bring your agent */}
      <section className="land-section land-bya">
        <div className="layout-wide">
          <Reveal>
            <h2 className="land-h2 land-h2-wide">Don&apos;t replace your agent. Upgrade it.</h2>
          </Reveal>
          <div className="land-bya-grid">
            <RevealStagger as="ul" className="land-bya-list" stagger={0.06}>
              {EXTERNAL_AGENTS.map((a) => (
                <RevealItem key={a} as="li">
                  <span>{a}</span>
                  <span className="land-bya-line" aria-hidden />
                </RevealItem>
              ))}
            </RevealStagger>
            <Reveal delay={0.2}>
              <div className="land-bya-target">
                <strong>NARNA ADQA</strong>
                <p>One API. Any Agent. Better Decisions.</p>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      {/* 8. Interactive ADQA demo */}
      <section className="land-section land-demo-sec">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Live demo</p>
            <h2 className="land-h2 land-h2-wide">See decision quality in 15 seconds.</h2>
            <p className="land-desc">
              No docs required. Run a sample decision and watch ADQA score it.
            </p>
          </Reveal>
          <Reveal delay={0.12}>
            <AdqaDemo />
          </Reveal>
        </div>
      </section>

      {/* 9. Memory */}
      <section className="land-section">
        <div className="layout-wide land-split-mem">
          <Reveal>
            <div>
              <p className="section-label">Decision Memory</p>
              <h2 className="land-h2">Agents remember. NARNA learns from decisions.</h2>
              <p className="land-desc">
                Memory helps an agent remember what happened. NARNA helps it understand what it should
                do differently next time.
              </p>
            </div>
          </Reveal>
          <RevealStagger as="ol" className="land-mem-flow" stagger={0.08}>
            {MEMORY_FLOW.map((s) => (
              <RevealItem key={s} as="li">
                {s}
              </RevealItem>
            ))}
          </RevealStagger>
        </div>
      </section>

      {/* 10. Decision Replay */}
      <section className="land-section land-replay-sec">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Decision Replay</p>
            <h2 className="land-h2 land-h2-wide">Not a chatbot. A decision system.</h2>
            <p className="land-desc">
              Replay past decisions against today’s knowledge. See what would change — and why.
            </p>
          </Reveal>
          <Reveal delay={0.1}>
            <ReplayDemo />
          </Reveal>
        </div>
      </section>

      {/* 11. Developers */}
      <section className="land-section land-dev">
        <div className="layout-wide">
          <Reveal>
            <h2 className="land-h2 land-h2-wide">Open source. Model agnostic. Built for agents.</h2>
          </Reveal>
          <RevealStagger className="land-dev-grid" stagger={0.1}>
            <RevealItem>
              <pre className="code-block">{SPEC.install}</pre>
            </RevealItem>
            <RevealItem>
              <pre className="code-block">{`// OpenClaw ~/.openclaw/openclaw.json
"mcp": { "servers": { "narna": {
  "url": "https://api.narna.org/mcp",
  "headers": { "Authorization": "Bearer uap_live_…" }
}}}}`}</pre>
            </RevealItem>
            <RevealItem>
              <pre className="code-block">narna evaluate · narna_agent_ask (MCP)</pre>
            </RevealItem>
          </RevealStagger>
          <Reveal delay={0.12}>
            <p className="land-desc" style={{ marginTop: "1rem" }}>
              OpenClaw skill:{" "}
              <a href={`${BRAND.github}/blob/main/plugins/narna-openclaw/SKILL.md`} target="_blank" rel="noreferrer">
                plugins/narna-openclaw
              </a>
            </p>
          </Reveal>
          <Reveal delay={0.15}>
            <div className="land-cta">
              <Link className="btn btn-secondary" to="/docs">
                Read the Docs
              </Link>
              <a className="btn btn-primary" href={BRAND.github} target="_blank" rel="noreferrer">
                Star on GitHub
              </a>
            </div>
          </Reveal>
        </div>
      </section>

      {/* 12. Pricing */}
      <section className="land-section" id="pricing">
        <div className="layout-wide">
          <Reveal>
            <p className="section-label">Pricing</p>
            <h2 className="land-h2">Simple. Start free.</h2>
            <p className="land-desc">{PRICING.subline}</p>
          </Reveal>
          <RevealStagger className="land-price-row land-price-row-4" stagger={0.08}>
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
            <RevealItem className="land-price">
              <h3>Enterprise</h3>
              <p className="land-price-amt">Custom</p>
              <p className="land-price-limit">Private deployment</p>
              <ul className="land-price-features">
                <li>Private deployment</li>
                <li>Enterprise data &amp; governance</li>
                <li>SSO · Audit · SLA</li>
              </ul>
              <Link to="/enterprise" className="btn btn-secondary">
                Contact us
              </Link>
            </RevealItem>
          </RevealStagger>
        </div>
      </section>

      {/* 13. Final CTA */}
      <section className="land-final-strong">
        <ParticleNetwork className="fx-final-particles" />
        <div className="layout-wide land-center fx-final-content">
          <Reveal y={16}>
            <h2 className="land-final-h">
              The next generation of AI won&apos;t just act.
              <br />
              <span className="land-final-accent">It will know when it should.</span>
            </h2>
            <p className="land-final-cta-label">Build with NARNA.</p>
            <div className="land-cta land-center-cta">
              <Link className="btn btn-primary" to="/ask">
                Try NARNA Free
              </Link>
              <Link className="btn land-btn-ghost" to="/docs">
                Read the Docs
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
