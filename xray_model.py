"""
Carregamento do modelo, inferencia multipatologia e Grad-CAM.

Usa classificação multirrótulo para padrões difusos de radiografia e
Grad-CAM para indicar as regiões que mais influenciaram cada previsão.
"""
from __future__ import annotations

import threading
from functools import lru_cache

import numpy as np
import torch
import torch.nn.functional as F
import torchxrayvision as xrv

WEIGHTS = "densenet121-res224-all"
PNEUMONIA_GROUP = ["Pneumonia", "Consolidation", "Infiltration", "Lung Opacity"]

_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_model():
    loaded_model = xrv.models.DenseNet(weights=WEIGHTS)
    loaded_model.eval()
    return loaded_model


def predict(tensor: torch.Tensor) -> dict:
    """Devolve a probabilidade e o limiar de operação por patologia."""
    loaded_model = get_model()
    with torch.no_grad():
        out = loaded_model(tensor)[0]

    result = {}
    thresholds = loaded_model.op_threshs
    for index, name in enumerate(loaded_model.pathologies):
        if not name:
            continue
        probability = float(out[index].item())
        threshold = None
        if thresholds is not None and not np.isnan(float(thresholds[index])):
            threshold = float(thresholds[index])
        result[name] = {"prob": probability, "op_threshold": threshold}
    return result


def gradcam(tensor: torch.Tensor, target_pathology: str) -> np.ndarray:
    """Gera um mapa Grad-CAM 224x224 normalizado no intervalo [0, 1]."""
    loaded_model = get_model()
    pathologies = loaded_model.pathologies
    if target_pathology not in pathologies:
        raise ValueError(f"Patologia desconhecida: {target_pathology}")
    target_index = list(pathologies).index(target_pathology)
    activations = {}

    def forward_hook(_module, _inputs, output):
        output.retain_grad()
        activations["value"] = output

    handle = loaded_model.features.register_forward_hook(forward_hook)
    try:
        with _lock:
            loaded_model.zero_grad(set_to_none=True)
            x = tensor.clone().requires_grad_(True)
            output = loaded_model(x)
            output[0, target_index].backward()

            activation = activations["value"]
            gradient = activation.grad
            weights = gradient.mean(dim=(2, 3), keepdim=True)
            cam = F.relu((weights * activation).sum(dim=1, keepdim=True))
            cam = F.interpolate(
                cam, size=(224, 224), mode="bilinear", align_corners=False
            )
            cam = cam[0, 0].detach().cpu().numpy()
    finally:
        handle.remove()

    cam = cam - cam.min()
    return cam / (cam.max() + 1e-8)


def cam_stats(cam: np.ndarray) -> dict:
    """Resume a distribuição espacial da ativação sem inferência anatômica."""
    normalized = np.clip(np.asarray(cam, dtype=np.float64), 0.0, 1.0)
    total = float(normalized.sum())
    height, width = normalized.shape

    if total <= 1e-8:
        centroid_x = centroid_y = 0.5
    else:
        yy, xx = np.mgrid[0:height, 0:width]
        centroid_x = float((xx * normalized).sum() / total / max(1, width - 1))
        centroid_y = float((yy * normalized).sum() / total / max(1, height - 1))

    horizontal = "esquerda" if centroid_x < 0.4 else "direita" if centroid_x > 0.6 else "central"
    vertical = "superior" if centroid_y < 0.4 else "inferior" if centroid_y > 0.6 else "média"

    return {
        "mean_activation": round(float(normalized.mean()), 4),
        "p90_activation": round(float(np.percentile(normalized, 90)), 4),
        "peak_activation": round(float(normalized.max()), 4),
        "centroid": {
            "x": round(centroid_x, 3),
            "y": round(centroid_y, 3),
        },
        "visual_region": f"{vertical} {horizontal}",
    }


def top_target(probabilities: dict) -> str:
    """Escolhe a maior probabilidade do grupo pneumônico como alvo do mapa."""
    candidates = {
        name: value["prob"]
        for name, value in probabilities.items()
        if name in PNEUMONIA_GROUP
    }
    if not candidates:
        candidates = {name: value["prob"] for name, value in probabilities.items()}
    return max(candidates, key=candidates.get)
