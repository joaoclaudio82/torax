"""Metadados transparentes do modelo para clientes e documentação da API."""
from __future__ import annotations


def build_model_card(model, *, weights: str) -> dict:
    pathologies = [item for item in getattr(model, "pathologies", []) if item]
    thresholds = getattr(model, "op_threshs", None)
    thresholds_available = 0
    if thresholds is not None:
        for value in thresholds:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if numeric == numeric:  # NaN é o único float diferente de si próprio.
                thresholds_available += 1

    return {
        "architecture": "DenseNet-121",
        "provider": "torchxrayvision",
        "weights": weights,
        "input_shape": [1, 1, 224, 224],
        "task": "multilabel chest radiograph classification",
        "pathologies": pathologies,
        "pathology_count": len(pathologies),
        "operating_thresholds_available": thresholds_available,
        "intended_use": "research-and-education",
        "clinical_use": False,
        "limitations": [
            "Predictions are not a radiology report.",
            "Grad-CAM indicates model attention and is not lesion segmentation.",
            "Performance depends on acquisition protocol and dataset shift.",
        ],
    }
