import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  askNarna,
  listAgentSkills,
  recordAgentOutcome,
  type AgentAskResponse,
} from "../api";
import { BRAND } from "../brand";

type ChatItem = {
  role: "user" | "assistant";
  text: string;
  meta?: AgentAskResponse;
  feedback?: "up" | "down";
};

function readFileAsText(file: File): Promise<{ name: string; text: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () =>
      resolve({ name: file.name, text: String(reader.result || "").slice(0, 12000) });
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

export default function Ask() {
  const [input, setInput] = useState("");
  const [items, setItems] = useState<ChatItem[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<Array<{ name: string; text: string }>>([]);
  const [showModels, setShowModels] = useState(false);
  const [quota, setQuota] = useState<{ used?: number; hard?: number | null }>({});
  const [installHint, setInstallHint] = useState(false);
  const [skills, setSkills] = useState<Array<{ skillId: string; name: string }>>([]);
  const [showSkills, setShowSkills] = useState(false);
  const [showLlm, setShowLlm] = useState(() => !localStorage.getItem("narna_llm_key"));
  const [llmProvider, setLlmProvider] = useState(
    () => localStorage.getItem("narna_llm_provider") || "openrouter"
  );
  const [llmApiKey, setLlmApiKey] = useState(() => localStorage.getItem("narna_llm_key") || "");
  const [llmModel, setLlmModel] = useState(() => localStorage.getItem("narna_llm_model") || "");
  const [askMode, setAskMode] = useState(
    () => localStorage.getItem("narna_ask_mode") || "cheap"
  );
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const deferredPrompt = useRef<{ prompt: () => Promise<void> } | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [items, loading]);

  useEffect(() => {
    const onBip = (e: Event) => {
      e.preventDefault();
      deferredPrompt.current = e as unknown as { prompt: () => Promise<void> };
      setInstallHint(true);
    };
    window.addEventListener("beforeinstallprompt", onBip);
    return () => window.removeEventListener("beforeinstallprompt", onBip);
  }, []);

  useEffect(() => {
    const apiKey = localStorage.getItem("uap_api_key") || undefined;
    listAgentSkills(apiKey)
      .then(setSkills)
      .catch(() => setSkills([]));
  }, [items.length]);

  const onInstall = async () => {
    const p = deferredPrompt.current;
    if (!p) return;
    await p.prompt();
    setInstallHint(false);
  };

  const onFeedback = async (idx: number, status: "success" | "fail") => {
    const item = items[idx];
    if (!item?.meta?.decisionId || item.feedback) return;
    try {
      const apiKey = localStorage.getItem("uap_api_key") || undefined;
      await recordAgentOutcome(item.meta.decisionId, {
        apiKey,
        status,
        lesson:
          status === "success"
            ? "User marked outcome helpful"
            : "User marked outcome not helpful — revise approach",
      });
      setItems((prev) =>
        prev.map((row, i) =>
          i === idx ? { ...row, feedback: status === "success" ? "up" : "down" } : row
        )
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const onSend = async () => {
    const message = input.trim();
    if (!message || loading) return;
    // Hermes-like slash commands
    const lower = message.toLowerCase();
    if (lower === "/new" || lower === "/reset") {
      setSessionId(undefined);
      setItems([]);
      setInput("");
      return;
    }
    if (lower === "/clear") {
      setItems([]);
      setInput("");
      return;
    }
    if (lower === "/skills") {
      setShowSkills(true);
      setInput("");
      return;
    }
    if (lower === "/help") {
      setItems((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            "Slash commands: /help /new /clear /skills /tools /model [id] /provider [name] /memory [q] /jobs /cron <nl>",
        },
      ]);
      setInput("");
      return;
    }
    if (lower === "/tools") {
      setItems((prev) => [
        ...prev,
        {
          role: "assistant",
          text:
            "Tools: web_search, web_fetch, calculator, code_exec, shell_exec, browser_*, datetime_now, workspace_*, memory_*, delegate_*, skill_*, http_request, image_gen, vision_describe, schedule_job, jobs_list, profile_*",
        },
      ]);
      setInput("");
      return;
    }
    if (lower === "/model" || lower.startsWith("/model ")) {
      const rest = message.slice(6).trim();
      if (rest) {
        setLlmModel(rest);
        localStorage.setItem("narna_llm_model", rest);
        setItems((prev) => [
          ...prev,
          { role: "assistant", text: `Model set to ${rest}` },
        ]);
      } else {
        setShowLlm(true);
        setItems((prev) => [
          ...prev,
          {
            role: "assistant",
            text: `Current model: ${llmModel || "(provider default)"} · provider ${llmProvider}`,
          },
        ]);
      }
      setInput("");
      return;
    }
    if (lower === "/provider" || lower.startsWith("/provider ")) {
      const rest = message.slice(9).trim().toLowerCase();
      if (rest && ["openrouter", "openai", "ollama", "mock"].includes(rest)) {
        setLlmProvider(rest);
        localStorage.setItem("narna_llm_provider", rest);
        setItems((prev) => [
          ...prev,
          { role: "assistant", text: `Provider set to ${rest}` },
        ]);
      } else {
        setShowLlm(true);
        setItems((prev) => [
          ...prev,
          { role: "assistant", text: `Provider: ${llmProvider}. Use /provider openrouter|openai|ollama|mock` },
        ]);
      }
      setInput("");
      return;
    }
    if (lower === "/memory" || lower.startsWith("/memory ")) {
      const q = message.slice(7).trim() || "recent";
      setInput("");
      setItems((prev) => [...prev, { role: "user", text: message }]);
      setLoading(true);
      try {
        const apiKey = localStorage.getItem("uap_api_key") || undefined;
        const resp = await askNarna(
          `Use memory_search tool with query "${q}" then summarize the top lessons for me.`,
          {
            apiKey,
            sessionId,
            mode: askMode,
            llmProvider: llmApiKey ? llmProvider : undefined,
            llmApiKey: llmApiKey || undefined,
            llmModel: llmApiKey && llmModel ? llmModel : undefined,
          }
        );
        setSessionId(resp.sessionId);
        setItems((prev) => [...prev, { role: "assistant", text: resp.answer, meta: resp }]);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
      return;
    }
    if (lower === "/jobs") {
      setItems((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Use /cron <natural language> to schedule, e.g. /cron every day remind me to review risk. Or ask: list my jobs.",
        },
      ]);
      setInput("");
      return;
    }
    if (lower.startsWith("/cron ")) {
      const nl = message.slice(6).trim();
      setInput("");
      setItems((prev) => [...prev, { role: "user", text: message }]);
      setLoading(true);
      try {
        const apiKey = localStorage.getItem("uap_api_key") || undefined;
        const resp = await askNarna(
          `Schedule this with the schedule_job tool (natural language): ${nl}`,
          {
            apiKey,
            sessionId,
            mode: askMode,
            llmProvider: llmApiKey ? llmProvider : undefined,
            llmApiKey: llmApiKey || undefined,
            llmModel: llmApiKey && llmModel ? llmModel : undefined,
          }
        );
        setSessionId(resp.sessionId);
        setItems((prev) => [...prev, { role: "assistant", text: resp.answer, meta: resp }]);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
      return;
    }
    setError(null);
    if (!llmApiKey) {
      setShowLlm(true);
    }
    setInput("");
    setItems((prev) => [...prev, { role: "user", text: message }]);
    setLoading(true);
    try {
      localStorage.setItem("narna_llm_provider", llmProvider);
      if (llmApiKey) localStorage.setItem("narna_llm_key", llmApiKey);
      if (llmModel) localStorage.setItem("narna_llm_model", llmModel);
      localStorage.setItem("narna_ask_mode", askMode);
      const apiKey = localStorage.getItem("uap_api_key") || undefined;
      const resp = await askNarna(message, {
        apiKey,
        sessionId,
        files,
        showModels,
        challenge: false,
        mode: askMode,
        llmProvider: llmApiKey ? llmProvider : undefined,
        llmApiKey: llmApiKey || undefined,
        llmModel: llmApiKey && llmModel ? llmModel : undefined,
      });
      setSessionId(resp.sessionId);
      setFiles([]);
      setQuota({
        used: resp.agentTurnsInPeriod,
        hard: resp.agentTurnsHardCap ?? null,
      });
      setItems((prev) => [...prev, { role: "assistant", text: resp.answer, meta: resp }]);
    } catch (e) {
      const text = e instanceof Error ? e.message : String(e);
      setError(text);
      if (text.includes("402") || text.toLowerCase().includes("quota")) {
        setError(
          "Hosted Ask fair-use limit reached. Use Desktop free (Mac/Windows) with your own LLM key — no Pro needed."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const onFile = async (list: FileList | null) => {
    if (!list?.length) return;
    try {
      const parsed = await Promise.all(Array.from(list).slice(0, 3).map(readFileAsText));
      setFiles(parsed);
    } catch {
      setError("Could not read file as text");
    }
  };

  return (
    <div className="ask-page">
      <div className="ask-shell">
        <header className="ask-header">
          <p className="pill-label">Ask NARNA</p>
          <h1>{BRAND.name}</h1>
          <p>
            An AI agent that scores its own decisions. Bring your own LLM key — NARNA adds ADQA,
            Decision Traces, and outcome learning.
          </p>
          <div className="ask-header-actions">
            <label className="ask-mode-label">
              Mode
              <select value={askMode} onChange={(e) => setAskMode(e.target.value)}>
                <option value="cheap">Cheap · 1 model</option>
                <option value="quality">Quality · 2-model merge</option>
                <option value="critical">Critical · 3 + critic</option>
              </select>
            </label>
            {installHint && (
              <button type="button" className="btn btn-secondary ask-install" onClick={onInstall}>
                Install on phone
              </button>
            )}
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowLlm((v) => !v)}
            >
              {llmApiKey ? "LLM key ✓" : "Add LLM key"}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowSkills((v) => !v)}
            >
              Skills ({skills.length})
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setSessionId(undefined);
                setItems([]);
              }}
            >
              /new
            </button>
          </div>
          {!llmApiKey && (
            <div className="ask-byok-banner" role="status">
              <strong>Bring your own LLM key</strong> — without a key, answers run in{" "}
              <em>mock mode</em> (ADQA still scores). Paste OpenRouter / OpenAI / Ollama below.
              <button type="button" className="btn btn-secondary ask-byok-btn" onClick={() => setShowLlm(true)}>
                Add key
              </button>
              <Link to="/download" className="ask-byok-link">
                Or use Desktop →
              </Link>
            </div>
          )}
          {showLlm && (
            <div className="ask-llm-box">
              <p className="ask-mobile-tip">
                Hermes-style BYOK — key stays in your browser localStorage, sent only with Ask
                requests (not stored on NARNA Free unless you save via Models settings).
              </p>
              <label>
                Provider
                <select value={llmProvider} onChange={(e) => setLlmProvider(e.target.value)}>
                  <option value="openrouter">OpenRouter</option>
                  <option value="openai">OpenAI</option>
                  <option value="ollama">Ollama</option>
                </select>
              </label>
              <label>
                API key
                <input
                  type="password"
                  value={llmApiKey}
                  onChange={(e) => setLlmApiKey(e.target.value)}
                  placeholder="sk-or-… / sk-…"
                  className="mono"
                />
              </label>
              <label>
                Model (optional)
                <input
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                  placeholder="openai/gpt-4o-mini"
                  className="mono"
                />
              </label>
            </div>
          )}
          {showSkills && (
            <ul className="ask-skills-list">
              {skills.length === 0 && <li>No saved skills yet — strong answers auto-save.</li>}
              {skills.slice(0, 12).map((s) => (
                <li key={s.skillId}>{s.name}</li>
              ))}
            </ul>
          )}
        </header>

        <div className="ask-thread">
          {items.length === 0 && (
            <div className="ask-empty">
              <p>Try: “Should I sign this contract?” — or `/help` `/new` `/model` `/cron`.</p>
              <p className="ask-mobile-tip">
                Without an LLM key, Ask runs in mock mode (still ADQA-scored). Add your key above.
              </p>
            </div>
          )}
          {items.map((item, idx) => (
            <div key={idx} className={`ask-bubble ask-${item.role}`}>
              <div className="ask-bubble-body">{item.text}</div>
              {item.meta && (
                <div className="ask-meta">
                  {item.meta.mockMode && (
                    <span className="ask-mock-badge">
                      Mock answer — add your LLM key for live models
                    </span>
                  )}
                  <span className="ask-dqs">
                    Verified by ADQA · DQS {item.meta.dqs ?? "—"} · {item.meta.guardian}
                    {item.meta.verdict ? ` · ${item.meta.verdict}` : ""}
                  </span>
                  {item.meta.traceId && (
                    <span className="ask-tools mono">Trace: {item.meta.traceId}</span>
                  )}
                  {!!item.meta.toolsUsed?.length && (
                    <span className="ask-tools">
                      Tools:{" "}
                      {[...new Set(item.meta.toolsUsed.map((t) => t.tool))].join(", ")}
                    </span>
                  )}
                  {item.meta.toolsUsed
                    ?.filter((t) => t.result && (t.result as { needsApproval?: boolean }).needsApproval)
                    .map((t, ti) => {
                      const cmd = String(
                        (t.result as { command?: string }).command ||
                          (t.args as { command?: string } | undefined)?.command ||
                          ""
                      );
                      return (
                        <button
                          key={`approve-${ti}`}
                          type="button"
                          className="btn btn-secondary"
                          onClick={() => {
                            setInput(
                              `Approve shell and re-run: tell NARNA to call shell_exec with approved=true for: ${cmd}`
                            );
                          }}
                        >
                          Approve shell: {cmd.slice(0, 48) || "command"}
                        </button>
                      );
                    })}
                  {item.meta.skillSaved?.name && (
                    <span className="ask-skill">Saved skill: {item.meta.skillSaved.name}</span>
                  )}
                  {showModels && item.meta.modelsUsed?.length > 0 && (
                    <span className="ask-models mono">{item.meta.modelsUsed.join(" · ")}</span>
                  )}
                  <div className="ask-feedback">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={!!item.feedback}
                      onClick={() => onFeedback(idx, "success")}
                    >
                      {item.feedback === "up" ? "Helpful ✓" : "Helpful"}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={!!item.feedback}
                      onClick={() => onFeedback(idx, "fail")}
                    >
                      {item.feedback === "down" ? "Not helpful ✓" : "Not helpful"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
          {loading && <div className="ask-bubble ask-assistant ask-pending">Thinking…</div>}
          <div ref={bottomRef} />
        </div>

        {error && (
          <div className="error ask-error">
            {error}{" "}
            {(error.includes("quota") || error.includes("402") || error.includes("fair-use")) && (
              <Link to="/download">Download Desktop free →</Link>
            )}
          </div>
        )}

        <div className="ask-composer">
          {files.length > 0 && (
            <p className="ask-files">Attached: {files.map((f) => f.name).join(", ")}</p>
          )}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask NARNA anything…"
            rows={3}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
          />
          <div className="ask-actions">
            <label className="btn btn-secondary ask-attach">
              Attach text
              <input
                type="file"
                accept=".txt,.md,.csv,.json,.yaml,.yml"
                hidden
                multiple
                onChange={(e) => onFile(e.target.files)}
              />
            </label>
            <label className="ask-toggle">
              <input
                type="checkbox"
                checked={showModels}
                onChange={(e) => setShowModels(e.target.checked)}
              />
              Show models
            </label>
            <Link to="/settings/models" className="btn btn-secondary ask-byo">
              BYO LLM
            </Link>
            <button type="button" className="btn btn-primary" onClick={onSend} disabled={loading}>
              {loading ? "…" : "Ask"}
            </button>
          </div>
          {quota.hard != null && (
            <p className="ask-quota">
              Hosted turns this period: {quota.used ?? 0} / {quota.hard} ·{" "}
              <Link to="/download">Desktop = unlimited free</Link>
            </p>
          )}
          {quota.hard == null && quota.used != null && (
            <p className="ask-quota">
              Hosted turns this period: {quota.used} · free launch ·{" "}
              <Link to="/download">Desktop recommended</Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
