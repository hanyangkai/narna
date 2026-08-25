async function load() {
  const s = await chrome.storage.sync.get({
    apiBase: "https://api.narna.org",
    profile: "citizen",
    apiKey: "",
  });
  document.getElementById("apiBase").value = s.apiBase;
  document.getElementById("profile").value = s.profile;
  document.getElementById("apiKey").value = s.apiKey;
}

document.getElementById("save").onclick = async () => {
  await chrome.storage.sync.set({
    apiBase: document.getElementById("apiBase").value.replace(/\/$/, ""),
    profile: document.getElementById("profile").value,
  });
  document.getElementById("status").textContent = "Saved.";
};

document.getElementById("rereg").onclick = async () => {
  await chrome.storage.sync.set({ apiKey: "", deviceId: "" });
  const s = await chrome.storage.sync.get({ apiBase: "https://api.narna.org", profile: "citizen" });
  const res = await fetch(`${s.apiBase}/v1/citizen/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label: "Guardian Extension", profile: s.profile }),
  });
  const body = await res.json();
  await chrome.storage.sync.set({
    apiKey: body.apiKey,
    deviceId: body.deviceId,
  });
  document.getElementById("apiKey").value = body.apiKey;
  document.getElementById("status").textContent = "Registered.";
};

load();
