import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  DEFAULT_DEV_KEY,
  fetchAgentModels,
  saveAgentModels,
  type AgentModelsConfig,
} from "../api";

export default function ModelsSettings() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("uap_api_key") || DEFAULT_DEV_KEY);
  const [cfg, setCfg] = useState<AgentModelsConfig | null>(null);
  const [provider, setProvider] = useState("openrouter");
  const [llmKey, setLlmKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [modelReason, setModelReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    localStorage.setItem("uap_api_key", apiKey);
    try {
      const out = await fetchAgentModels(apiKey);
      setCfg(out);
      setProvider(out.provider || "openrouter");
      setBaseUrl(out.baseUrl || "");
      setModelReason(out.modelReason || "");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setCfg(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onSave = async () => {
    setMsg(null);
    setError(null);
    try {
      await saveAgentModels(apiKey, {
        provider,
        apiKey: llmKey || undefined,
        baseUrl: baseUrl || undefined,
        modelReason: modelReason || undefined,
      });
      setMsg("Saved BYO LLM settings.");
      setLlmKey("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="layout-wide">
      <header className="page-header">
        <p className="pill-label">Models</p>
        <h1>Bring Your Own LLM</h1>
        <p>
          Hermes-style BYOK: paste OpenRouter, OpenAI, or Ollama credentials. NARNA does not host
          an LLM for you — it routes, tools, scores (ADQA), and remembers.
        </p>
      </header>

      <div className="console-bar">
        <label>
          API Key
          <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} className="mono" />
        </label>
        <button type="button" className="btn btn-secondary" onClick={load} disabled={loading}>
          Refresh
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {msg && <div className="card">{msg}</div>}

      {cfg && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <p>
            <strong>Plan:</strong> {cfg.plan === "cloud" ? "Personal" : cfg.plan} · BYO{" "}
            {cfg.byoLlmAllowed ? "allowed" : "locked"}
          </p>
          <p>
            <strong>Current key:</strong>{" "}
            {cfg.apiKeySet ? cfg.apiKeyPreview : "not set (uses server default)"}
          </p>
          {!cfg.byoLlmAllowed && (
            <p>
              Prefer free Desktop (Mac/Windows) with local keys — no Pro.{" "}
              <Link to="/download">Download →</Link>
            </p>
          )}
        </div>
      )}

      <div className="card">
        <label>
          Provider
          <select value={provider} onChange={(e) => setProvider(e.target.value)}>
            <option value="openrouter">OpenRouter</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
            <option value="mock">Mock (dev)</option>
          </select>
        </label>
        <label style={{ display: "block", marginTop: "0.75rem" }}>
          API key
          <input
            type="password"
            value={llmKey}
            onChange={(e) => setLlmKey(e.target.value)}
            placeholder="Leave blank to keep existing"
            className="mono"
            style={{ width: "100%" }}
          />
        </label>
        <label style={{ display: "block", marginTop: "0.75rem" }}>
          Base URL (optional)
          <input
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://api.openai.com/v1 or http://127.0.0.1:11434/v1"
            className="mono"
            style={{ width: "100%" }}
          />
        </label>
        <label style={{ display: "block", marginTop: "0.75rem" }}>
          Reason model id
          <input
            value={modelReason}
            onChange={(e) => setModelReason(e.target.value)}
            placeholder="openai/gpt-4o-mini"
            className="mono"
            style={{ width: "100%" }}
          />
        </label>
        <button
          type="button"
          className="btn btn-primary"
          style={{ marginTop: "1rem" }}
          onClick={onSave}
          disabled={!cfg?.byoLlmAllowed}
        >
          Save
        </button>
        <p style={{ marginTop: "1rem" }}>
          <Link to="/ask">← Back to Ask NARNA</Link>
        </p>
      </div>
    </div>
  );
}
