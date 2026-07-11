import { findStudy, studies } from "./data.js";
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
let selectedStudyId = studies[0].id;
let viewerState = { ...DEFAULT_VIEW };
let studyMode = false;
let studyRevealed = false;

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

function renderButtons(activeId) {
  buttonsContainer.innerHTML = studies
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
    .join("");
}

function renderStudy(id, animate = true) {
  const study = findStudy(id);
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

buttonsContainer.addEventListener("click", (event) => {
  const button = event.target.closest("[data-study]");
  if (button) {
    studyRevealed = false;
    renderStudy(button.dataset.study);
  }
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
  const study = findStudy(selectedStudyId);
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

async function analyzeFile(file, targetPathology = null) {
  currentAnalysisFile = file;
  const formData = new FormData();
  formData.append("file", file);
  if (targetPathology) formData.append("target_pathology", targetPathology);
  status.textContent = targetPathology
    ? `Gerando explicação para ${targetPathology}…`
    : `Analisando ${file.name}… a primeira execução pode baixar o modelo.`;
  actionButtons.forEach((button) => {
    button.disabled = true;
  });

  try {
    const response = await fetch("/analyze", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail ?? `HTTP ${response.status}`);
    renderAnalysis(payload);
    status.textContent = "Análise concluída.";
  } catch (error) {
    status.textContent = `Não foi possível analisar: ${error.message}`;
  } finally {
    actionButtons.forEach((button) => {
      button.disabled = false;
    });
  }
}

function renderAnalysis(data) {
  latestAnalysis = data;
  document.querySelector("#result-original").src = data.image_original;
  document.querySelector("#result-overlay").src = data.image_overlay;
  document.querySelector("#result-overlay").style.opacity =
    Number(document.querySelector("#overlay-opacity").value) / 100;
  renderQuality(data.input_quality);
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
      const threshold =
        prediction.op_threshold == null
          ? ""
          : `<span class="prediction-threshold" style="left:${prediction.op_threshold * 100}%"></span>`;
      return `
        <button
          type="button"
          class="prediction-row ${prediction.in_pneumonia_group ? "group" : ""} ${prediction.pathology === data.target_pathology ? "selected" : ""}"
          data-pathology="${prediction.pathology}"
          aria-pressed="${prediction.pathology === data.target_pathology}"
        >
          <span>${prediction.pathology}</span>
          <span class="prediction-track">
            <span class="prediction-fill" style="width:${percent}%"></span>
            ${threshold}
          </span>
          <span class="prediction-value">${percent}%${prediction.above_threshold ? " ↑" : ""}</span>
        </button>
      `;
    })
    .join("");
  document.querySelector("#result-disclaimer").textContent =
    data.explainability?.note ?? data.disclaimer;
  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderQuality(quality) {
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
  `;
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
  const study = findStudy(selectedStudyId);
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

const comparisonStudies = studies.filter((study) => study.id !== "anatomy");
const comparisonA = document.querySelector("#comparison-a");
const comparisonB = document.querySelector("#comparison-b");
const comparisonOptions = comparisonStudies
  .map((study) => `<option value="${study.id}">${study.title}</option>`)
  .join("");
comparisonA.innerHTML = comparisonOptions;
comparisonB.innerHTML = comparisonOptions;
comparisonB.value = comparisonStudies.find((study) => study.id === "lobar-pneumonia")?.id
  ?? comparisonStudies[1].id;

document.querySelector("#run-comparison").addEventListener("click", async () => {
  const button = document.querySelector("#run-comparison");
  const comparisonStatus = document.querySelector("#comparison-status");
  const studyA = findStudy(comparisonA.value);
  const studyB = findStudy(comparisonB.value);

  if (studyA.id === studyB.id) {
    comparisonStatus.textContent = "Escolha duas imagens diferentes.";
    return;
  }

  button.disabled = true;
  comparisonStatus.textContent = "Comparando respostas do modelo…";
  try {
    const [fileA, fileB] = await Promise.all([
      studyToFile(studyA),
      studyToFile(studyB),
    ]);
    const formData = new FormData();
    formData.append("file_a", fileA);
    formData.append("file_b", fileB);
    const response = await fetch("/compare", { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail ?? `HTTP ${response.status}`);
    renderComparison(payload, studyA, studyB);
    comparisonStatus.textContent = "Comparação concluída.";
  } catch (error) {
    comparisonStatus.textContent = `Não foi possível comparar: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});

function renderComparison(data, studyA, studyB) {
  document.querySelector("#comparison-image-a").src = data.image_a;
  document.querySelector("#comparison-image-b").src = data.image_b;
  document.querySelector("#comparison-caption-a").textContent =
    `${studyA.title} · qualidade ${data.quality_a.score}/100`;
  document.querySelector("#comparison-caption-b").textContent =
    `${studyB.title} · qualidade ${data.quality_b.score}/100`;
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

renderStudy(studies[0].id, false);
