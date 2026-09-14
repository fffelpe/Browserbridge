const syncButton = document.getElementById("sync-button");
const optionsButton = document.getElementById("options-button");
const statusDot = document.getElementById("status-dot");
const statusTitle = document.getElementById("status-title");
const statusText = document.getElementById("status-text");
const bookmarkCount = document.getElementById("bookmark-count");
const historyCount = document.getElementById("history-count");
const lastSync = document.getElementById("last-sync");

function setState(kind, title, text) {
  statusDot.className = `dot ${kind}`;
  statusTitle.textContent = title;
  statusText.textContent = text;
}

function formatDate(timestamp) {
  if (!timestamp) return "Nunca sincronizado";
  return `Última sincronização: ${new Date(timestamp).toLocaleString("pt-BR")}`;
}

function render(result, lastSyncAt) {
  lastSync.textContent = formatDate(lastSyncAt);

  if (!result) {
    setState("idle", "Pronto", "Clique em sincronizar para testar o bridge.");
    return;
  }

  bookmarkCount.textContent = result.bookmarks?.imported ?? 0;
  historyCount.textContent = result.history?.imported ?? 0;

  if (result.ok) {
    const detected = (result.detected || []).join(", ") || "nenhum";
    const warning = result.warnings?.length
      ? ` Avisos: ${result.warnings.length}.`
      : "";
    setState("ok", "Sincronizado", `Navegadores detectados: ${detected}.${warning}`);
  } else {
    setState("error", "Falha na sincronização", result.error || "Erro desconhecido.");
  }
}

async function load() {
  const data = await browser.runtime.sendMessage({ type: "get-status" });
  render(data.lastResult, data.lastSync);
}

syncButton.addEventListener("click", async () => {
  syncButton.disabled = true;
  syncButton.textContent = "Sincronizando…";
  setState("busy", "Sincronizando", "Lendo os navegadores selecionados.");

  const result = await browser.runtime.sendMessage({ type: "sync-now" });
  const data = await browser.runtime.sendMessage({ type: "get-status" });
  render(result, data.lastSync);

  syncButton.disabled = false;
  syncButton.textContent = "Sincronizar agora";
});

optionsButton.addEventListener("click", () => {
  browser.runtime.openOptionsPage();
});

load();
