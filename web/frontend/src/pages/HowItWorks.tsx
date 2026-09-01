import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { BRAND } from "../brand";

function FlowArrow({ label }: { label?: string }) {
  return (
    <div className="how-arrow" aria-hidden>
      {label ? <span>{label}</span> : null}
      <svg viewBox="0 0 24 24" width="20" height="20">
        <path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
    </div>
  );
}

function LayerBox({
  title,
  sub,
  tone,
  children,
}: {
  title: string;
  sub: string;
  tone: "agent" | "adqa" | "memory" | "llm" | "cmem";
  children?: ReactNode;
}) {
  return (
    <div className={`how-box how-box-${tone}`}>
      <p className="how-box-sub">{sub}</p>
      <h3>{title}</h3>
      {children}
    </div>
  );
}

export default function HowItWorks() {
  return (
    <div className="layout-wide how-page how-visual">
      <header className="page-header how-hero">
        <p className="pill-label">How it works</p>
        <h1>Act → Verify → Learn</h1>
        <p className="how-hero-lead">
          Agent làm việc · ADQA chấm điểm · Memory nhớ bài học
        </p>
      </header>

      {/* Main flow */}
      <section className="how-panel">
        <h2 className="how-panel-title">Vòng lặp</h2>
        <div className="how-flow">
          <div className="how-node">
            <span className="how-node-icon">💬</span>
            <strong>Hỏi</strong>
          </div>
          <FlowArrow />
          <div className="how-node">
            <span className="how-node-icon">🧠</span>
            <strong>Suy luận</strong>
          </div>
          <FlowArrow />
          <div className="how-node how-node-accent">
            <span className="how-node-icon">✓</span>
            <strong>ADQA</strong>
            <small>DQS · Guardian</small>
          </div>
          <FlowArrow />
          <div className="how-node">
            <span className="how-node-icon">⚡</span>
            <strong>Hành động</strong>
          </div>
          <FlowArrow />
          <div className="how-node">
            <span className="how-node-icon">📚</span>
            <strong>Nhớ</strong>
          </div>
        </div>
      </section>

      {/* Stack diagram */}
      <section className="how-panel">
        <h2 className="how-panel-title">Kiến trúc</h2>
        <div className="how-stack">
          <LayerBox title="LLM của bạn" sub="Brain" tone="llm">
            <p>OpenRouter · OpenAI · Ollama · hoặc web Ask</p>
          </LayerBox>
          <div className="how-stack-connector" />
          <LayerBox title="NARNA Agent" sub="Runtime" tone="agent">
            <p>Chat · tools · browser · gateway</p>
          </LayerBox>
          <div className="how-stack-row">
            <LayerBox title="Memory" sub="Nhớ gì?" tone="memory">
              <p>MEMORY.md · FTS · lessons</p>
            </LayerBox>
            <LayerBox title="ADQA" sub="Đủ tốt?" tone="adqa">
              <p>ACT · REVIEW · REJECT</p>
            </LayerBox>
            <LayerBox title="CMEM" sub="Tùy chọn" tone="cmem">
              <p>Đồng bộ đa máy</p>
            </LayerBox>
          </div>
        </div>
      </section>

      {/* Memory upgrade visual */}
      <section className="how-panel how-panel-memory">
        <h2 className="how-panel-title">Memory — 3 tầng</h2>
        <div className="how-memory-lanes">
          <div className="how-lane">
            <span className="how-lane-tag">Hôm nay</span>
            <strong>Session + FTS</strong>
            <p>Mọi lượt chat được index · tìm lại theo nghĩa</p>
          </div>
          <div className="how-lane how-lane-mid">
            <span className="how-lane-tag">Lâu dài</span>
            <strong>MEMORY.md + lessons</strong>
            <p>DQS ≥ 70 → tự lưu bài học · USER/PROJECT profile</p>
          </div>
          <div className="how-lane">
            <span className="how-lane-tag">Đa thiết bị</span>
            <strong>CMEM bridge</strong>
            <p>
              <code>NARNA_CMEM_URL</code> ·{" "}
              <a href="https://cmem.ai/" target="_blank" rel="noreferrer">
                cmem.ai
              </a>
            </p>
          </div>
        </div>
        <p className="how-note">
          v0.2.9: recall FTS tăng · lessons gần đây luôn inject vào context
        </p>
      </section>

      {/* Devices */}
      <section className="how-panel">
        <h2 className="how-panel-title">Chạy ở đâu?</h2>
        <div className="how-devices">
          <div className="how-device how-device-ok">
            <span className="how-device-icon">🖥</span>
            <h3>Mac / Windows</h3>
            <p className="how-device-status">✓ Full agent</p>
            <ul>
              <li>Tools · shell · browser</li>
              <li>~50–200 MB app</li>
              <li>Data ~/.narna</li>
            </ul>
            <Link to="/download" className="btn btn-primary btn-sm">
              Download
            </Link>
          </div>
          <div className="how-device how-device-partial">
            <span className="how-device-icon">📱</span>
            <h3>iPhone / iPad</h3>
            <p className="how-device-status">◐ PWA Ask</p>
            <ul>
              <li>Add to Home Screen → /ask</li>
              <li>BYOK key trong Safari</li>
              <li>Không chạy Desktop binary</li>
            </ul>
            <Link to="/ask" className="btn btn-secondary btn-sm">
              Mở Ask
            </Link>
          </div>
          <div className="how-device how-device-partial">
            <span className="how-device-icon">🌐</span>
            <h3>Browser only</h3>
            <p className="how-device-status">◐ Ask + ADQA</p>
            <ul>
              <li>Không cần cài LLM local</li>
              <li>Cần API key hoặc mock</li>
              <li>Fair-use cloud</li>
            </ul>
            <Link to="/ask" className="btn btn-secondary btn-sm">
              Try Ask
            </Link>
          </div>
        </div>
      </section>

      {/* LLM without local download */}
      <section className="how-panel">
        <h2 className="how-panel-title">Chưa có LLM trên PC?</h2>
        <div className="how-llm-options">
          <div className="how-llm-card how-llm-yes">
            <h3>✓ Được — qua API</h3>
            <div className="how-llm-flow">
              <span>Bạn</span>
              <FlowArrow />
              <span>NARNA Ask</span>
              <FlowArrow />
              <span>OpenRouter / OpenAI</span>
            </div>
            <p>Paste key 1 lần · trả phí theo usage của provider · không tải model</p>
          </div>
          <div className="how-llm-card how-llm-no">
            <h3>✗ Chưa — điều khiển ChatGPT web</h3>
            <p>
              NARNA <strong>không</strong> tự login ChatGPT.com / Claude.ai thay bạn (anti-bot, ToS).
              Desktop có <code>browser_navigate</code> cho trang bạn mở — không phải thay LLM API.
            </p>
            <p className="how-note">Workaround: OpenRouter free tier · Ollama sau khi có GPU/RAM</p>
          </div>
        </div>
      </section>

      {/* MCP compact */}
      <section className="how-panel how-panel-compact">
        <h2 className="how-panel-title">MCP</h2>
        <div className="how-mcp-strip">
          <code>api.narna.org/mcp</code>
          <span>→</span>
          <span>ADQA · Ask · traces · CMEM enrich</span>
        </div>
        <Link to="/docs/integrations">Setup Cursor / OpenClaw →</Link>
      </section>

      <section className="how-cta-bar">
        <Link className="btn btn-primary" to="/download">
          Mac / Windows free
        </Link>
        <Link className="btn btn-secondary" to="/ask">
          iPhone / browser Ask
        </Link>
      </section>
    </div>
  );
}
