const MODE = "framework_stream";
const PREFS_KEY = "mzd_context_engine_prefs";
const DEFAULT_PREFS = {
  fontSize: 19,
  lineHeight: 1.92,
  autoGenerate: true,
  showEvents: false,
};

const state = {
  articles: [],
  article: null,
  sessionId: null,
  anchorId: null,
  loadingArticle: false,
  uiVersion: 0,
  agentVersion: 0,
  selection: null,
  stream: null,
  workflowStream: null,
  lastWorkflowRequest: null,
  apiReady: false,
  map: {
    instance: null,
    tileLayer: null,
    layers: [],
    variables: [],
    keywordCount: 0,
    aiStatus: "即时变量",
  },
  prewarm: {
    version: 0,
    streams: [],
    running: false,
  },
  prefs: {...DEFAULT_PREFS},
};

const $ = (selector) => document.querySelector(selector);
const reader = $("#reader");
const statusNode = $("#status");
const eventLog = $("#events");
const agentOutput = $("#agent-output");
const agentImage = $("#agent-image");
const agentStatus = $("#agent-status");
const subagentQueue = $("#subagent-queue");
const toolDialog = $("#tool-dialog");
const modalAgent = $("#modal-agent");
const modalContext = $("#modal-context");
const modalTimeline = $("#modal-timeline");
const searchDialog = $("#search-dialog");
const noteDialog = $("#note-dialog");
const mapDialog = $("#map-dialog");

const ICONS = {
  settings: '<path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06A1.65 1.65 0 0 0 15 19.4a1.65 1.65 0 0 0-1 .6 1.65 1.65 0 0 0-.38 1.06V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-.6-1 1.65 1.65 0 0 0-1.06-.38H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-.6 1.65 1.65 0 0 0 .38-1.06V3a2 2 0 0 1 4 0v.09A1.65 1.65 0 0 0 15 4.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.12.37.33.7.6 1 .3.25.67.38 1.06.38H21a2 2 0 0 1 0 4h-.09A1.65 1.65 0 0 0 19.4 15Z"/>',
  close: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  component: '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M16 3h3a2 2 0 0 1 2 2v3"/><path d="M8 21H5a2 2 0 0 1-2-2v-3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/><path d="M9 9h6v6H9z"/>',
  spark: '<path d="M13 2 9 14l-7 3 8 1 4 4 1-8 7-4-8-1-1-7Z"/>',
  timeline: '<path d="M4 5h8"/><path d="M4 12h16"/><path d="M4 19h10"/><circle cx="18" cy="5" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="18" cy="19" r="2"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  image: '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
  map: '<path d="M9 18 3 21V6l6-3 6 3 6-3v15l-6 3-6-3Z"/><path d="M9 3v15"/><path d="M15 6v15"/>',
  route: '<circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/><path d="M8.5 16.5 15.5 7.5"/>',
  event: '<path d="M8 2v4"/><path d="M16 2v4"/><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M3 10h18"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/>',
  agent: '<path d="M12 8V4"/><rect x="4" y="8" width="16" height="12" rx="3"/><path d="M9 13h.01"/><path d="M15 13h.01"/><path d="M9 17h6"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/>',
  note: '<path d="M6 3h9l3 3v15H6z"/><path d="M14 3v4h4"/><path d="M9 12h6"/><path d="M9 16h6"/>',
  font: '<path d="M4 19 10 5h4l6 14"/><path d="M7 13h10"/>',
  book: '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H7a3 3 0 0 0-3 3Z"/><path d="M4 5.5V22"/><path d="M12 3v16"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M5 21a7 7 0 0 1 14 0"/>',
  flag: '<path d="M5 22V4"/><path d="M5 4h12l-2 5 2 5H5"/>',
  network: '<circle cx="6" cy="18" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><path d="M8.5 16.5 15.5 8.5"/><path d="M9 18h6"/>',
  trend: '<path d="M4 18h16"/><path d="M6 15 11 9l4 4 5-8"/><path d="M20 5v5h-5"/>',
  "chevron-left": '<path d="m15 18-6-6 6-6"/>',
  "chevron-right": '<path d="m9 18 6-6-6-6"/>',
  refresh: '<path d="M21 12a9 9 0 0 1-15.3 6.4"/><path d="M3 12A9 9 0 0 1 18.3 5.6"/><path d="M18 2v4h-4"/><path d="M6 22v-4h4"/>',
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((node) => {
    const name = node.dataset.icon;
    if (!name || !ICONS[name]) return;
    node.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">${ICONS[name]}</svg>`;
  });
}

function idempotencyKey() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `web_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function logEvent(type, payload) {
  eventLog.textContent += `${type} ${JSON.stringify(payload, null, 2)}\n\n`;
  eventLog.scrollTop = eventLog.scrollHeight;
}

function setRuntimeLabel(text) {
  $("#runtime-label").textContent = text;
}

function setAgentStatus(text) {
  agentStatus.textContent = text;
}

function setMapStatus(text) {
  state.map.aiStatus = text;
  const node = $("#map-status");
  if (node) node.textContent = text;
}

function renderAnalysisPanel(text) {
  const panel = $("#analysis-content");
  const loading = $("#analysis-loading");
  if (!panel || !loading) return;
  loading.hidden = true;
  panel.hidden = false;
  let html = "";
  const lines = text.split("\n");
  let section = "";
  let collectLines = [];
  const flush = () => {
    if (section && collectLines.length) {
      html += renderAnalysisSection(section, collectLines);
      collectLines = [];
    }
    section = "";
  };
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const m = trimmed.match(/^(标题|摘要|发现|建议点击|地图变量|插图提示)\s*[：:]\s*(.*)$/);
    if (m) {
      flush();
      section = m[1];
      if (m[2]) collectLines.push(m[2]);
      continue;
    }
    if (trimmed.startsWith("- ") || trimmed.startsWith("· ")) {
      collectLines.push(trimmed.slice(2));
      continue;
    }
    collectLines.push(trimmed);
  }
  flush();
  if (!html) html = `<p class="summary">${escapeHtml(text)}</p>`;
  panel.innerHTML = html;
  panel.scrollTop = 0;
}

function renderAnalysisSection(title, lines) {
  const body = lines.join("\n");
  switch (title) {
    case "标题":
      return `<h2>${escapeHtml(body)}</h2>`;
    case "摘要":
      return `<p class="summary">${escapeHtml(body)}</p>`;
    case "发现":
      return renderAnalysisDiscoveries(lines);
    case "建议点击":
      return "";
    case "地图变量":
      return "";
    case "插图提示":
      return "";
    default:
      return `<p class="summary">${escapeHtml(body)}</p>`;
  }
}

function renderAnalysisDiscoveries(lines) {
  let html = '<div class="context-cards">';
  for (const line of lines) {
    const parts = line.split("｜").map((s) => s.trim());
    if (parts.length < 2) {
      html += `<div class="discovery-card"><div class="card-desc">${escapeHtml(line)}</div></div>`;
      continue;
    }
    const kind = parts[0];
    const name = parts[1];
    const desc = parts[2] || "";
    const kindClass = kind.includes("组织") ? "org" : kind.includes("阶级") ? "event" : kind.includes("人物") ? "person" : kind.includes("地点") ? "place" : "event";
    html += `<div class="discovery-card">
      <div class="card-title"><span class="kind-tag ${kindClass}">${escapeHtml(kind)}</span>${escapeHtml(name)}</div>
      <div class="card-desc">${escapeHtml(desc)}</div>
    </div>`;
  }
  html += "</div>";
  return html;
}

function renderContextCardsInline(writingContext, eraContext, coreArgument) {
  const panel = $("#analysis-content");
  if (!panel) return;
  let html = '<div class="context-cards">';
  if (writingContext) html += `<div class="context-card-inline"><h4>写作背景</h4><p>${escapeHtml(writingContext)}</p></div>`;
  if (eraContext) html += `<div class="context-card-inline situation"><h4>时代背景</h4><p>${escapeHtml(eraContext)}</p></div>`;
  if (coreArgument) html += `<div class="context-card-inline argument"><h4>核心论点</h4><p>${escapeHtml(coreArgument)}</p></div>`;
  html += "</div>";
  panel.innerHTML += html;
}

function openToolDialog(title, options = {}) {
  $("#tool-dialog-title").textContent = title;
  toolDialog.classList.toggle("agent-dialog", options.showAgent !== false);
  modalAgent.hidden = options.showAgent === false;
  modalContext.hidden = !options.showContext;
  modalTimeline.hidden = !options.showTimeline;
  if (!toolDialog.open) toolDialog.showModal();
  hydrateIcons(toolDialog);
}

function closeToolDialog() {
  if (toolDialog.open) toolDialog.close();
}

function articleOptionValue(item) {
  return `${item.articleId}__${item.currentReleaseId}`;
}

function resetContextCards(message = "等待生成") {
  document.querySelectorAll(".context-card").forEach((node) => {
    node.classList.remove("loading", "failed");
    const body = node.querySelector(".card-body");
    body.classList.add("empty");
    body.textContent = message;
  });
}

function resetAgent(message = "等待探索") {
  if (state.workflowStream) state.workflowStream.close();
  subagentQueue.innerHTML = "";
  agentImage.hidden = true;
  agentImage.innerHTML = "";
  agentOutput.classList.remove("notice-mode");
  agentOutput.classList.add("empty");
  agentOutput.textContent = message;
  setAgentStatus("idle");
  $("#agent-regenerate").disabled = true;
  state.lastWorkflowRequest = null;
}

function cancelBackgroundWorkflows() {
  state.prewarm.streams.forEach((source) => source.close());
  state.prewarm.streams = [];
  state.prewarm.running = false;
  state.prewarm.version += 1;
}

function loadPrefs() {
  try {
    const parsed = JSON.parse(localStorage.getItem(PREFS_KEY) || "{}");
    const saved = parsed && typeof parsed === "object" ? parsed : {};
    return {
      ...DEFAULT_PREFS,
      ...saved,
      fontSize: Number(saved.fontSize || DEFAULT_PREFS.fontSize),
      lineHeight: Number(saved.lineHeight || DEFAULT_PREFS.lineHeight),
      autoGenerate: saved.autoGenerate ?? DEFAULT_PREFS.autoGenerate,
      showEvents: saved.showEvents ?? DEFAULT_PREFS.showEvents,
    };
  } catch {
    return {...DEFAULT_PREFS};
  }
}

function savePrefs() {
  localStorage.setItem(PREFS_KEY, JSON.stringify(state.prefs));
}

function applyPrefs() {
  document.documentElement.style.setProperty("--reader-font-size", `${state.prefs.fontSize}px`);
  document.documentElement.style.setProperty("--reader-line-height", String(state.prefs.lineHeight));
  $("#debug-panel").hidden = !state.prefs.showEvents;
  $("#pref-font-size").value = String(state.prefs.fontSize);
  $("#pref-line-height").value = String(state.prefs.lineHeight);
  $("#pref-auto-generate").checked = Boolean(state.prefs.autoGenerate);
  $("#pref-show-events").checked = Boolean(state.prefs.showEvents);
  if (state.prefs.theme) {
    applyTheme(state.prefs.theme);
    const active = document.querySelector(`.swatch[data-theme="${state.prefs.theme}"]`);
    if (active) {
      document.querySelectorAll(".swatch").forEach((s) => s.classList.remove("active"));
      active.classList.add("active");
    }
  }
}

function cardForSlot(slot) {
  return document.querySelector(`[data-slot="${slot}"]`);
}

function renderCard(card) {
  const target = cardForSlot(card.slot);
  if (!target) return;
  target.classList.remove("loading", "failed");
  const points = (card.points || [])
    .map((point) => `<li>${point.label ? `<strong>${escapeHtml(point.label)}：</strong>` : ""}${escapeHtml(point.text)}</li>`)
    .join("");
  target.querySelector(".card-body").classList.remove("empty");
  target.querySelector(".card-body").innerHTML = `
    <h3>${escapeHtml(card.headline)}</h3>
    <p>${escapeHtml(card.summary)}</p>
    ${points ? `<ul>${points}</ul>` : ""}
    <div class="sources">sourceIds：${escapeHtml((card.sourceIds || []).join("、"))}</div>
  `;
}

function renderPartial(slot, text) {
  const target = cardForSlot(slot);
  if (!target) return;
  target.classList.add("loading");
  const body = target.querySelector(".card-body");
  body.classList.remove("empty");
  body.innerHTML = `<pre class="streaming-text">${escapeHtml(text)}</pre>`;
}

function markFailed(message) {
  document.querySelectorAll(".context-card.loading").forEach((node) => node.classList.remove("loading"));
  statusNode.textContent = message;
  setRuntimeLabel("failed");
}

function articleMeta(article) {
  return [article.dateDisplay, article.location, article.documentType]
    .filter(Boolean)
    .join(" · ");
}

function anchorSourceIds(anchorId) {
  const anchor = state.article?.anchors?.find((item) => item.anchorId === anchorId);
  return anchor?.paragraphIds || [];
}

function articleSourceIds(limit = 20) {
  return (state.article?.paragraphs || []).slice(0, limit).map((item) => item.paragraphId);
}

function articleOverviewTarget() {
  return {
    targetType: "article",
    targetId: state.article.articleId,
    label: "全篇总览",
    sourceIds: articleSourceIds(12),
  };
}

function mapContextTarget() {
  return {
    targetType: "article",
    targetId: state.article.articleId,
    label: "AI 地图语境",
    sourceIds: articleSourceIds(20),
  };
}

function summarizeApiSettings(settings) {
  const keyText = settings.hasApiKey ? `密钥：${settings.apiKeySource === "environment" ? "环境变量" : "已保存"}` : "密钥：未配置";
  const modelText = settings.model ? `模型：${settings.model}` : "模型：未配置";
  const imageText = settings.imageModel ? `图片：${settings.imageModel}` : "图片：未配置";
  return `${modelText} · ${imageText} · ${keyText}`;
}

async function loadApiSettings() {
  const settings = await fetch("/api/v1/settings/llm").then((response) => response.json());
  $("#api-base-url").value = settings.baseUrl || "";
  $("#api-model").value = settings.model || "";
  $("#api-key").value = "";
  $("#api-clear-key").checked = false;
  $("#api-temperature").value = String(settings.temperature ?? 0.2);
  $("#api-image-base-url").value = settings.imageBaseUrl || "";
  $("#api-image-model").value = settings.imageModel || "";
  $("#api-image-size").value = settings.imageSize || "1024x1024";
  $("#api-image-quality").value = settings.imageQuality || "low";
  $("#api-image-format").value = settings.imageOutputFormat || "png";
  $("#api-status").textContent = summarizeApiSettings(settings);
  state.apiReady = Boolean(settings.hasApiKey && settings.model);
  if (!settings.hasApiKey || !settings.model) {
    setRuntimeLabel("api missing");
    statusNode.textContent = "请在设置里添加 API";
  }
  return settings;
}

async function saveApiSettings() {
  const apiKey = $("#api-key").value.trim();
  const baseUrl = $("#api-base-url").value.trim();
  const model = $("#api-model").value.trim();
  const imageBaseUrl = $("#api-image-base-url").value.trim();
  const imageModel = $("#api-image-model").value.trim();
  const payload = {
    clearApiKey: $("#api-clear-key").checked,
    temperature: Number($("#api-temperature").value || 0.2),
    imageSize: $("#api-image-size").value,
    imageQuality: $("#api-image-quality").value,
    imageOutputFormat: $("#api-image-format").value,
  };
  if (baseUrl) payload.baseUrl = baseUrl;
  if (model) payload.model = model;
  if (apiKey) payload.apiKey = apiKey;
  if (imageBaseUrl) payload.imageBaseUrl = imageBaseUrl;
  if (imageModel) payload.imageModel = imageModel;

  const settings = await fetch("/api/v1/settings/llm", {
    method: "PUT",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  }).then((response) => {
    if (!response.ok) throw new Error(`API 设置保存失败：${response.status}`);
    return response.json();
  });

  $("#api-key").value = "";
  $("#api-clear-key").checked = false;
  $("#api-status").textContent = `已保存 · ${summarizeApiSettings(settings)}`;
  state.apiReady = Boolean(settings.hasApiKey && settings.model);
  if (settings.hasApiKey && settings.model) {
    setRuntimeLabel("api ready");
    statusNode.textContent = "API 已配置，可以生成";
    if (state.prefs.autoGenerate && state.article && state.sessionId && !state.prewarm.running) {
      prewarmArticleWorkflows();
    }
  }
}

function bindSettings() {
  const safe = (sel, event, handler) => {
    const el = $(sel);
    if (!el) return;
    el.addEventListener(event, (...args) => {
      const result = handler(...args);
      if (result && typeof result.catch === "function") {
        result.catch((error) => { statusNode.textContent = error.message || "操作失败"; });
      }
    });
  };
  safe("#settings-open", "click", async () => {
    await loadApiSettings();
    $("#settings-dialog").showModal();
  });
  safe("#settings-close", "click", () => $("#settings-dialog").close());
  safe("#tool-dialog-close", "click", closeToolDialog);
  safe("#search-open", "click", async () => {
    await loadApiSettings();
    searchDialog.showModal();
    renderSearchResults();
    window.requestAnimationFrame(() => $("#article-search")?.focus());
  });
  safe("#search-dialog-close", "click", () => searchDialog.close());
  safe("#note-open", "click", async () => {
    await loadApiSettings();
    loadArticleNote();
    noteDialog.showModal();
  });
  safe("#note-dialog-close", "click", () => noteDialog.close());
  safe("#article-note", "input", saveArticleNote);
  safe("#font-open", "click", async () => {
    await loadApiSettings();
    $("#settings-dialog").showModal();
    window.requestAnimationFrame(() => {
      const section = $(".settings-section[aria-labelledby='appearance-settings-title']");
      if (section) section.scrollIntoView({block: "start", behavior: "smooth"});
    });
  });
  safe("#open-anchors", "click", () => openToolDialog("锚点", {showAgent: false, showTimeline: true}));
  safe("#article-search", "input", renderSearchResults);
  safe("#map-keyword-form", "submit", (event) => {
    event.preventDefault();
    const input = $("#map-keyword");
    addMapKeyword(input.value);
    input.value = "";
  });
  safe("#map-dialog-close", "click", () => mapDialog.close());
  safe("#api-save", "click", () => {
    saveApiSettings().catch((error) => {
      $("#api-status").textContent = error.message || "API 设置保存失败";
    });
  });

  safe("#pref-font-size", "input", (event) => {
    state.prefs.fontSize = Number(event.target.value);
    applyPrefs();
    savePrefs();
  });
  safe("#pref-line-height", "input", (event) => {
    state.prefs.lineHeight = Number(event.target.value);
    applyPrefs();
    savePrefs();
  });
  safe("#pref-auto-generate", "change", (event) => {
    state.prefs.autoGenerate = event.target.checked;
    savePrefs();
  });
  safe("#pref-show-events", "change", (event) => {
    state.prefs.showEvents = event.target.checked;
    applyPrefs();
    savePrefs();
  });

  const themeSwatches = $("#theme-swatches");
  if (themeSwatches) {
    themeSwatches.addEventListener("click", (event) => {
      const swatch = event.target.closest(".swatch");
      if (!swatch) return;
      themeSwatches.querySelectorAll(".swatch").forEach((s) => s.classList.remove("active"));
      swatch.classList.add("active");
      state.prefs.theme = swatch.dataset.theme;
      applyTheme(swatch.dataset.theme);
      savePrefs();
    });
  }
}

function applyTheme(theme) {
  const root = document.documentElement;
  root.classList.remove("theme-dark", "theme-green", "theme-blue");
  if (theme === "dark") root.classList.add("theme-dark");
  else if (theme === "green") root.classList.add("theme-green");
  else if (theme === "blue") root.classList.add("theme-blue");
}

async function createReadingSession() {
  const session = await fetch("/api/v1/reading-sessions", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      releaseId: state.article.releaseId,
      articleId: state.article.articleId,
      anchorId: state.anchorId,
      mode: MODE,
      client: {device: "web"},
    }),
  }).then((response) => {
    if (!response.ok) throw new Error(`会话创建失败：${response.status}`);
    return response.json();
  });
  state.sessionId = session.sessionId;
}

function renderArticle() {
  $("#title").textContent = state.article.title;
  $("#meta").textContent = `${state.article.anchors.length} / ${state.article.paragraphs.length}`;
  $("#reader-title").textContent = state.article.title;
  $("#article-folio").textContent = `${state.article.paragraphs.length} 段 · ${state.article.anchors.length} 锚点`;
  $("#anchor-badge").textContent = state.article.coreQuestion || articleMeta(state.article);
  reader.innerHTML = state.article.paragraphs
    .map((paragraph) => `<p class="paragraph" data-id="${escapeHtml(paragraph.paragraphId)}" data-anchor="${escapeHtml(paragraph.anchorId)}">${escapeHtml(paragraph.text)}</p>`)
    .join("");
  setActiveAnchor(state.anchorId);
  renderExplorationSurface();

  document.querySelectorAll(".paragraph").forEach((node) => {
    node.addEventListener("click", () => {
      const anchorId = node.dataset.anchor;
      setActiveAnchor(anchorId);
      statusNode.textContent = "已定位段落，可选择文本或打开工具";
    });
  });
}

function noteStorageKey() {
  const releaseId = state.article?.releaseId || state.article?.currentReleaseId || "release";
  const articleId = state.article?.articleId || "article";
  return `mzd_note_${releaseId}_${articleId}`;
}

function loadArticleNote() {
  const note = localStorage.getItem(noteStorageKey()) || "";
  $("#article-note").value = note;
  $("#note-status").textContent = note ? "已从本机恢复" : "自动保存到本机";
}

function saveArticleNote() {
  localStorage.setItem(noteStorageKey(), $("#article-note").value);
  $("#note-status").textContent = "已保存到本机";
}

function paragraphSnippet(text, query) {
  const source = String(text || "");
  if (!query) return source.slice(0, 110);
  const index = source.indexOf(query);
  if (index < 0) return source.slice(0, 110);
  const start = Math.max(0, index - 34);
  const end = Math.min(source.length, index + query.length + 76);
  return `${start > 0 ? "..." : ""}${source.slice(start, end)}${end < source.length ? "..." : ""}`;
}

function renderSearchResults() {
  const input = $("#article-search");
  const container = $("#search-results");
  const paragraphs = state.article?.paragraphs || [];
  const query = input.value.trim();
  const results = query
    ? paragraphs.filter((paragraph) => paragraph.text.includes(query)).slice(0, 16)
    : paragraphs.slice(0, 8);

  if (!paragraphs.length) {
    container.innerHTML = '<p class="search-empty">正文尚未加载</p>';
    return;
  }
  if (query && !results.length) {
    container.innerHTML = '<p class="search-empty">没有找到匹配段落</p>';
    return;
  }

  container.innerHTML = results
    .map((paragraph, index) => {
      const paragraphIndex = paragraphs.findIndex((item) => item.paragraphId === paragraph.paragraphId);
      const labelIndex = paragraphIndex >= 0 ? paragraphIndex + 1 : index + 1;
      return `
        <button type="button" class="search-result" data-search-paragraph="${escapeHtml(paragraph.paragraphId)}">
          <span>第 ${labelIndex} 段</span>
          <strong>${escapeHtml(paragraph.anchorTitle || paragraph.anchorId || "正文段落")}</strong>
          <small>${escapeHtml(paragraphSnippet(paragraph.text, query))}</small>
        </button>
      `;
    })
    .join("");
}

function focusParagraph(paragraphId) {
  const paragraphNode = document.querySelector(`.paragraph[data-id="${CSS.escape(paragraphId)}"]`);
  const paragraph = state.article?.paragraphs?.find((item) => item.paragraphId === paragraphId);
  if (!paragraphNode || !paragraph) return;
  setActiveAnchor(paragraph.anchorId);
  paragraphNode.scrollIntoView({behavior: "smooth", block: "center"});
  paragraphNode.classList.add("search-hit");
  window.setTimeout(() => paragraphNode.classList.remove("search-hit"), 1400);
  statusNode.textContent = "已定位搜索段落";
}

function renderExplorationSurface() {
  const anchors = state.article.anchors.slice(0, 12);
  const timeline = $("#timeline");
  if (timeline) {
    timeline.innerHTML = anchors
      .map((anchor, index) => `
        <button type="button" class="timeline-item" data-panel="timeline" data-workflow="timeline" data-target-type="timeline" data-target-id="${escapeHtml(anchor.anchorId)}" data-target-label="${escapeHtml(anchor.title)}" data-source-ids="${escapeHtml(anchor.paragraphIds.join(","))}">
          <span class="timeline-index">${index + 1}</span>
          <span class="timeline-title">${escapeHtml(anchor.title)}</span>
          <small>${anchor.paragraphIds.length} 段</small>
        </button>
      `)
      .join("");
  }
  hydrateIcons();
}

async function loadArticle(summary) {
  if (state.loadingArticle) return;
  state.loadingArticle = true;
  try {
    if (state.stream) state.stream.close();
    cancelBackgroundWorkflows();
    state.uiVersion += 1;
    state.selection = null;
    state.map.variables = [];
    state.map.keywordCount = 0;
    setMapStatus("即时变量");
    clearMapLayers();
    $("#analyze").disabled = true;
    resetContextCards();
    resetAgent();
    const analysisContent = $("#analysis-content");
    const analysisLoading = $("#analysis-loading");
    if (analysisContent) { analysisContent.hidden = true; analysisContent.innerHTML = ""; }
    if (analysisLoading) { analysisLoading.hidden = false; analysisLoading.innerHTML = '<span class="pulse" aria-hidden="true"></span><span>正在分析文章...</span>'; }
    setRuntimeLabel("loading");
    statusNode.textContent = "正在加载文章";

    state.article = await fetch(`/api/v1/articles/${summary.articleId}?releaseId=${summary.currentReleaseId}`).then((response) => {
      if (!response.ok) throw new Error(`文章加载失败：${response.status}`);
      return response.json();
    });
    state.anchorId = state.article.anchors[0]?.anchorId || null;
    renderArticle();
    await createReadingSession();

    setRuntimeLabel("ready");
    if (state.prefs.autoGenerate && state.apiReady) {
      startWorkflow("article_overview", articleOverviewTarget());
      prewarmArticleWorkflows();
      setTimeout(() => {
        submitInteraction("anchor_changed", {anchorId: state.anchorId, openDialog: false, inline: true});
      }, 800);
    } else if (state.prefs.autoGenerate) {
      setRuntimeLabel("api missing");
      statusNode.textContent = "请在设置里添加 API 后生成";
    } else {
      statusNode.textContent = "已关闭自动生成，点击段落或提问开始";
    }
  } finally {
    state.loadingArticle = false;
  }
}

function setActiveAnchor(anchorId) {
  state.anchorId = anchorId;
  document.querySelectorAll(".paragraph").forEach((node) => {
    node.classList.toggle("active", node.dataset.anchor === anchorId);
  });
  const anchor = state.article.anchors.find((item) => item.anchorId === anchorId);
  $("#anchor-badge").textContent = anchor ? anchor.title : anchorId;
}

function workflowTargetFromButton(button) {
  const sourceIds = (button.dataset.sourceIds || "").split(",").map((item) => item.trim()).filter(Boolean);
  const targetType = button.dataset.targetType || "anchor";
  const isArticleTarget = targetType === "article";
  return {
    targetType,
    targetId: button.dataset.targetId || (isArticleTarget ? state.article.articleId : state.anchorId),
    label: button.dataset.targetLabel || button.textContent.trim(),
    sourceIds: sourceIds.length ? sourceIds : (isArticleTarget ? articleSourceIds(20) : anchorSourceIds(state.anchorId)),
  };
}

function renderSubagent(name) {
  const chip = document.createElement("span");
  chip.className = "subagent-chip";
  chip.textContent = formatSubagentName(name);
  subagentQueue.append(chip);
}

function setAgentImageLoading(text) {
  agentImage.hidden = false;
  agentImage.innerHTML = `<div class="generated-loading">${escapeHtml(text)}</div>`;
}

function renderAgentImage(data) {
  const cached = data.cached ? " · 复用真实生成结果" : "";
  agentImage.hidden = false;
  agentImage.innerHTML = `
    <figure>
      <img src="${escapeHtml(data.imageUrl)}" alt="AI 生成的文章插图" loading="lazy" />
      <figcaption>${escapeHtml(data.model || "image model")}${cached}</figcaption>
    </figure>
  `;
}

function clearMapLayers() {
  state.map.layers.forEach((layer) => layer.remove());
  state.map.layers = [];
}

function mapColor(variable) {
  if (variable.kind === "scope") return "#9d3b2f";
  if (variable.kind === "keyword") return "#b9873d";
  if (variable.kind === "地点") return "#2f6f5e";
  if (variable.kind === "区域" || variable.kind === "路线") return "#4f6696";
  if (variable.kind === "time") return "#8b6914";
  if (variable.kind === "semantic") return "#386f90";
  return "#2f6f5e";
}

function shortMapLabel(label) {
  const compact = String(label || "").replace(/^第\d+组[:：]\s*/, "").replace(/\s+/g, "");
  return compact.length > 9 ? `${compact.slice(0, 8)}…` : compact;
}

function renderMapVariableList() {
  $("#map-variable-list").innerHTML = state.map.variables
    .map((item) => `
      <button type="button" class="map-variable" data-map-variable="${escapeHtml(item.id)}">
        <span style="--dot:${escapeHtml(mapColor(item))}"></span>
        <strong>${escapeHtml(item.label)}</strong>
        <em>${escapeHtml(item.description || "基于原文生成的语义变量")}</em>
        <small>${item.sourceIds?.length || item.weight || 1}</small>
        <b aria-hidden="true">›</b>
      </button>
    `)
    .join("");
}

function renderInstantMap() {
  const target = $("#history-map");
  if (!target) return;
  if (typeof L === "undefined") {
    target.innerHTML = '<div class="map-fallback">地图组件未加载，请刷新页面。</div>';
    return;
  }
  if (!state.map.instance) {
    state.map.instance = L.map(target, {
      zoomControl: false,
      attributionControl: false,
      scrollWheelZoom: true,
      doubleClickZoom: true,
      keyboard: true,
      keyboardPanDelta: 120,
      dragging: true,
      touchZoom: true,
    }).setView([35.8, 104.2], 4);
    state.map.tileLayer = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 12,
      minZoom: 3,
      opacity: 0.62,
      crossOrigin: true,
    }).addTo(state.map.instance);
    L.control.zoom({position: "bottomleft"}).addTo(state.map.instance);
  }
  state.map.instance.invalidateSize();
  clearMapLayers();
  let overlay = target.querySelector(".map-empty-overlay");
  if (!state.map.variables.length) {
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "map-empty-overlay";
      overlay.innerHTML = '<span>等待 AI 生成地图坐标...</span>';
      target.appendChild(overlay);
    }
    renderMapVariableList();
    setMapStatus("等待 AI");
    return;
  }
  if (overlay) overlay.remove();
  const points = state.map.variables.map((item) => [item.lat, item.lng]);
  if (points.length > 1) {
    state.map.layers.push(
      L.polyline(points, {
        color: "#9d3b2f",
        weight: 2,
        opacity: 0.58,
        dashArray: "8 8",
      }).addTo(state.map.instance)
    );
  }
  state.map.variables.forEach((item, index) => {
    const marker = L.circleMarker([item.lat, item.lng], {
      radius: item.kind === "scope" ? 11 : 7,
      color: "#fffdf7",
      weight: 2,
      fillColor: mapColor(item),
      fillOpacity: 0.92,
    }).addTo(state.map.instance);
    marker.bindTooltip(`${shortMapLabel(item.label)}${item.sourceIds?.length ? ` ${item.sourceIds.length}` : ""}`, {
      direction: "top",
      offset: [0, -8],
      permanent: index < 6 || item.kind === "keyword" || item.kind === "scope",
      className: "semantic-map-label",
    });
    state.map.layers.push(marker);
  });
  if (points.length) {
    state.map.instance.fitBounds(points, {padding: [40, 40], maxZoom: 8, animate: true, duration: 0.6});
  }
  renderMapVariableList();
  setMapStatus(state.map.aiStatus || "即时变量");
}

function addMapKeyword(keyword) {
  const trimmed = keyword.trim();
  if (!trimmed) return;
  state.map.keywordCount += 1;
  const index = state.map.keywordCount;
  state.map.variables.push({
    id: `keyword_${Date.now()}_${index}`,
    label: trimmed,
    sourceIds: anchorSourceIds(state.anchorId),
    lat: 31.2 + (index % 5) * 1.6,
    lng: 99.5 + (index % 7) * 1.9,
    weight: 1,
    kind: "keyword",
  });
  renderInstantMap();
}

function normalizeAgentMapVariable(item, index) {
  const lat = Number(item.lat);
  const lng = Number(item.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || !item.label) return null;
  return {
    id: item.id || `ai_map_${index}_${Date.now()}`,
    label: item.label,
    description: item.description || "",
    sourceIds: Array.isArray(item.sourceIds) ? item.sourceIds : [],
    lat,
    lng,
    weight: Number(item.weight) || 1,
    kind: item.kind || "semantic",
  };
}

function applyAgentMapVariables(data) {
  const incoming = (data.variables || [])
    .map((item, index) => normalizeAgentMapVariable(item, index))
    .filter(Boolean);
  if (!incoming.length) return;
  const keywordVariables = state.map.variables.filter((item) => item.kind === "keyword");
  state.map.variables = [...incoming, ...keywordVariables];
  setMapStatus(data.cached ? "AI 已复用" : "AI 已更新");
  renderInstantMap();
}

function friendlyError(message) {
  if (!message) return "工作流失败";
  if (message.includes("Missing required LLM setting")) return "需要先在设置中添加 API Key 和文本模型。";
  if (message.includes("Missing required image setting")) return "需要先在设置中添加图像 API Key 或图像模型配置。";
  if (message.includes("provider returned")) return "模型服务返回错误，请检查模型名称、额度或 Base URL。";
  return message;
}

function renderAgentNotice(title, message) {
  subagentQueue.innerHTML = "";
  agentImage.hidden = true;
  agentImage.innerHTML = "";
  agentOutput.classList.remove("empty");
  agentOutput.classList.add("notice-mode");
  agentOutput.innerHTML = `
    <div class="agent-notice">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(message)}</p>
      <button type="button" data-open-settings>打开设置</button>
    </div>
  `;
}

function formatAgentText(text) {
  if (!text) return "";
  const lines = text.split("\n");
  let result = [];
  let section = "";
  let collectLines = [];
  const flushSection = () => {
    if (section && collectLines.length) {
      result.push(renderSection(section, collectLines));
      collectLines = [];
    }
    section = "";
  };
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const sectionMatch = trimmed.match(/^(标题|摘要|发现|建议点击|地图变量|插图提示)\s*[：:]\s*(.*)$/);
    if (sectionMatch) {
      flushSection();
      section = sectionMatch[1];
      if (sectionMatch[2]) collectLines.push(sectionMatch[2]);
      continue;
    }
    if (trimmed.startsWith("- ") || trimmed.startsWith("· ") || trimmed.startsWith("• ")) {
      collectLines.push(trimmed.slice(2));
      continue;
    }
    collectLines.push(trimmed);
  }
  flushSection();
  if (!result.length) return escapeHtml(text);
  return result.join("");
}

function renderSection(title, lines) {
  const body = lines.join("\n");
  switch (title) {
    case "标题":
      return `<h3 class="agent-section-title">${escapeHtml(body)}</h3>`;
    case "摘要":
      return `<p class="agent-section-summary">${escapeHtml(body)}</p>`;
    case "发现":
      return renderDiscoveries(lines);
    case "建议点击":
      return renderSuggestions(lines);
    case "地图变量":
      return renderMapVars(lines);
    case "插图提示":
      return `<div class="agent-meta"><span class="agent-meta-label">插图提示</span>${escapeHtml(body)}</div>`;
    default:
      return `<p>${escapeHtml(body)}</p>`;
  }
}

function renderDiscoveries(lines) {
  let html = '<div class="agent-discoveries">';
  for (const line of lines) {
    const parts = line.split("｜").map((s) => s.trim());
    if (parts.length < 2) {
      html += `<div class="discovery-item"><span class="discovery-text">${escapeHtml(line)}</span></div>`;
      continue;
    }
    const kind = parts[0];
    const name = parts[1];
    const desc = parts[2] || "";
    const sources = parts[3] || "";
    const sourceIds = sources.replace(/p_mzd_\d+_/g, "").replace(/,\s*$/, "");
    const kindClass = kind.includes("组织") ? "org" : kind.includes("阶级") ? "class" : kind.includes("人物") ? "person" : "other";
    html += `<div class="discovery-item">
      <span class="discovery-kind ${kindClass}">${escapeHtml(kind)}</span>
      <strong class="discovery-name">${escapeHtml(name)}</strong>
      <span class="discovery-desc">${escapeHtml(desc)}</span>
      ${sourceIds ? `<small class="discovery-src">${escapeHtml(sourceIds)}</small>` : ""}
    </div>`;
  }
  html += "</div>";
  return html;
}

function renderSuggestions(lines) {
  let html = '<div class="agent-suggestions">';
  for (const line of lines) {
    const parts = line.split("｜").map((s) => s.trim());
    if (parts.length >= 2) {
      html += `<span class="agent-suggestion-item">${escapeHtml(parts[1])}</span>`;
    } else {
      html += `<span class="agent-suggestion-item">${escapeHtml(line)}</span>`;
    }
  }
  html += "</div>";
  return html;
}

function renderMapVars(lines) {
  let html = '<div class="agent-map-vars">';
  for (const line of lines) {
    const parts = line.split("｜").map((s) => s.trim());
    if (parts.length >= 2) {
      const kind = parts[0];
      const label = parts[1];
      const desc = parts[2] || "";
      const kindColor = kind.includes("地点") ? "#2f6f5e" : kind.includes("区域") ? "#4f6696" : "#386f90";
      html += `<div class="map-var-item">
        <span class="map-var-dot" style="background:${kindColor}"></span>
        <strong>${escapeHtml(label)}</strong>
        <em>${escapeHtml(desc)}</em>
      </div>`;
    }
  }
  html += "</div>";
  return html;
}

function formatSubagentName(name) {
  const map = {
    "article_scanner": "文章扫描",
    "context_mapper": "语境映射",
    "reasoning_synthesizer": "推理综合",
    "temporal_extractor": "时间提取",
    "sequence_checker": "时序校验",
    "figure_extractor": "人物提取",
    "relation_mapper": "关系映射",
    "event_extractor": "事件提取",
    "causal_chain_checker": "因果链校验",
    "place_extractor": "地点提取",
    "spatial_context_mapper": "空间语境",
    "scene_selector": "场景选择",
    "image_prompt_writer": "图像提示",
  };
  return map[name] || name;
}

async function startWorkflow(workflow, target, options = {}) {
  if (!state.article || !state.sessionId || !state.anchorId) return;

  const isInline = workflow === "article_overview" && options.inline !== false;

  if (isInline) {
    const panel = $("#analysis-content");
    const loading = $("#analysis-loading");
    if (panel) { panel.hidden = true; panel.innerHTML = ""; }
    if (loading) loading.hidden = false;
  } else {
    modalAgent.hidden = false;
  }

  if (!state.apiReady) {
    setAgentStatus("api missing");
    if (!isInline) {
      $("#agent-regenerate").disabled = true;
      renderAgentNotice("还不能生成", "请先在设置里添加 API Key 和文本模型。配置完成后再点击这个工具。");
    }
    return;
  }

  state.agentVersion += 1;
  const currentVersion = state.agentVersion;
  if (state.workflowStream) state.workflowStream.close();
  state.lastWorkflowRequest = {
    workflow,
    target: typeof structuredClone === "function" ? structuredClone(target) : JSON.parse(JSON.stringify(target)),
  };
  subagentQueue.innerHTML = "";
  agentImage.hidden = true;
  agentImage.innerHTML = "";
  agentOutput.classList.remove("empty");
  agentOutput.classList.remove("notice-mode");
  agentOutput.textContent = "正在连接真实大模型...\n如果等待超过 20 秒，请检查网络、模型名称或 API 额度。";
  $("#agent-regenerate").disabled = true;
  setAgentStatus("running");

  const payload = {
    releaseId: state.article.releaseId,
    articleId: state.article.articleId,
    anchorId: state.anchorId,
    workflow,
    target,
    mode: MODE,
    uiVersion: currentVersion,
    occurredAt: new Date().toISOString(),
    forceRegenerate: Boolean(options.forceRegenerate),
  };

  let accepted;
  try {
    accepted = await fetch(`/api/v1/reading-sessions/${state.sessionId}/workflows`, {
      method: "POST",
      headers: {"Content-Type": "application/json", "Idempotency-Key": idempotencyKey()},
      body: JSON.stringify(payload),
    }).then((response) => {
      if (!response.ok) throw new Error(`工作流创建失败：${response.status}`);
      return response.json();
    });
  } catch (error) {
    if (!options.silentFailure) {
      agentOutput.textContent = error.message || "工作流创建失败";
      setAgentStatus("failed");
      $("#agent-regenerate").disabled = !state.lastWorkflowRequest;
    }
    return;
  }

  const source = new EventSource(accepted.streamUrl);
  state.workflowStream = source;
  const types = [
    "workflow.accepted",
    "subagent.started",
    "artifact.block",
    "artifact.committed",
    "map.variables.committed",
    "image.started",
    "image.committed",
    "image.failed",
    "workflow.completed",
    "workflow.failed",
  ];
  types.forEach((type) => {
    source.addEventListener(type, (event) => {
      let data;
      try { data = JSON.parse(event.data); } catch { return; }
      if (data.uiVersion !== state.agentVersion) return;

      if (type === "workflow.accepted") {
        agentOutput.textContent = `# ${data.title}${data.cached ? " · 复用" : ""}\n\n`;
      }
      if (type === "subagent.started") renderSubagent(data.subagent);
      if (type === "artifact.block") {
        if (isInline) {
          renderAnalysisPanel(data.text);
        } else {
          agentOutput.classList.remove("empty");
          agentOutput.innerHTML = formatAgentText(data.text);
          agentOutput.scrollTop = agentOutput.scrollHeight;
        }
      }
      if (type === "artifact.committed") {
        if (isInline) {
          renderAnalysisPanel(data.text);
        } else {
          agentOutput.classList.remove("empty");
          const displayText = data.cached ? `${data.text}\n\n[已复用上次真实生成结果]` : data.text;
          agentOutput.innerHTML = formatAgentText(displayText);
          agentOutput.scrollTop = 0;
        }
      }
      if (type === "map.variables.committed") applyAgentMapVariables(data);
      if (type === "image.started") setAgentImageLoading("图像模型正在生成");
      if (type === "image.committed") renderAgentImage(data);
      if (type === "image.failed") setAgentImageLoading(data.error?.message || "图像生成失败");
      if (type === "workflow.completed") {
        const loading = $("#analysis-loading");
        if (loading) loading.hidden = true;
        document.querySelectorAll(".context-card.loading").forEach((node) => node.classList.remove("loading"));
        setAgentStatus("completed");
        if (!isInline) $("#agent-regenerate").disabled = !state.lastWorkflowRequest;
        source.close();
      }
      if (type === "workflow.failed") {
        const loading = $("#analysis-loading");
        if (loading) loading.hidden = true;
        document.querySelectorAll(".context-card.loading").forEach((node) => node.classList.remove("loading"));
        if (isInline) {
          if (loading) loading.innerHTML = `<span style="color:var(--oxide)">分析失败：${escapeHtml(friendlyError(data.error?.message))}</span>`;
          loading.hidden = false;
        } else if (!options.silentFailure) {
          agentOutput.classList.remove("empty");
          agentOutput.classList.remove("notice-mode");
          agentOutput.textContent = friendlyError(data.error?.message);
        }
        setAgentStatus("failed");
        if (!isInline) $("#agent-regenerate").disabled = !state.lastWorkflowRequest;
        source.close();
      }
    });
  });

  source.onerror = () => {
    if (!options.silentFailure) agentOutput.textContent = "工作流事件流连接中断";
    setAgentStatus("failed");
    $("#agent-regenerate").disabled = !state.lastWorkflowRequest;
    source.close();
  };
}

async function runBackgroundWorkflow(workflow, target, version) {
  const payload = {
    releaseId: state.article.releaseId,
    articleId: state.article.articleId,
    anchorId: state.anchorId,
    workflow,
    target,
    mode: MODE,
    uiVersion: version,
    occurredAt: new Date().toISOString(),
    forceRegenerate: false,
  };

  const accepted = await fetch(`/api/v1/reading-sessions/${state.sessionId}/workflows`, {
    method: "POST",
    headers: {"Content-Type": "application/json", "Idempotency-Key": idempotencyKey()},
    body: JSON.stringify(payload),
  }).then((response) => {
    if (!response.ok) throw new Error(`后台工作流创建失败：${response.status}`);
    return response.json();
  });

  const source = new EventSource(accepted.streamUrl);
  state.prewarm.streams.push(source);

  return new Promise((resolve) => {
    const closeSource = (status = "settled") => {
      clearTimeout(timer);
      source.close();
      state.prewarm.streams = state.prewarm.streams.filter((item) => item !== source);
      resolve(status);
    };
    const timer = setTimeout(() => closeSource("timeout"), 60000);

    source.addEventListener("map.variables.committed", (event) => {
      let data;
      try { data = JSON.parse(event.data); } catch { return; }
      if (version !== state.prewarm.version) return;
      applyAgentMapVariables(data);
    });
    source.addEventListener("workflow.completed", () => {
      closeSource("completed");
    });
    source.addEventListener("workflow.failed", () => {
      closeSource("failed");
    });
    source.onerror = () => closeSource("error");
  });
}

function prewarmArticleWorkflows() {
  if (!state.apiReady || !state.article || !state.sessionId) return;
  cancelBackgroundWorkflows();
  state.prewarm.running = true;
  const version = state.prewarm.version;
  setRuntimeLabel("preparing");
  statusNode.textContent = "正在后台准备全篇与地图变量";
  setMapStatus("AI 准备中");
  Promise.allSettled([
    runBackgroundWorkflow("map_context", mapContextTarget(), version),
  ]).then((results) => {
    if (version !== state.prewarm.version) return;
    state.prewarm.running = false;
    setRuntimeLabel("ready");
    const okCount = results.filter((item) => item.status === "fulfilled" && item.value === "completed").length;
    statusNode.textContent = okCount ? "后台内容已准备" : "后台准备未完成，可稍后重试";
    if (state.map.aiStatus === "AI 准备中") setMapStatus("即时变量");
  });
}

document.addEventListener("click", (event) => {
  const settingsTrigger = event.target.closest("[data-open-settings]");
  if (settingsTrigger) {
    closeToolDialog();
    loadApiSettings().then(() => $("#settings-dialog").showModal()).catch((error) => {
      statusNode.textContent = error.message || "设置加载失败";
    });
    return;
  }

  const mapTrigger = event.target.closest("[data-map-panel]");
  if (mapTrigger) {
    mapDialog.showModal();
    window.requestAnimationFrame(() => renderInstantMap());
    return;
  }

  const mapVariable = event.target.closest("[data-map-variable]");
  if (mapVariable && state.map.instance) {
    const variable = state.map.variables.find((item) => item.id === mapVariable.dataset.mapVariable);
    if (variable) state.map.instance.flyTo([variable.lat, variable.lng], 5, {duration: 0.45});
    return;
  }

  const searchResult = event.target.closest("[data-search-paragraph]");
  if (searchResult) {
    focusParagraph(searchResult.dataset.searchParagraph);
    closeToolDialog();
    return;
  }

  const button = event.target.closest("[data-workflow]");
  if (!button) return;
  const workflow = button.dataset.workflow;
  const title = button.dataset.targetLabel || button.textContent.trim() || "探索";
  if (workflow === "article_overview") {
    startWorkflow(workflow, workflowTargetFromButton(button), {inline: true}).catch((error) => {
      const loading = $("#analysis-loading");
      if (loading) loading.innerHTML = `<span style="color:var(--oxide)">分析失败：${escapeHtml(error.message || "工作流失败")}</span>`;
    });
    return;
  }
  if (workflow === "map_context") {
    startWorkflow(workflow, workflowTargetFromButton(button)).catch((error) => {
      statusNode.textContent = error.message || "地图工作流失败";
    });
    return;
  }
  openToolDialog(title, {
    showAgent: true,
    showTimeline: button.dataset.panel === "timeline",
  });
  startWorkflow(workflow, workflowTargetFromButton(button)).catch((error) => {
    agentOutput.textContent = error.message || "工作流失败";
    setAgentStatus("failed");
  });
});

$("#agent-regenerate").addEventListener("click", () => {
  if (!state.lastWorkflowRequest) return;
  startWorkflow(state.lastWorkflowRequest.workflow, state.lastWorkflowRequest.target, {forceRegenerate: true}).catch((error) => {
    agentOutput.textContent = error.message || "重新生成失败";
    setAgentStatus("failed");
  });
});

function paragraphFromSelection(selection) {
  if (!selection || selection.rangeCount === 0) return null;
  const node = selection.anchorNode?.nodeType === Node.TEXT_NODE ? selection.anchorNode.parentElement : selection.anchorNode;
  return node?.closest?.(".paragraph") || null;
}

async function submitInteraction(eventType, options = {}) {
  if (!state.article || !state.sessionId || !state.anchorId) return;

  const isInline = options.inline === true;

  if (!isInline && options.openDialog !== false) {
    openToolDialog("实时情境", {showAgent: false, showContext: true});
  }

  state.uiVersion += 1;
  const currentVersion = state.uiVersion;
  if (state.stream) state.stream.close();
  eventLog.textContent = "";
  setRuntimeLabel("streaming");
  statusNode.textContent = "大模型正在生成";

  if (!isInline) {
    document.querySelectorAll(".context-card").forEach((node) => node.classList.add("loading"));
  }

  const payload = {
    eventType,
    releaseId: state.article.releaseId,
    articleId: state.article.articleId,
    anchorId: options.anchorId || state.anchorId,
    paragraphId: options.paragraphId || null,
    selection: options.selection || null,
    entityId: null,
    entityType: null,
    mode: MODE,
    question: options.question || null,
    currentUiHash: null,
    uiVersion: currentVersion,
    occurredAt: new Date().toISOString(),
    clientContext: {device: "web"},
  };

  const accepted = await fetch(`/api/v1/reading-sessions/${state.sessionId}/interactions`, {
    method: "POST",
    headers: {"Content-Type": "application/json", "Idempotency-Key": idempotencyKey()},
    body: JSON.stringify(payload),
  }).then((response) => {
    if (!response.ok) throw new Error(`交互创建失败：${response.status}`);
    return response.json();
  });

  const source = new EventSource(accepted.streamUrl);
  state.stream = source;

  const types = [
    "interaction.accepted",
    "plan.committed",
    "slot.started",
    "slot.block",
    "slot.committed",
    "interaction.completed",
    "interaction.failed",
  ];

  types.forEach((type) => {
    source.addEventListener(type, (event) => {
      let data;
      try { data = JSON.parse(event.data); } catch { return; }
      logEvent(type, data);
      if (data.uiVersion !== state.uiVersion) return;

      if (type === "plan.committed") {
        data.updateSlots.forEach((slot) => cardForSlot(slot)?.classList.add("loading"));
      }
      if (type === "slot.block") renderPartial(data.slot, data.text);
      if (type === "slot.committed") {
        if (isInline) {
          const p = data.payload;
          const slot = data.slot;
          const panel = $("#analysis-content");
          if (panel && p) {
            const label = slot === "writing_context" ? "写作背景" : slot === "era_context" ? "时代背景" : "核心论点";
            const cls = slot === "era_context" ? "situation" : slot === "core_argument" ? "argument" : "";
            const cardHtml = `<div class="context-card-inline ${cls}"><h4>${escapeHtml(label)}</h4><p>${escapeHtml(p.summary || "")}</p></div>`;
            panel.innerHTML += cardHtml;
          }
        } else {
          renderCard(data.payload);
        }
      }
      if (type === "interaction.completed") {
        statusNode.textContent = "生成完成";
        setRuntimeLabel("ready");
        source.close();
      }
      if (type === "interaction.failed") {
        markFailed(data.error?.message || "生成失败");
        source.close();
      }
    });
  });

  source.onerror = () => {
    markFailed("事件流连接中断");
    source.close();
  };
}

async function init() {
  hydrateIcons();
  state.prefs = loadPrefs();
  bindSettings();
  applyPrefs();
  await loadApiSettings();

  const list = await fetch("/api/v1/articles").then((response) => response.json());
  state.articles = list.items || [];
  if (!state.articles.length) throw new Error("未找到本地毛选语料目录");

  const select = $("#article-select");
  select.innerHTML = state.articles
    .map((item) => `<option value="${escapeHtml(articleOptionValue(item))}">${escapeHtml(`${item.articleId.replace("art_mzd_", "")} · ${item.title}`)}</option>`)
    .join("");
  select.addEventListener("change", async () => {
    const selected = state.articles.find((item) => articleOptionValue(item) === select.value);
    if (selected) {
      try {
        await loadArticle(selected);
      } catch (error) {
        statusNode.textContent = error.message || "加载文章失败";
      }
    }
  });

  await loadArticle(state.articles[0]);
}

const selectionToolbar = $("#selection-toolbar");

reader.addEventListener("mouseup", (e) => {
  const selection = window.getSelection();
  const text = selection ? selection.toString().trim() : "";
  if (!text) {
    state.selection = null;
    $("#analyze").disabled = true;
    selectionToolbar.hidden = true;
    return;
  }
  const node = paragraphFromSelection(selection);
  if (!node) return;
  state.selection = {
    text,
    startParagraphId: node.dataset.id,
    endParagraphId: node.dataset.id,
    startOffset: null,
    endOffset: null,
  };
  $("#analyze").disabled = false;
  statusNode.textContent = `${text.length} 字`;
  const rect = selection.getRangeAt(0).getBoundingClientRect();
  selectionToolbar.hidden = false;
  selectionToolbar.style.left = `${rect.left + rect.width / 2 - selectionToolbar.offsetWidth / 2}px`;
  selectionToolbar.style.top = `${rect.top - selectionToolbar.offsetHeight - 8}px`;
});

document.addEventListener("mousedown", (e) => {
  if (!selectionToolbar.hidden && !selectionToolbar.contains(e.target) && !reader.contains(e.target)) {
    selectionToolbar.hidden = true;
  }
});

$("#analyze").addEventListener("click", async () => {
  if (!state.selection) return;
  try {
    await submitInteraction("text_selected", {
      anchorId: state.anchorId,
      paragraphId: state.selection.startParagraphId,
      selection: state.selection,
    });
  } catch (error) {
    statusNode.textContent = error.message || "分析失败";
  }
});

$("#question-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("#question");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  try {
    await submitInteraction("question_submitted", {question, anchorId: state.anchorId});
  } catch (error) {
    statusNode.textContent = error.message || "提问失败";
  }
});

function navigateArticle(direction) {
  if (!state.articles.length || !state.article) return;
  const currentIndex = state.articles.findIndex((item) => item.articleId === state.article.articleId);
  const nextIndex = currentIndex + direction;
  if (nextIndex < 0 || nextIndex >= state.articles.length) return;
  const select = $("#article-select");
  select.value = articleOptionValue(state.articles[nextIndex]);
  loadArticle(state.articles[nextIndex]).catch((error) => {
    statusNode.textContent = error.message || "切换文章失败";
  });
}

$("#prev-article").addEventListener("click", () => navigateArticle(-1));
$("#next-article").addEventListener("click", () => navigateArticle(1));

init().catch((error) => {
  console.error(error);
  markFailed(error.message || "初始化失败");
});
