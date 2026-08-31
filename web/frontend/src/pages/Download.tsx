import { Link } from "react-router-dom";
import { BRAND, SPEC } from "../brand";

const steps = [
  {
    title: "Download",
    win: "Windows or macOS zip — no Python needed",
    unix: "Or: pip install narna[desktop]",
    alt: "Hermes-like local agent on your PC",
  },
  {
    title: "Launch",
    win: "NARNA-Desktop.exe / NARNA-Desktop",
    unix: "narna desktop",
    alt: "Opens http://127.0.0.1:8765/",
  },
  {
    title: "Bring your key",
    win: "Setup wizard → paste OpenRouter / OpenAI / Ollama",
    unix: "Saved only under ~/.narna",
    alt: "BYOK — your keys never leave your machine",
  },
  {
    title: "Chat + tools",
    win: "Shell, browser, memory, ADQA scoring",
    unix: "Same agent runtime as cloud gateway",
    alt: "Optional: narna gateway run for Telegram later",
  },
];

export default function Download() {
  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Desktop</p>
        <h1>NARNA on your PC</h1>
        <p>
          Local agent on <strong>127.0.0.1</strong> — Ask, tools, ADQA, Decision Memory. Keys stay on
          disk. No cloud account required for the runtime.
        </p>
      </header>

      <section className="section">
        <div className="land-cta" style={{ marginBottom: "1.5rem" }}>
          <a
            className="btn btn-primary"
            href="https://github.com/hanyangkai/narna/releases/latest/download/NARNA-Desktop-windows.zip"
            target="_blank"
            rel="noreferrer"
          >
            Download Windows
          </a>
          <a
            className="btn btn-primary"
            href="https://github.com/hanyangkai/narna/releases/latest/download/NARNA-Desktop-macos.zip"
            target="_blank"
            rel="noreferrer"
          >
            Download macOS
          </a>
          <Link className="btn btn-secondary" to="/ask">
            Use in browser
          </Link>
        </div>

        <h2>macOS — portable (no Python)</h2>
        <p className="section-desc">
          Download <code>NARNA-Desktop-macos.zip</code> from{" "}
          <a
            href="https://github.com/hanyangkai/narna/releases/latest"
            target="_blank"
            rel="noreferrer"
          >
            GitHub Releases
          </a>
          , unzip, run <code>NARNA-Desktop</code> (or double-click in Finder).
        </p>
        <pre className="code-block">{`# Or build from source (maintainers)
bash scripts/build_desktop_mac.sh`}</pre>

        <h2>Windows — portable (no Python)</h2>
        <p className="section-desc">
          Latest release:{" "}
          <a
            href="https://github.com/hanyangkai/narna/releases/latest"
            target="_blank"
            rel="noreferrer"
          >
            GitHub Releases
          </a>
          — download <code>NARNA-Desktop-windows.zip</code>, unzip, run{" "}
          <code>NARNA-Desktop.exe</code>.
        </p>
        <pre className="code-block">{`# Or build from source (maintainers)
.\\scripts\\build_desktop_exe.ps1`}</pre>

        <h2>Windows — with Python</h2>
        <pre className="code-block">{`# PowerShell
irm https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.ps1 | iex
narna desktop`}</pre>

        <h2>macOS / Linux</h2>
        <pre className="code-block">{`curl -fsSL https://raw.githubusercontent.com/hanyangkai/narna/main/desktop/install.sh | bash
narna desktop`}</pre>

        <h2>Any OS — one-liner (like Hermes)</h2>
        <pre className="code-block">{`curl -fsSL https://raw.githubusercontent.com/hanyangkai/narna/main/scripts/install.sh | bash
narna desktop
narna browser setup    # optional Playwright
narna daemon install   # optional always-on`}</pre>

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
            <a href={`${BRAND.github}/tree/main/desktop`} target="_blank" rel="noreferrer">
              desktop/ on GitHub
            </a>
          </li>
        </ul>
        <p style={{ color: "var(--muted)", marginTop: "1rem" }}>
          Portable exe needs no Python. Pip path needs Python 3.11+. Data: <code>~/.narna</code>.
        </p>
      </section>
    </div>
  );
}
