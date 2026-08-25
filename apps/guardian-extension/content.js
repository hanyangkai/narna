(function () {
  const PROVIDER_MAP = [
    { host: "chatgpt.com", id: "chatgpt" },
    { host: "chat.openai.com", id: "chatgpt" },
    { host: "claude.ai", id: "claude" },
    { host: "gemini.google.com", id: "gemini" },
    { host: "chat.deepseek.com", id: "deepseek" },
    { host: "copilot.microsoft.com", id: "copilot" },
  ];

  function detectProvider() {
    const h = location.hostname;
    for (const p of PROVIDER_MAP) {
      if (h.includes(p.host)) return p.id;
    }
    return "unknown";
  }

  function ensureBadge() {
    if (document.getElementById("narna-guardian-badge")) return;
    const el = document.createElement("div");
    el.id = "narna-guardian-badge";
    el.className = "narna-badge narna-band-trusted";
    el.textContent = "NARNA Protected";
    document.documentElement.appendChild(el);
  }

  function setBadge(band, passportStatus) {
    ensureBadge();
    const el = document.getElementById("narna-guardian-badge");
    el.className = `narna-badge narna-band-${band || "trusted"}`;
    const label =
      passportStatus === "blocked"
        ? "Dangerous"
        : passportStatus === "unverified"
          ? "Caution"
          : "Protected";
    el.textContent = `NARNA · ${label}`;
  }

  function showBanner(result) {
    let ban = document.getElementById("narna-guardian-banner");
    if (!ban) {
      ban = document.createElement("div");
      ban.id = "narna-guardian-banner";
      document.documentElement.appendChild(ban);
    }
    ban.className = `narna-banner narna-band-${result.band || "caution"}`;
    const reasons = (result.reasons || []).slice(0, 2).join("; ");
    ban.innerHTML = "";
    const text = document.createElement("span");
    text.textContent = `NARNA ${String(result.decision || "").toUpperCase()}: ${reasons || "policy"}`;
    ban.appendChild(text);
    if (result.decision === "ask" && result.capability) {
      const btn = document.createElement("button");
      btn.textContent = "Approve once";
      btn.onclick = async () => {
        const apr = await chrome.runtime.sendMessage({
          type: "REQUEST_APPROVAL",
          capability: result.capability,
        });
        if (apr?.approvalToken) {
          ban.dataset.approvalToken = apr.approvalToken;
          ban.dataset.capability = result.capability;
          text.textContent = "Approved — send again";
          btn.remove();
        }
      };
      ban.appendChild(btn);
    }
  }

  function readComposerText() {
    const candidates = [
      document.querySelector("[contenteditable='true']"),
      document.querySelector("textarea"),
      document.querySelector("div[role='textbox']"),
    ].filter(Boolean);
    for (const el of candidates) {
      const t = (el.innerText || el.value || "").trim();
      if (t) return t;
    }
    return "";
  }

  async function gateSend(event) {
    const settings = await chrome.runtime.sendMessage({ type: "GET_SETTINGS" });
    if (!settings?.protectedMode) return;

    const text = readComposerText();
    if (!text) return;

    const ban = document.getElementById("narna-guardian-banner");
    const approvalToken = ban?.dataset?.approvalToken || null;

    const result = await chrome.runtime.sendMessage({
      type: "GATEWAY_CHECK",
      payload: {
        provider: detectProvider(),
        url: location.href,
        action: "message.send",
        text,
        approvalToken,
      },
    });

    if (!result || result.skipped) return;
    setBadge(result.band, result.passportStatus);

    if (result.decision === "allow") {
      if (ban) ban.remove();
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    showBanner(result);
  }

  function attach() {
    ensureBadge();
    chrome.runtime.sendMessage({ type: "GET_SETTINGS" }).then((s) => {
      if (s?.protectedMode === false) {
        const el = document.getElementById("narna-guardian-badge");
        if (el) el.textContent = "NARNA Off";
      }
    });

    document.addEventListener(
      "keydown",
      (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          gateSend(e);
        }
      },
      true
    );

    document.addEventListener(
      "click",
      (e) => {
        const t = e.target;
        if (!(t instanceof Element)) return;
        const btn = t.closest("button");
        if (!btn) return;
        const label = (btn.getAttribute("aria-label") || btn.textContent || "").toLowerCase();
        if (label.includes("send") || label.includes("submit")) {
          gateSend(e);
        }
      },
      true
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach);
  } else {
    attach();
  }
})();
