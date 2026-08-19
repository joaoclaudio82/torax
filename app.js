import { mergeNihStudies, studies } from "./data.js";
import { glossaryEntry } from "./glossary.js";
import {
  addHistoryEntry,
  clearHistory,
  createEducationalReport,
  entryFromAnalysis,
  predictionsToCsv,
  readHistory,
} from "./history.js";
import { createImageFilter, DEFAULT_VIEW, normalizeView } from "./viewer.js";

const buttonsContainer = document.querySelector("#study-buttons");
const image = document.querySelector("#study-image");
const title = document.querySelector("#study-title");
const subtitle = document.querySelector("#study-subtitle");
const badge = document.querySelector("#study-badge");
const description = document.querySelector("#study-description");
const observations = document.querySelector("#study-observations");
const source = document.querySelector("#study-source");
const license = document.querySelector("#study-license");
const dialog = document.querySelector("#image-dialog");
const dialogImage = document.querySelector("#dialog-image");
let catalogStudies = [...studies];
let selectedStudyId = catalogStudies[0].id;
let viewerState = { ...DEFAULT_VIEW };
let studyMode = false;
let studyRevealed = false;
let activeJobId = null;
let pollAbort = null;

function currentStudy(id = selectedStudyId) {
  return catalogStudies.find((study) => study.id === id) ?? catalogStudies[0];
}

function updateNihBanner(manifest) {
  const banner = document.querySelector("#nih-pack-banner");
  if (!banner) return;
  if (manifest?.available) {
    banner.hidden = true;
    banner.innerHTML = "";
    return;
  }
  banner.hidden = false;
  banner.innerHTML = `
    <strong>Pack NIH não carregado.</strong>
    <span>${escapeHtml(manifest?.message || "Baixe as radiografias reais para o atlas de teste.")}</span>
    <code>${escapeHtml(manifest?.download_command || "npm run download:nih-demo")}</code>
  `;
}

async function loadNihCatalog() {
  try {
    const response = await fetch("/api/nih-manifest");
    const manifest = await response.json();
    if (!response.ok) throw new Error(manifest.detail || `HTTP ${response.status}`);
    catalogStudies = mergeNihStudies(studies, manifest.images || []);
    updateNihBanner(manifest);
  } catch {
    catalogStudies = [...studies];
    updateNihBanner({
      available: false,
      message: "Não foi possível consultar o manifesto NIH.",
      download_command: "npm run download:nih-demo",
    });
  }
  document.querySelector("#image-count").textContent = String(catalogStudies.length);
  if (!catalogStudies.some((study) => study.id === selectedStudyId)) {
    selectedStudyId = catalogStudies[0].id;
  }
  populateComparisonSelects();
  renderButtons(selectedStudyId);
}

async function initOperationalStatus() {
  document.querySelector("#image-count").textContent = catalogStudies.length;
  document.querySelector("#study-count").textContent = catalogStudies.length;
  const modelStatus = document.querySelector("#model-status");

  try {
    const response = await fetch("/health");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const health = await response.json();
    document.querySelector("#class-count").textContent = health.pathologies;
    document.querySelector("#model-name").textContent = "DenseNet-121";
    const versionBadge = document.querySelector("#api-version");
    if (versionBadge && health.api_version) {
      versionBadge.textContent = `v${health.api_version}`;
    }
    modelStatus.querySelector("span").textContent =
      `Modelo disponível · ${health.pathologies} classes`;
    modelStatus.classList.remove("error");
    modelStatus.classList.add("ready");
  } catch {
    document.querySelector("#class-count").textContent = "—";
    document.querySelector("#model-name").textContent = "Indisponível";
    modelStatus.querySelector("span").textContent = "Modelo indisponível";
    modelStatus.classList.add("error");
  }
  await loadNihCatalog();
}

function applyViewerState() {
  viewerState = normalizeView(viewerState);
  const filter = createImageFilter(viewerState);
  image.style.filter = filter;
  dialogImage.style.filter = filter;
  document.querySelector("#brightness-control").value = viewerState.brightness;
  document.querySelector("#contrast-control").value = viewerState.contrast;
  document.querySelector("#brightness-value").textContent =
    `${viewerState.brightness}%`;
  document.querySelector("#contrast-value").textContent =
    `${viewerState.contrast}%`;
  const invertButton = document.querySelector("#invert-control");
  invertButton.setAttribute("aria-pressed", String(viewerState.inverted));
  invertButton.classList.toggle("active", viewerState.inverted);
}

function resetViewer() {
  viewerState = { ...DEFAULT_VIEW };
  applyViewerState();
}

function filteredStudies() {
  const query = (document.querySelector("#study-filter")?.value || "")
    .trim()
    .toLowerCase();
  if (!query) return catalogStudies;
  return catalogStudies.filter((study) => {
    const haystack = [
      study.title,
      study.subtitle,
      study.badge,
      ...(study.learningTags || []),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });
}

function renderButtons(activeId) {
  const visible = filteredStudies();
  document.querySelector("#study-count").textContent = String(visible.length);
  buttonsContainer.innerHTML = visible.length
    ? visible
        .map(
          (study, index) => `
        <button
          class="study-button ${study.id === activeId ? "active" : ""}"
          type="button"
          data-study="${study.id}"
          aria-pressed="${study.id === activeId}"
        >
          <span class="study-number">${String(index + 1).padStart(2, "0")}</span>
          <span>
            <strong>${study.title}</strong>
            <small>${study.subtitle}</small>
          </span>
        </button>
      `,
        )
        .join("")
    : `<p class="empty-filter">Nenhuma imagem corresponde ao filtro.</p>`;
}

function renderStudy(id, animate = true) {
  const study = currentStudy(id);
  selectedStudyId = study.id;
  resetViewer();

  if (animate) image.classList.add("changing");

  window.setTimeout(
    () => {
      image.src = study.image;
      image.alt = study.alt;
      title.textContent = study.title;
      subtitle.textContent = study.subtitle;
      badge.textContent = study.badge;
      description.textContent = study.description;
      source.href = study.source;
      license.textContent = study.license;
      observations.innerHTML = study.observations
        .map((observation) => `<li>${observation}</li>`)
        .join("");
      document.querySelector("#use-sample").textContent =
        `Analisar: ${study.title}`;
      applyStudyMode(study);
      renderButtons(study.id);
      image.classList.remove("changing");
    },
    animate ? 160 : 0,
  );
}

document.querySelector("#study-filter")?.addEventListener("input", () => {
  renderButtons(selectedStudyId);
});

buttonsContainer.addEventListener("click", (event) => {
  const button = event.target.closest("[data-study]");
  if (button) {
    studyRevealed = false;
    renderStudy(button.dataset.study);
  }
});

buttonsContainer.addEventListener("keydown", (event) => {
  if (!["ArrowDown", "ArrowUp"].includes(event.key)) return;
  const buttons = [...buttonsContainer.querySelectorAll("[data-study]")];
  const currentIndex = buttons.indexOf(document.activeElement);
  if (currentIndex < 0) return;
  event.preventDefault();
  const direction = event.key === "ArrowDown" ? 1 : -1;
  const nextIndex = (currentIndex + direction + buttons.length) % buttons.length;
  const nextId = buttons[nextIndex].dataset.study;
  studyRevealed = false;
  renderStudy(nextId);
  window.setTimeout(() => {
    buttonsContainer.querySelector(`[data-study="${nextId}"]`)?.focus();
  }, 180);
});

function applyStudyMode(study) {
  const toggle = document.querySelector("#study-mode-toggle");
  const panel = document.querySelector("#study-mode-panel");
  toggle.setAttribute("aria-pressed", String(studyMode));
  toggle.classList.toggle("active", studyMode);
  panel.hidden = !studyMode;

  if (!studyMode) return;
  if (!studyRevealed) {
    document.querySelector("#study-feedback").textContent = "";
    title.textContent = "Qual é o principal padrão?";
    subtitle.textContent = "Caso sem identificação";
    badge.textContent = "Modo estudo";
    description.textContent =
      "Observe a radiografia, registre sua hipótese e depois revele a referência.";
    observations.innerHTML = "";
  }
}

const studyHypotheses = [
  "Normal",
  "Pneumonia",
  "Consolidation",
  "Pneumothorax",
  "Effusion",
  "Edema",
  "Lung Opacity",
  "Anatomia",
];
document.querySelector("#study-hypothesis").innerHTML = studyHypotheses
  .map((hypothesis) => `<option value="${hypothesis}">${hypothesis}</option>`)
  .join("");

document.querySelector("#study-mode-toggle").addEventListener("click", () => {
  studyMode = !studyMode;
  studyRevealed = false;
  renderStudy(selectedStudyId, false);
});

document.querySelector("#reveal-study").addEventListener("click", () => {
  const study = currentStudy(selectedStudyId);
  const hypothesis = document.querySelector("#study-hypothesis").value;
  const matched = study.learningTags.includes(hypothesis);
  studyRevealed = true;
  renderStudy(study.id, false);
  document.querySelector("#study-feedback").textContent = matched
    ? `Hipótese compatível com a referência: ${study.learningTags.join(", ")}.`
    : `Referência educacional: ${study.learningTags.join(", ")}. Compare com sua hipótese (${hypothesis}).`;
});

document.querySelector("#zoom-button").addEventListener("click", () => {
  dialogImage.src = image.src;
  dialogImage.alt = image.alt;
  dialog.showModal();
});

document.querySelector("#close-dialog").addEventListener("click", () => {
  dialog.close();
});

dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});

document.querySelector("#brightness-control").addEventListener("input", (event) => {
  viewerState.brightness = Number(event.target.value);
  applyViewerState();
});

document.querySelector("#contrast-control").addEventListener("input", (event) => {
  viewerState.contrast = Number(event.target.value);
  applyViewerState();
});

document.querySelector("#invert-control").addEventListener("click", () => {
  viewerState.inverted = !viewerState.inverted;
  applyViewerState();
});

document.querySelector("#reset-viewer").addEventListener("click", resetViewer);

const dropZone = document.querySelector("#drop-zone");
const fileInput = document.querySelector("#analysis-file");
const status = document.querySelector("#analysis-status");
const results = document.querySelector("#analysis-results");
const actionButtons = document.querySelectorAll(".analysis-actions button");
let currentAnalysisFile = null;
let latestAnalysis = null;

async function cancelActiveJob() {
  if (pollAbort) {
    pollAbort.abort();
    pollAbort = null;
  }
  if (activeJobId) {
    const jobId = activeJobId;
    activeJobId = null;
    try {
      await fetch(`/jobs/${jobId}/cancel`, { method: "POST" });
    } catch {
      // ignore cancel errors
    }
  }
}

async function pollJob(jobId) {
  const stageLabels = {
    queued: "Na fila",
    starting: "Iniciando",
    preprocessing: "Pré-processando",
    inference: "Inferência",
    "inference-cache": "Inferência (cache)",
    gradcam: "Grad-CAM",
    stability: "Estabilidade",
    finalizing: "Finalizando",
    cache: "Cache",
    done: "Concluído",
    error: "Erro",
    cancelled: "Cancelado",
  };
  pollAbort = new AbortController();
  activeJobId = jobId;
  try {
    for (let attempt = 0; attempt < 120; attempt += 1) {
      const response = await fetch(`/jobs/${jobId}`, {
        signal: pollAbort.signal,
      });
      const job = await response.json();
      if (!response.ok) throw new Error(job.detail ?? `HTTP ${response.status}`);
      const pct = Math.round((job.progress || 0) * 100);
      const stage = stageLabels[job.stage] || job.stage;
      status.textContent = `${stage}… ${pct}%`;
      updateProgressBar(job.progress || 0, stage);
      if (job.status === "completed") return job.result;
      if (job.status === "failed") throw new Error(job.error || "Falha no job.");
      if (job.status === "cancelled") throw new Error("Análise cancelada.");
      await new Promise((resolve) => setTimeout(resolve, 400));
    }
    throw new Error("Tempo esgotado aguardando a análise.");
  } finally {
    if (activeJobId === jobId) activeJobId = null;
  }
}

function updateProgressBar(progress, stage) {
  const wrap = document.querySelector("#analysis-progress");
  const bar = document.querySelector("#analysis-progress-bar");
  if (!wrap || !bar) return;
  wrap.hidden = false;
  bar.style.width = `${Math.max(4, Math.round(progress * 100))}%`;
  wrap.setAttribute("aria-valuenow", String(Math.round(progress * 100)));
  wrap.dataset.stage = stage || "";
}

async function analyzeFile(file, targetPathology = null) {
  await cancelActiveJob();
  currentAnalysisFile = file;
  const formData = new FormData();
  formData.append("file", file);
  if (targetPathology) formData.append("target_pathology", targetPathology);
  const estimateStability = document.querySelector("#estimate-stability")?.checked;
  if (estimateStability) formData.append("estimate_stability", "true");
  status.textContent = targetPathology
    ? `Gerando explicação para ${targetPathology}…`
    : `Analisando ${file.name}… a primeira execução pode baixar o modelo.`;
  actionButtons.forEach((button) => {
    button.disabled = true;
  });
  updateProgressBar(0.05, "starting");

  try {
    let payload;
    if (targetPathology && latestAnalysis) {
      const response = await fetch("/analyze/gradcam", {
        method: "POST",
        body: formData,
      });
      payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? `HTTP ${response.status}`);
      updateProgressBar(1, "done");
      renderAnalysis(payload, { saveToHistory: false });
      status.textContent = "Mapa Grad-CAM atualizado.";
      return;
    }

    const useAsync = document.querySelector("#use-async-analyze")?.checked;
    if (useAsync) {
      const started = await fetch("/analyze/async", {
        method: "POST",
        body: formData,
      });
      const jobInfo = await started.json();
      if (!started.ok) throw new Error(jobInfo.detail ?? `HTTP ${started.status}`);
      payload = await pollJob(jobInfo.job_id);
    } else {
      const response = await fetch("/analyze", { method: "POST", body: formData });
      payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? `HTTP ${response.status}`);
      updateProgressBar(1, "done");
    }
    renderAnalysis(payload, { saveToHistory: !targetPathology });
    status.textContent = payload.cache?.hit
      ? "Análise concluída (cache)."
      : "Análise concluída.";
  } catch (error) {
    if (error.name === "AbortError") {
      status.textContent = "Análise cancelada.";
    } else {
      status.textContent = `Não foi possível analisar: ${error.message}`;
    }
  } finally {
    actionButtons.forEach((button) => {
      button.disabled = false;
    });
    const wrap = document.querySelector("#analysis-progress");
    if (wrap) wrap.hidden = true;
  }
}

function renderAnalysis(data, { saveToHistory = false } = {}) {
  latestAnalysis = data;
  document.querySelector("#result-original").src = data.image_original;
  document.querySelector("#result-overlay").src = data.image_overlay;
  document.querySelector("#result-overlay").style.opacity =
    Number(document.querySelector("#overlay-opacity").value) / 100;
  renderQuality(data.input_quality, data.image_metadata);
  renderRadiographQuality(data.radiograph_quality);
  renderStability(data.prediction_stability);
  renderDecisionContext(data.decision_context);
  renderPerformance(data.timings);
  const target = data.predictions.find(
    (prediction) => prediction.pathology === data.target_pathology,
  );
  const camStats = data.explainability?.cam_stats;
  document.querySelector("#target-result").innerHTML =
    `Alvo do mapa: <strong>${data.target_pathology}</strong> · ` +
    `${(target.prob * 100).toFixed(1)}% · atenção ${camStats?.visual_region ?? "não calculada"}`;
  document.querySelector("#prediction-bars").innerHTML = data.predictions
    .slice(0, 10)
    .map((prediction) => {
      const percent = (prediction.prob * 100).toFixed(1);
      const entry = glossaryEntry(prediction.pathology);
      const threshold =
        prediction.op_threshold == null
          ? ""
          : `<span class="prediction-threshold" style="left:${prediction.op_threshold * 100}%"></span>`;
      return `
        <button
          type="button"
          class="prediction-row ${prediction.in_pneumonia_group ? "group" : ""} ${prediction.threshold_band ?? ""} ${prediction.pathology === data.target_pathology ? "selected" : ""}"
          data-pathology="${prediction.pathology}"
          title="${entry.title}: ${entry.summary}"
          aria-pressed="${prediction.pathology === data.target_pathology}"
        >
          <span>${entry.title}</span>
          <span class="prediction-track">
            <span class="prediction-fill" style="width:${percent}%"></span>
            ${threshold}
          </span>
          <span class="prediction-value">${percent}%${prediction.threshold_band === "borderline" ? " ≈" : prediction.above_threshold ? " ↑" : ""}</span>
        </button>
      `;
    })
    .join("");
  document.querySelector("#result-disclaimer").textContent =
    data.explainability?.note ?? data.disclaimer;
  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "nearest" });
  if (saveToHistory) saveAnalysisToHistory(data);
}

function renderQuality(quality, metadata = null) {
  const panel = document.querySelector("#quality-panel");
  if (!quality) {
    panel.hidden = true;
    return;
  }

  const levelLabels = {
    good: "Boa",
    adequate: "Adequada",
    attention: "Requer atenção",
    insufficient: "Insuficiente",
  };
  const warnings = quality.warnings.length
    ? `<ul>${quality.warnings.map((warning) => `<li>${warning}</li>`).join("")}</ul>`
    : "<p>Nenhum alerta heurístico identificado.</p>";
  const metrics = quality.metrics;
  const dicomMetadata = metadata?.format === "DICOM"
    ? `
      <div class="dicom-metadata">
        <span>DICOM técnico</span>
        <strong>${metadata.view_position || "Posição não informada"} · ${metadata.photometric_interpretation}</strong>
        <small>${metadata.window_applied ? `Window ${metadata.window_center}/${metadata.window_width} aplicado` : "Window não informado"}</small>
      </div>
    `
    : "";

  panel.hidden = false;
  panel.innerHTML = `
    <div class="quality-score quality-${quality.level}">
      <strong>${quality.score}</strong><span>/ 100</span>
    </div>
    <div class="quality-summary">
      <div><strong>Qualidade de entrada: ${levelLabels[quality.level]}</strong></div>
      ${warnings}
    </div>
    <dl class="quality-metrics">
      <div><dt>Dimensões</dt><dd>${metrics.width ?? "—"} × ${metrics.height ?? "—"}</dd></div>
      <div><dt>Contraste</dt><dd>${metrics.contrast ?? "—"}</dd></div>
      <div><dt>Proporção</dt><dd>${metrics.aspect_ratio ?? "—"}</dd></div>
    </dl>
    ${dicomMetadata}
  `;
}

function renderRadiographQuality(report) {
  const panel = document.querySelector("#radiograph-qc-panel");
  if (!report) {
    panel.hidden = true;
    return;
  }
  const flags = report.flags?.length
    ? `<ul>${report.flags.map((flag) => `<li>${flag}</li>`).join("")}</ul>`
    : "<p>Nenhum alerta de posicionamento/exposição destacado.</p>";
  panel.hidden = false;
  panel.innerHTML = `
    <div>
      <span class="section-label">QC radiográfico (educacional)</span>
      <strong>Exposição: ${report.exposure.label}</strong>
      <p>${report.exposure.tip}</p>
    </div>
    <dl class="quality-metrics">
      <div><dt>Rotação</dt><dd>${report.rotation.label}</dd></div>
      <div><dt>Projeção</dt><dd>${report.projection_hint.label}</dd></div>
      <div><dt>Assimetria</dt><dd>${report.rotation.asymmetry_ratio}</dd></div>
    </dl>
    ${flags}
    <p class="panel-note">${report.disclaimer}</p>
  `;
}

function renderStability(report) {
  const panel = document.querySelector("#stability-panel");
  if (!report) {
    panel.hidden = true;
    return;
  }
  const rows = report.most_variable
    .map(
      (item) =>
        `<li><strong>${item.pathology}</strong> · σ=${item.std} · média=${(item.mean * 100).toFixed(1)}%</li>`,
    )
    .join("");
  panel.hidden = false;
  panel.innerHTML = `
    <div>
      <span class="section-label">Estabilidade da saída</span>
      <strong>${report.stability_label}</strong>
      <p>σ média = ${report.mean_std} · ${report.samples} amostras TTA</p>
    </div>
    <ul>${rows}</ul>
    <p class="panel-note">${report.note}</p>
  `;
}

function renderDecisionContext(context) {
  const panel = document.querySelector("#decision-panel");
  if (!context) {
    panel.hidden = true;
    return;
  }
  const borderline = context.borderline_classes;
  panel.hidden = false;
  panel.innerHTML = `
    <div>
      <span class="section-label">Contexto da decisão</span>
      <strong>${borderline.length} classe(s) próxima(s) do limiar</strong>
      <p>${borderline.length ? borderline.join(", ") : "Nenhuma classe na faixa limítrofe."}</p>
    </div>
    <div>
      <span>Separação entre as duas maiores probabilidades</span>
      <strong>${(context.top_probability_gap * 100).toFixed(1)} pp</strong>
    </div>
    <p>${context.note}</p>
  `;
}

function renderPerformance(timings) {
  const panel = document.querySelector("#performance-panel");
  if (!timings) {
    panel.hidden = true;
    return;
  }
  const stabilityRow =
    timings.stability_ms > 0
      ? `<div><dt>Estabilidade (TTA)</dt><dd>${timings.stability_ms} ms</dd></div>`
      : "";
  panel.hidden = false;
  panel.innerHTML = `
    <span>Tempo de processamento</span>
    <dl>
      <div><dt>Pré-processamento</dt><dd>${timings.preprocessing_ms ?? "—"} ms</dd></div>
      <div><dt>Inferência</dt><dd>${timings.inference_ms ?? "—"} ms</dd></div>
      <div><dt>Grad-CAM</dt><dd>${timings.gradcam_ms ?? "—"} ms</dd></div>
      ${stabilityRow}
      <div><dt>Total</dt><dd>${timings.total_ms ?? "—"} ms</dd></div>
    </dl>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function createThumbnail(dataUrl) {
  return new Promise((resolve) => {
    const source = new Image();
    source.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = 96;
      canvas.height = 96;
      const context = canvas.getContext("2d");
      context.fillStyle = "#111619";
      context.fillRect(0, 0, 96, 96);
      const scale = Math.min(96 / source.width, 96 / source.height);
      const width = source.width * scale;
      const height = source.height * scale;
      context.drawImage(source, (96 - width) / 2, (96 - height) / 2, width, height);
      resolve(canvas.toDataURL("image/jpeg", 0.65));
    };
    source.onerror = () => resolve("");
    source.src = dataUrl;
  });
}

function readSystematicReview() {
  const checked = [
    ...document.querySelectorAll(".systematic-review input:checked"),
  ].map((input) => input.value);
  if (!checked.length) return null;
  return { checklist: checked, saved_at: new Date().toISOString() };
}

async function saveAnalysisToHistory(data) {
  const thumbnail = await createThumbnail(data.image_original);
  const entry = entryFromAnalysis(data, {
    filename: currentAnalysisFile?.name ?? "imagem-sem-nome",
    thumbnail,
    systematicReview: readSystematicReview(),
  });
  addHistoryEntry(entry);
  renderHistory(entry.id);
}

function renderHistory(selectedId = null) {
  const entries = readHistory();
  const list = document.querySelector("#history-list");
  document.querySelector("#export-latest").disabled = entries.length === 0;
  document.querySelector("#export-csv").disabled = entries.length === 0;

  if (!entries.length) {
    list.innerHTML = '<p class="history-empty">Nenhuma análise salva localmente.</p>';
    document.querySelector("#history-preview").innerHTML =
      "<p>Execute uma análise para criar o primeiro registro local.</p>";
    return;
  }

  list.innerHTML = entries
    .map(
      (entry) => `
        <button type="button" class="history-item" data-history-id="${entry.id}">
          ${entry.thumbnail ? `<img src="${entry.thumbnail}" alt="" />` : ""}
          <span>
            <strong>${escapeHtml(entry.filename)}</strong>
            <small>${escapeHtml(entry.targetPathology)} · ${new Date(entry.timestamp).toLocaleString("pt-BR")}</small>
          </span>
        </button>
      `,
    )
    .join("");
  renderHistoryPreview(
    entries.find((entry) => entry.id === selectedId) ?? entries[0],
  );
}

function renderHistoryPreview(entry) {
  const predictions = (entry.topPredictions || [])
    .map(
      (prediction) =>
        `<li><span>${escapeHtml(prediction.pathology)}</span><strong>${((prediction.probability ?? 0) * 100).toFixed(1)}%${prediction.threshold_band ? ` · ${escapeHtml(prediction.threshold_band)}` : ""}</strong></li>`,
    )
    .join("");
  const stability = entry.predictionStability?.stability_label
    ? `<p>Estabilidade: ${escapeHtml(entry.predictionStability.stability_label)}</p>`
    : "";
  const reopen = entry.snapshot
    ? `<button type="button" class="secondary-button" id="reopen-history" data-history-id="${entry.id}">Reabrir análise</button>`
    : "";
  document.querySelector("#history-preview").innerHTML = `
    <div class="history-preview-header">
      ${entry.thumbnail ? `<img src="${entry.thumbnail}" alt="" />` : ""}
      <div>
        <span class="section-label">Registro local</span>
        <h3>${escapeHtml(entry.filename)}</h3>
        <p>Alvo Grad-CAM: ${escapeHtml(entry.targetPathology)}</p>
        ${stability}
      </div>
    </div>
    <ul>${predictions}</ul>
    <p class="history-quality">Qualidade de entrada: ${entry.quality?.score ?? "—"}/100</p>
    ${reopen}
  `;
  document.querySelector("#reopen-history")?.addEventListener("click", () => {
    if (!entry.snapshot) return;
    renderAnalysis(entry.snapshot, { saveToHistory: false });
    status.textContent = `Análise reaberta do histórico: ${entry.filename}`;
    document.querySelector("#analisar")?.scrollIntoView({ behavior: "smooth" });
  });
}

async function studyToFile(study) {
  const response = await fetch(study.image);
  if (!response.ok) throw new Error(`Falha ao carregar ${study.title}.`);
  const blob = await response.blob();
  return new File([blob], study.image.split("/").at(-1), {
    type: blob.type || "application/octet-stream",
  });
}

document.querySelector("#pick-file").addEventListener("click", () => {
  fileInput.click();
});

document.querySelector("#overlay-opacity").addEventListener("input", (event) => {
  document.querySelector("#result-overlay").style.opacity =
    Number(event.target.value) / 100;
});

document.querySelector("#prediction-bars").addEventListener("click", (event) => {
  const row = event.target.closest("[data-pathology]");
  if (!row || !currentAnalysisFile || row.dataset.pathology === latestAnalysis?.target_pathology) {
    return;
  }
  analyzeFile(currentAnalysisFile, row.dataset.pathology);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) analyzeFile(fileInput.files[0]);
});

document.querySelector("#use-sample").addEventListener("click", async () => {
  const study = currentStudy(selectedStudyId);
  status.textContent = `Preparando ${study.title}…`;
  const file = await studyToFile(study);
  analyzeFile(file);
});

for (const eventName of ["dragenter", "dragover"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("drag");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("drag");
  });
}

dropZone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  if (file) analyzeFile(file);
});

document
  .querySelector("#save-systematic-review")
  .addEventListener("click", () => {
    const checked = [
      ...document.querySelectorAll(".systematic-review input:checked"),
    ].map((input) => input.value);
    const reviewStatus = document.querySelector("#systematic-review-status");
    if (!checked.length) {
      reviewStatus.textContent = "Marque ao menos uma etapa revisada.";
      return;
    }
    sessionStorage.setItem(
      "thorax-systematic-review",
      JSON.stringify({ checked, timestamp: new Date().toISOString() }),
    );
    reviewStatus.textContent =
      `${checked.length} etapa(s) registrada(s) somente nesta sessão.`;
  });

const comparisonA = document.querySelector("#comparison-a");
const comparisonB = document.querySelector("#comparison-b");

function populateComparisonSelects() {
  const comparisonStudies = catalogStudies.filter((study) => study.id !== "anatomy");
  const comparisonOptions = comparisonStudies
    .map((study) => `<option value="${study.id}">${study.title}</option>`)
    .join("");
  const previousA = comparisonA.value;
  const previousB = comparisonB.value;
  comparisonA.innerHTML =
    `<option value="__upload__">Arquivo enviado (A)</option>${comparisonOptions}`;
  comparisonB.innerHTML =
    `<option value="__upload__">Arquivo enviado (B)</option>${comparisonOptions}`;
  if ([...comparisonA.options].some((option) => option.value === previousA)) {
    comparisonA.value = previousA;
  }
  if ([...comparisonB.options].some((option) => option.value === previousB)) {
    comparisonB.value = previousB;
  } else {
    comparisonB.value =
      comparisonStudies.find((study) => study.id === "lobar-pneumonia")?.id
      ?? comparisonStudies[1]?.id
      ?? comparisonStudies[0]?.id;
  }
}

async function resolveComparisonFile(side) {
  const select = side === "a" ? comparisonA : comparisonB;
  const upload = document.querySelector(`#comparison-file-${side}`);
  if (select.value === "__upload__") {
    const file = upload?.files?.[0];
    if (!file) throw new Error(`Selecione o arquivo da imagem ${side.toUpperCase()}.`);
    return { file, label: file.name };
  }
  const study = currentStudy(select.value);
  return { file: await studyToFile(study), label: study.title };
}

populateComparisonSelects();

document.querySelector("#run-comparison").addEventListener("click", async () => {
  const button = document.querySelector("#run-comparison");
  const comparisonStatus = document.querySelector("#comparison-status");
  button.disabled = true;
  comparisonStatus.textContent = "Comparando respostas do modelo…";
  try {
    const [resolvedA, resolvedB] = await Promise.all([
      resolveComparisonFile("a"),
      resolveComparisonFile("b"),
    ]);
    const formData = new FormData();
    formData.append("file_a", resolvedA.file);
    formData.append("file_b", resolvedB.file);
    const response = await fetch("/compare", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail ?? `HTTP ${response.status}`);
    renderComparison(payload, resolvedA.label, resolvedB.label);
    comparisonStatus.textContent = "Comparação concluída.";
  } catch (error) {
    comparisonStatus.textContent = `Não foi possível comparar: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});

function renderComparison(data, labelA, labelB) {
  document.querySelector("#comparison-image-a").src = data.image_a;
  document.querySelector("#comparison-image-b").src = data.image_b;
  document.querySelector("#comparison-caption-a").textContent =
    `${labelA} · qualidade ${data.quality_a.score}/100`;
  document.querySelector("#comparison-caption-b").textContent =
    `${labelB} · qualidade ${data.quality_b.score}/100`;
  document.querySelector("#comparison-deltas").innerHTML = data.top_changes
    .map((item) => {
      const deltaPercent = item.delta * 100;
      const width = Math.min(50, Math.abs(deltaPercent));
      const direction = deltaPercent >= 0 ? "positive" : "negative";
      const sign = deltaPercent > 0 ? "+" : "";
      return `
        <div class="delta-row">
          <span>${item.pathology}</span>
          <span class="delta-track">
            <span class="delta-fill ${direction}" style="width:${width}%"></span>
          </span>
          <span class="delta-value">${sign}${deltaPercent.toFixed(1)} pp</span>
        </div>
      `;
    })
    .join("");
  document.querySelector("#comparison-disclaimer").textContent = data.disclaimer;
  document.querySelector("#comparison-results").hidden = false;
}

document.querySelector("#history-list").addEventListener("click", (event) => {
  const item = event.target.closest("[data-history-id]");
  if (!item) return;
  const entry = readHistory().find(
    (historyEntry) => historyEntry.id === item.dataset.historyId,
  );
  if (entry) renderHistoryPreview(entry);
});

document.querySelector("#clear-history").addEventListener("click", () => {
  clearHistory();
  renderHistory();
});

document.querySelector("#export-csv").addEventListener("click", () => {
  const [latest] = readHistory();
  if (!latest) return;
  const blob = new Blob([predictionsToCsv(latest)], {
    type: "text/csv;charset=utf-8",
  });
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(blob);
  anchor.download = `thorax-predicoes-${latest.id}.csv`;
  anchor.click();
  URL.revokeObjectURL(anchor.href);
});

document.querySelector("#export-latest").addEventListener("click", () => {
  const [latest] = readHistory();
  if (!latest) return;
  const report = createEducationalReport(latest);
  const blob = new Blob([JSON.stringify(report, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `thorax-relatorio-${latest.id}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
});

renderHistory();
initOperationalStatus();
renderStudy(studies[0].id, false);
