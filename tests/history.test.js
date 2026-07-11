import assert from "node:assert/strict";
import test from "node:test";

import {
  addHistoryEntry,
  clearHistory,
  createEducationalReport,
  MAX_HISTORY_ITEMS,
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
