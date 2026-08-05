export const HISTORY_KEY = "thorax-analysis-history-v1";
export const MAX_HISTORY_ITEMS = 10;

export function readHistory(storage = globalThis.localStorage) {
  try {
    const parsed = JSON.parse(storage.getItem(HISTORY_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.slice(0, MAX_HISTORY_ITEMS) : [];
  } catch {
    return [];
  }
}

export function writeHistory(entries, storage = globalThis.localStorage) {
  const limited = entries.slice(0, MAX_HISTORY_ITEMS);
  storage.setItem(HISTORY_KEY, JSON.stringify(limited));
  return limited;
}

export function addHistoryEntry(entry, storage = globalThis.localStorage) {
  const entries = readHistory(storage).filter((item) => item.id !== entry.id);
  return writeHistory([entry, ...entries], storage);
}

export function clearHistory(storage = globalThis.localStorage) {
  storage.removeItem(HISTORY_KEY);
}

export function createEducationalReport(entry) {
  return {
    schema: "thorax.educational-report.v1",
    generated_at: new Date().toISOString(),
    model: "densenet121-res224-all",
    analysis: {
      timestamp: entry.timestamp,
      filename: entry.filename,
      target_pathology: entry.targetPathology,
      top_predictions: entry.topPredictions,
      input_quality: entry.quality,
      image_metadata: entry.imageMetadata,
      explainability: entry.explainability,
    },
    disclaimer:
      "Relatório educacional. Não representa diagnóstico nem laudo radiológico.",
  };
}

function csvEscape(value) {
  const text = String(value ?? "");
  if (/[",\n]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

export function predictionsToCsv(entry) {
  const rows = [
    ["filename", "timestamp", "pathology", "probability", "threshold_band"],
  ];
  for (const prediction of entry.topPredictions || []) {
    rows.push([
      entry.filename || "",
      entry.timestamp || "",
      prediction.pathology || "",
      prediction.probability ?? prediction.prob ?? "",
      prediction.threshold_band || prediction.thresholdBand || "",
    ]);
  }
  return rows.map((row) => row.map(csvEscape).join(",")).join("\n");
}
