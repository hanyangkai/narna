async function refresh() {
  const s = await chrome.runtime.sendMessage({ type: "GET_SETTINGS" });
  document.getElementById("protected").checked = !!s.protectedMode;
  document.getElementById("meta").textContent = s.deviceId
    ? `Device ${s.deviceId.slice(0, 16)}… · CTI ${((s.ctiFeed || []).length)} · API ${s.apiBase}`
    : "Not registered yet";
  document.getElementById("last").textContent = JSON.stringify(
    (s.lastDecisions || []).slice(0, 3),
    null,
    2
  );
}

document.getElementById("protected").addEventListener("change", async (e) => {
  await chrome.runtime.sendMessage({ type: "SET_PROTECTED", value: e.target.checked });
  await refresh();
});

document.getElementById("sync").addEventListener("click", async () => {
  await chrome.runtime.sendMessage({ type: "SYNC_NOW" });
  await refresh();
});

refresh();
