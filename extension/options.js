const ids = ["chrome", "edge", "brave", "syncBookmarks", "syncHistory", "historyDays"];

async function load() {
  const data = await browser.runtime.sendMessage({ type: "get-status" });
  document.getElementById("chrome").checked = !!data.sources.chrome;
  document.getElementById("edge").checked = !!data.sources.edge;
  document.getElementById("brave").checked = !!data.sources.brave;
  document.getElementById("syncBookmarks").checked = !!data.syncBookmarks;
  document.getElementById("syncHistory").checked = !!data.syncHistory;
  document.getElementById("historyDays").value = String(data.historyDays || 30);
}

document.getElementById("save").addEventListener("click", async () => {
  const settings = {
    sources: {
      chrome: document.getElementById("chrome").checked,
      edge: document.getElementById("edge").checked,
      brave: document.getElementById("brave").checked
    },
    syncBookmarks: document.getElementById("syncBookmarks").checked,
    syncHistory: document.getElementById("syncHistory").checked,
    historyDays: Number(document.getElementById("historyDays").value)
  };

  await browser.storage.local.set(settings);
  const saved = document.getElementById("saved");
  saved.textContent = "Salvo.";
  setTimeout(() => saved.textContent = "", 1800);
});

document.getElementById("detect").addEventListener("click", async () => {
  const output = document.getElementById("detect-result");
  output.textContent = "Detectando…";

  try {
    const result = await browser.runtime.sendMessage({ type: "detect" });
    if (result?.ok) {
      output.textContent = result.detected?.length
        ? `Detectados: ${result.detected.join(", ")}`
        : "Bridge funcionando, mas nenhum navegador compatível foi localizado.";
    } else {
      output.textContent = `Erro: ${result?.error || "resposta inválida"}`;
    }
  } catch (error) {
    output.textContent = `Não foi possível conectar ao bridge: ${error.message}`;
  }
});

load();
