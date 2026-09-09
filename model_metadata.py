"""Metadados transparentes do modelo para clientes e documentação da API."""
from __future__ import annotations


MODEL_CARD_VERSION = "1.1"


def build_model_card(model, *, weights: str) -> dict:
    raw_pathologies = list(getattr(model, "pathologies", []) or [])
    pathologies = [item for item in raw_pathologies if item]
    thresholds = getattr(model, "op_threshs", None)
    thresholds_available = 0
    if thresholds is not None:
        for pathology, value in zip(raw_pathologies, thresholds):
            if not pathology:
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if numeric == numeric:
                thresholds_available += 1

    return {
        "model_card_version": MODEL_CARD_VERSION,
        "architecture": "DenseNet-121",
        "provider": "torchxrayvision",
        "weights": weights,
        "input_shape": [1, 1, 224, 224],
        "task": "multilabel chest radiograph classification",
        "pathologies": pathologies,
        "pathology_count": len(pathologies),
        "operating_thresholds_available": thresholds_available,
        "score_semantics": {
            "legacy_api_field": "prob",
            "recommended_name": "model_score",
            "type": "operating-point-normalized model score",
            "calibrated_probability": False,
            "normalized_operating_threshold": 0.5,
            "note": (
                "O campo legado `prob` deve ser interpretado como escore do modelo, "
                "não como probabilidade diagnóstica calibrada. Para classes com "
                "op_threshs, o torchxrayvision aplica sigmoid e op_norm; o ponto "
                "de operação é 0.5 na saída normalizada."
            ),
        },
        "explainability": {
            "method": "Grad-CAM",
            "semantic_scope": "model-attention",
            "lesion_segmentation": False,
        },
        "intended_use": "research-and-education",
        "clinical_use": False,
        "limitations": [
            "Predictions are not calibrated diagnostic probabilities or a radiology report.",
            "Grad-CAM indicates model attention and is not lesion segmentation.",
            "Performance depends on acquisition protocol and dataset shift.",
            "External validation is required before any clinical interpretation.",
            "Returned metadata is filtered, but pixel-level identifiers are not automatically verified.",
        ],
    }
