const HOST_NAME = "site.felipeleal.browserbridge";

const DEFAULT_SETTINGS = {
  sources: {
    chrome: true,
    edge: true,
    brave: false
  },
  syncBookmarks: true,
  syncHistory: true,
  historyDays: 30,
  lastSync: 0,
  lastResult: null
};

async function getSettings() {
  const stored = await browser.storage.local.get(DEFAULT_SETTINGS);
  return {
    ...DEFAULT_SETTINGS,
    ...stored,
    sources: {
      ...DEFAULT_SETTINGS.sources,
      ...(stored.sources || {})
    }
  };
}

async function setLastResult(result) {
  await browser.storage.local.set({
    lastResult: result,
    lastSync: result.ok ? Date.now() : (await getSettings()).lastSync
  });
}

async function findWritableBookmarkRoot() {
  const tree = await browser.bookmarks.getTree();
  const root = tree[0];
  if (!root?.children?.length) {
    throw new Error("Nenhuma raiz gravável de favoritos foi encontrada.");
  }

  // A raiz absoluta do Firefox não pode receber itens diretamente.
  // Seus filhos (Barra/Menu/Outros favoritos) podem.
  const candidate = root.children.find(node => !node.url);
  if (!candidate) {
    throw new Error("Nenhuma pasta raiz de favoritos foi encontrada.");
  }
  return candidate.id;
}

async function findChildFolder(parentId, title) {
  const children = await browser.bookmarks.getChildren(parentId);
  return children.find(item => !item.url && item.title === title) || null;
}

async function ensureFolder(parentId, title) {
  const existing = await findChildFolder(parentId, title);
  if (existing) return existing.id;

  const created = await browser.bookmarks.create({
    parentId,
    title
  });
  return created.id;
}

async function collectBookmarkUrls() {
  const tree = await browser.bookmarks.getTree();
  const urls = new Set();

  function walk(nodes) {
    for (const node of nodes || []) {
      if (node.url) urls.add(node.url);
      if (node.children) walk(node.children);
    }
  }

  walk(tree);
  return urls;
}

async function importBookmarks(items) {
  if (!items?.length) return { imported: 0, skipped: 0 };

  const writableRootId = await findWritableBookmarkRoot();
  const browserBridgeRootId = await ensureFolder(writableRootId, "BrowserBridge");
  const knownUrls = await collectBookmarkUrls();

  let imported = 0;
  let skipped = 0;

  // Cache das pastas já localizadas/criadas nesta sincronização.
  const folderCache = new Map();

  for (const item of items) {
    if (!item.url || knownUrls.has(item.url)) {
      skipped++;
      continue;
    }

    const sourceTitle = item.sourceLabel || item.source || "Importado";
    let parentId = await ensureFolder(browserBridgeRootId, sourceTitle);

    const path = Array.isArray(item.folderPath) ? item.folderPath : [];
    let cacheKey = `${sourceTitle}`;

    for (const segment of path) {
      if (!segment) continue;
      cacheKey += `/${segment}`;

      if (folderCache.has(cacheKey)) {
        parentId = folderCache.get(cacheKey);
      } else {
        parentId = await ensureFolder(parentId, segment);
        folderCache.set(cacheKey, parentId);
      }
    }

    await browser.bookmarks.create({
      parentId,
      title: item.title || item.url,
      url: item.url
    });

    knownUrls.add(item.url);
    imported++;
  }

  return { imported, skipped };
}

function roundedVisitTime(value) {
  return Math.round(Number(value || 0) / 1000);
}

async function importHistory(visits) {
  if (!visits?.length) return { imported: 0, skipped: 0 };

  const byUrl = new Map();
  for (const visit of visits) {
    if (!visit.url || !visit.visitTime) continue;
    if (!byUrl.has(visit.url)) byUrl.set(visit.url, []);
    byUrl.get(visit.url).push(visit);
  }

  let imported = 0;
  let skipped = 0;

  for (const [url, sourceVisits] of byUrl) {
    let existing = [];
    try {
      existing = await browser.history.getVisits({ url });
    } catch (_) {
      existing = [];
    }

    const existingSeconds = new Set(
      existing.map(v => roundedVisitTime(v.visitTime))
    );

    for (const visit of sourceVisits) {
      const secondKey = roundedVisitTime(visit.visitTime);
      if (existingSeconds.has(secondKey)) {
        skipped++;
        continue;
      }

      try {
        await browser.history.addUrl({
          url,
          title: visit.title || undefined,
          visitTime: Number(visit.visitTime)
        });
        existingSeconds.add(secondKey);
        imported++;
      } catch (error) {
        console.warn("Não foi possível importar visita:", url, error);
        skipped++;
      }
    }
  }

  return { imported, skipped };
}

async function runSync(trigger = "manual") {
  const settings = await getSettings();
  const selectedSources = Object.entries(settings.sources)
    .filter(([, enabled]) => enabled)
    .map(([source]) => source);

  if (!selectedSources.length) {
    const result = {
      ok: false,
      trigger,
      error: "Nenhum navegador de origem está selecionado.",
      at: Date.now()
    };
    await setLastResult(result);
    return result;
  }

  // Na primeira sincronização importamos somente a janela configurada.
  // Nas seguintes, pedimos desde a última sincronização com uma pequena
  // sobreposição; a deduplicação evita repetir visitas.
  const configuredSince = Date.now() - settings.historyDays * 24 * 60 * 60 * 1000;
  const incrementalSince = settings.lastSync
    ? Math.max(configuredSince, settings.lastSync - 2 * 60 * 1000)
    : configuredSince;

  try {
    const payload = await browser.runtime.sendNativeMessage(HOST_NAME, {
      action: "sync",
      sources: selectedSources,
      includeBookmarks: settings.syncBookmarks,
      includeHistory: settings.syncHistory,
      historySince: incrementalSince
    });

    if (!payload?.ok) {
      throw new Error(payload?.error || "O host nativo não respondeu corretamente.");
    }

    const bookmarkResult = settings.syncBookmarks
      ? await importBookmarks(payload.bookmarks || [])
      : { imported: 0, skipped: 0 };

    const historyResult = settings.syncHistory
      ? await importHistory(payload.history || [])
      : { imported: 0, skipped: 0 };

    const result = {
      ok: true,
      trigger,
      at: Date.now(),
      detected: payload.detected || [],
      bookmarks: bookmarkResult,
      history: historyResult,
      warnings: payload.warnings || []
    };

    await setLastResult(result);
    return result;
  } catch (error) {
    const result = {
      ok: false,
      trigger,
      at: Date.now(),
      error: error?.message || String(error)
    };
    await setLastResult(result);
    return result;
  }
}

browser.runtime.onInstalled.addListener(async () => {
  const current = await browser.storage.local.get();
  if (!current.sources) {
    await browser.storage.local.set(DEFAULT_SETTINGS);
  }
});

browser.runtime.onStartup.addListener(() => {
  runSync("startup");
});

browser.runtime.onMessage.addListener((message) => {
  if (message?.type === "sync-now") {
    return runSync("manual");
  }

  if (message?.type === "get-status") {
    return getSettings();
  }

  if (message?.type === "detect") {
    return browser.runtime.sendNativeMessage(HOST_NAME, {
      action: "detect"
    });
  }

  return false;
});
