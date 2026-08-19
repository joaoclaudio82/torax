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
      radiograph_quality: entry.radiographQuality,
      image_metadata: entry.imageMetadata,
      explainability: entry.explainability,
      prediction_stability: entry.predictionStability,
      systematic_review: entry.systematicReview,
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
    [
      "filename",
      "timestamp",
      "pathology",
      "probability",
      "threshold_band",
      "threshold_margin",
      "ambiguity",
    ],
  ];
  for (const prediction of entry.topPredictions || []) {
    rows.push([
      entry.filename || "",
      entry.timestamp || "",
      prediction.pathology || "",
      prediction.probability ?? prediction.prob ?? "",
      prediction.threshold_band || prediction.thresholdBand || "",
      prediction.threshold_margin ?? prediction.thresholdMargin ?? "",
      prediction.ambiguity ?? "",
    ]);
  }
  if (entry.predictionStability?.stability_label) {
    rows.push([]);
    rows.push([
      "stability_label",
      entry.predictionStability.stability_label,
      "mean_std",
      entry.predictionStability.mean_std ?? "",
    ]);
  }
  return rows.map((row) => row.map(csvEscape).join(",")).join("\n");
}

export function entryFromAnalysis(data, {
  id,
  filename,
  thumbnail = "",
  systematicReview = null,
} = {}) {
  return {
    id: id || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    timestamp: new Date().toISOString(),
    filename: filename || "imagem-sem-nome",
    targetPathology: data.target_pathology,
    topPredictions: (data.predictions || []).slice(0, 10).map((prediction) => ({
      pathology: prediction.pathology,
      probability: prediction.prob,
      aboveThreshold: prediction.above_threshold,
      threshold_band: prediction.threshold_band,
      threshold_margin: prediction.threshold_margin,
      ambiguity: prediction.ambiguity,
    })),
    quality: data.input_quality,
    radiographQuality: data.radiograph_quality,
    imageMetadata: data.image_metadata,
    explainability: data.explainability,
    predictionStability: data.prediction_stability
      ? {
          stability_label: data.prediction_stability.stability_label,
          mean_std: data.prediction_stability.mean_std,
          samples: data.prediction_stability.samples,
        }
      : null,
    systematicReview,
    thumbnail,
    snapshot: {
      target_pathology: data.target_pathology,
      predictions: data.predictions,
      image_original: data.image_original,
      image_overlay: data.image_overlay,
      input_quality: data.input_quality,
      radiograph_quality: data.radiograph_quality,
      image_metadata: data.image_metadata,
      decision_context: data.decision_context,
      prediction_stability: data.prediction_stability,
      explainability: data.explainability,
      timings: data.timings,
      disclaimer: data.disclaimer,
    },
  };
}
