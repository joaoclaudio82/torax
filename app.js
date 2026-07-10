import { findStudy, studies } from "./data.js";

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
          <span class="study-arrow" aria-hidden="true">→</span>
        </button>
      `,
    )
    .join("");
}

function renderStudy(id, animate = true) {
  const study = findStudy(id);

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
      renderButtons(study.id);
      image.classList.remove("changing");
    },
    animate ? 160 : 0,
  );
}

buttonsContainer.addEventListener("click", (event) => {
  const button = event.target.closest("[data-study]");
  if (button) renderStudy(button.dataset.study);
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

const dropZone = document.querySelector("#drop-zone");
const fileInput = document.querySelector("#analysis-file");
const status = document.querySelector("#analysis-status");
const results = document.querySelector("#analysis-results");
const actionButtons = document.querySelectorAll(".analysis-actions button");

async function analyzeFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  status.textContent = `Analisando ${file.name}… a primeira execução pode baixar o modelo.`;
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
  document.querySelector("#result-original").src = data.image_original;
  document.querySelector("#result-overlay").src = data.image_overlay;
  const target = data.predictions.find(
    (prediction) => prediction.pathology === data.target_pathology,
  );
  document.querySelector("#target-result").innerHTML =
    `Alvo do mapa: <strong>${data.target_pathology}</strong> · ` +
    `${(target.prob * 100).toFixed(1)}% de probabilidade do modelo`;
  document.querySelector("#prediction-bars").innerHTML = data.predictions
    .slice(0, 10)
    .map((prediction) => {
      const percent = (prediction.prob * 100).toFixed(1);
      const threshold =
        prediction.op_threshold == null
          ? ""
          : `<span class="prediction-threshold" style="left:${prediction.op_threshold * 100}%"></span>`;
      return `
        <div class="prediction-row ${prediction.in_pneumonia_group ? "group" : ""}">
          <span>${prediction.pathology}</span>
          <span class="prediction-track">
            <span class="prediction-fill" style="width:${percent}%"></span>
            ${threshold}
          </span>
          <span class="prediction-value">${percent}%</span>
        </div>
      `;
    })
    .join("");
  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

document.querySelector("#pick-file").addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) analyzeFile(fileInput.files[0]);
});

document.querySelector("#use-sample").addEventListener("click", async () => {
  status.textContent = "Preparando a imagem do acervo…";
  const response = await fetch(studies[0].image);
  const file = new File([await response.blob()], "radiografia-pa.jpg", {
    type: "image/jpeg",
  });
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

renderStudy(studies[0].id, false);
