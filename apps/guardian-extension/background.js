const DEFAULTS = {
  apiBase: "https://api.narna.org",
  protectedMode: true,
  apiKey: "",
  deviceId: "",
  profile: "citizen",
  lastDecisions: [],
  ctiFeed: [],
  ctiSince: null,
  emergencies: [],
};

async function getSettings() {
  const data = await chrome.storage.sync.get(DEFAULTS);
  return { ...DEFAULTS, ...data };
}

async function setSettings(patch) {
  await chrome.storage.sync.set(patch);
}

async function ensureRegistered() {
  const s = await getSettings();
  if (s.apiKey && s.deviceId) return s;
  const res = await fetch(`${s.apiBase}/v1/citizen/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label: "Guardian Extension", profile: s.profile || "citizen" }),
  });
  if (!res.ok) throw new Error(`register failed: ${res.status}`);
  const body = await res.json();
  await setSettings({ apiKey: body.apiKey, deviceId: body.deviceId, profile: body.profile });
  return getSettings();
}

async function gatewayCheck(payload) {
  const s = await ensureRegistered();
  const res = await fetch(`${s.apiBase}/v1/gateway/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...payload,
      apiKey: s.apiKey,
      deviceId: s.deviceId,
      profile: s.profile,
    }),
  });
  if (!res.ok) throw new Error(`gateway check failed: ${res.status}`);
  const result = await res.json();
  const hist = [result, ...(s.lastDecisions || [])].slice(0, 20);
  await setSettings({ lastDecisions: hist });
  return result;
}

async function syncCti() {
  const s = await getSettings();
  const q = new URLSearchParams({ limit: "50" });
  if (s.ctiSince) q.set("since", s.ctiSince);
  const res = await fetch(`${s.apiBase}/v1/cti/citizen/feed?${q}`);
  if (!res.ok) return;
  const body = await res.json();
  const feed = body.feed || [];
  if (!feed.length) return;
  const merged = [...feed, ...(s.ctiFeed || [])].slice(0, 200);
  const latest = feed[0]?.receivedAt || s.ctiSince;
  await setSettings({ ctiFeed: merged, ctiSince: latest });
}

async function syncEmergency() {
  const s = await getSettings();
  const res = await fetch(`${s.apiBase}/v1/guardian/emergency/feed?limit=10`);
  if (!res.ok) return;
  const body = await res.json();
  const broadcasts = body.broadcasts || [];
  const prevIds = new Set((s.emergencies || []).map((e) => e.broadcastId));
  for (const b of broadcasts) {
    if (!prevIds.has(b.broadcastId)) {
      chrome.notifications.create(b.broadcastId, {
        type: "basic",
        iconUrl: "icons/icon48.png",
        title: "NARNA Emergency",
        message: b.message || "Update threat signatures",
      });
      if (b.action === "refresh_cti") await syncCti();
    }
  }
  await setSettings({ emergencies: broadcasts.slice(-20) });
}

chrome.runtime.onInstalled.addListener(async () => {
  await ensureRegistered().catch(() => {});
  chrome.alarms.create("narna-sync", { periodInMinutes: 1 });
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "narna-sync") return;
  await syncCti().catch(() => {});
  await syncEmergency().catch(() => {});
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    if (msg.type === "GET_SETTINGS") {
      sendResponse(await getSettings());
      return;
    }
    if (msg.type === "SET_PROTECTED") {
      await setSettings({ protectedMode: !!msg.value });
      sendResponse(await getSettings());
      return;
    }
    if (msg.type === "GATEWAY_CHECK") {
      const s = await getSettings();
      if (!s.protectedMode) {
        sendResponse({ decision: "allow", band: "trusted", skipped: true });
        return;
      }
      // Local CTI match before network
      const text = (msg.payload?.text || "").toLowerCase();
      for (const sig of s.ctiFeed || []) {
        for (const p of sig.patterns || []) {
          if (p && text.includes(String(p).toLowerCase())) {
            const blocked = {
              decision: "deny",
              band: "dangerous",
              passportStatus: "blocked",
              reasons: [`local cti: ${p}`],
              approvalRequired: false,
              capability: "content",
            };
            sendResponse(blocked);
            return;
          }
        }
      }
      sendResponse(await gatewayCheck(msg.payload || {}));
      return;
    }
    if (msg.type === "REQUEST_APPROVAL") {
      const s = await ensureRegistered();
      const res = await fetch(`${s.apiBase}/v1/citizen/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deviceId: s.deviceId,
          capability: msg.capability,
        }),
      });
      sendResponse(await res.json());
      return;
    }
    if (msg.type === "SYNC_NOW") {
      await syncCti();
      await syncEmergency();
      sendResponse({ ok: true });
      return;
    }
    sendResponse({ ok: false });
  })().catch((e) => sendResponse({ ok: false, error: String(e) }));
  return true;
});
