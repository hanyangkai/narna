import { Link } from "react-router-dom";
import { BRAND, SPEC } from "../brand";

const steps = [
  {
    title: "Install",
    win: "irm …/desktop/install.ps1 | iex",
    unix: "curl -fsSL …/desktop/install.sh | bash",
    alt: `pip install "narna[desktop]"`,
  },
  {
    title: "Launch",
    win: "narna desktop",
    unix: "narna desktop",
    alt: "Double-click NARNA Desktop (Windows shortcut)",
  },
  {
    title: "Bring your key",
    win: "Paste OpenRouter / OpenAI / Ollama in the UI",
    unix: "Saved only under ~/.narna",
    alt: "No company LLM — BYOK forever",
  },
];

export default function Download() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Desktop</p>
        <h1>NARNA on your PC</h1>
        <p>
          Download the local agent — Ask, tools, ADQA, and Decision Memory run on{" "}
          <strong>127.0.0.1</strong>. Your API keys never leave the machine.
        </p>
      </header>

      <section className="section">
        <div className="land-cta" style={{ marginBottom: "1.5rem" }}>
          <a
            className="btn btn-primary"
            href="https://github.com/hanyangkai/narna/tree/main/desktop"
            target="_blank"
            rel="noreferrer"
          >
            Get Desktop pack
          </a>
          <Link className="btn btn-secondary" to="/ask">
            Use in browser instead
          </Link>
        </div>

        <h2>Windows</h2>
        <pre className="code-block">{`# PowerShell
irm https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.ps1 | iex
narna desktop`}</pre>

        <h2>macOS / Linux</h2>
        <pre className="code-block">{`curl -fsSL https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.sh | bash
narna desktop`}</pre>

        <h2>Any OS (pip)</h2>
        <pre className="code-block">{`${SPEC.install.replace("narna", 'narna[desktop]')}
narna desktop
# opens http://127.0.0.1:8765/`}</pre>
      </section>

      <section className="section">
        <h2>How it works</h2>
        <ol className="land-howto">
          {steps.map((s, i) => (
            <li key={s.title} className="land-howto-item">
              <div className="land-howto-copy">
                <span className="land-step-n">0{i + 1}</span>
                <h3>{s.title}</h3>
                <p>
                  {s.win}
                  <br />
                  <span style={{ color: "var(--muted)" }}>{s.unix}</span>
                </p>
              </div>
              <pre className="code-block land-howto-term">{s.alt}</pre>
            </li>
          ))}
        </ol>
      </section>

      <section className="section">
        <h2>Also available</h2>
        <ul className="land-diy">
          <li>
            <code>narna desktop --tui</code> — fullscreen terminal UI
          </li>
          <li>
            <code>narna chat</code> — simple REPL
          </li>
          <li>
            <a href={BRAND.github} target="_blank" rel="noreferrer">
              Source on GitHub
            </a>
          </li>
        </ul>
        <p style={{ color: "var(--muted)", marginTop: "1rem" }}>
          Requires Python 3.11+. Data lives in <code>~/.narna</code>.
        </p>
      </section>
    </div>
  );
}
