import assert from "node:assert/strict";
import test from "node:test";

import {
  addHistoryEntry,
  clearHistory,
  createEducationalReport,
  entryFromAnalysis,
  MAX_HISTORY_ITEMS,
  predictionsToCsv,
  readHistory,
} from "../history.js";

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

test("o histórico mantém as entradas mais recentes dentro do limite", () => {
  const storage = memoryStorage();
  for (let index = 0; index < MAX_HISTORY_ITEMS + 3; index += 1) {
    addHistoryEntry({ id: String(index) }, storage);
  }

  const entries = readHistory(storage);
  assert.equal(entries.length, MAX_HISTORY_ITEMS);
  assert.equal(entries[0].id, String(MAX_HISTORY_ITEMS + 2));
});

test("o histórico pode ser apagado sem afetar outros dados", () => {
  const storage = memoryStorage();
  addHistoryEntry({ id: "one" }, storage);
  clearHistory(storage);
  assert.deepEqual(readHistory(storage), []);
});

test("o relatório educacional possui schema e aviso explícitos", () => {
  const report = createEducationalReport({
    timestamp: "2026-01-01T00:00:00.000Z",
    filename: "study.jpg",
    targetPathology: "Effusion",
    topPredictions: [],
    quality: { score: 90 },
    explainability: { target_pathology: "Effusion" },
  });

  assert.equal(report.schema, "thorax.educational-report.v1");
  assert.equal(report.analysis.target_pathology, "Effusion");
  assert.match(report.disclaimer, /Não representa diagnóstico/);
});

test("a exportação CSV inclui cabeçalho e linhas de predição", () => {
  const csv = predictionsToCsv({
    filename: "study.jpg",
    timestamp: "2026-01-01T00:00:00.000Z",
    topPredictions: [
      { pathology: "Effusion", probability: 0.81, threshold_band: "above" },
    ],
  });
  assert.match(csv, /^filename,timestamp,pathology/);
  assert.match(csv, /study\.jpg/);
  assert.match(csv, /Effusion,0\.81,above/);
});

test("entryFromAnalysis persiste threshold_band e snapshot reabrível", () => {
  const entry = entryFromAnalysis(
    {
      target_pathology: "Effusion",
      predictions: [
        {
          pathology: "Effusion",
          prob: 0.81,
          above_threshold: true,
          threshold_band: "above",
          threshold_margin: 0.2,
          ambiguity: 0.1,
        },
      ],
      input_quality: { score: 90 },
      radiograph_quality: { exposure: { label: "adequada" } },
      image_metadata: { format: "PNG" },
      explainability: { target_pathology: "Effusion" },
      prediction_stability: { stability_label: "estável", mean_std: 0.01 },
      image_original: "data:image/png;base64,aaa",
      image_overlay: "data:image/png;base64,bbb",
      decision_context: { borderline_classes: [] },
      timings: { total_ms: 10 },
      disclaimer: "educacional",
    },
    { filename: "study.jpg", systematicReview: { checklist: ["A"] } },
  );
  assert.equal(entry.topPredictions[0].threshold_band, "above");
  assert.equal(entry.predictionStability.stability_label, "estável");
  assert.equal(entry.systematicReview.checklist[0], "A");
  assert.equal(entry.snapshot.target_pathology, "Effusion");
  const csv = predictionsToCsv(entry);
  assert.match(csv, /Effusion,0\.81,above/);
});
