"""
Carregamento do modelo, inferencia multipatologia e Grad-CAM.

Usa classificação multirrótulo para padrões difusos de radiografia e
Grad-CAM para indicar as regiões que mais influenciaram cada previsão.
"""
from __future__ import annotations

import math
import threading
from functools import lru_cache

import numpy as np
import torch
import torch.nn.functional as F
import torchxrayvision as xrv

WEIGHTS = "densenet121-res224-all"
PNEUMONIA_GROUP = ["Pneumonia", "Consolidation", "Infiltration", "Lung Opacity"]

# O torchxrayvision usa uma única instância de modelo em cache. Predição e
# Grad-CAM compartilham essa instância e, portanto, precisam compartilhar o
# mesmo lock. RLock evita deadlock caso uma operação interna seja reutilizada.
_model_lock = threading.RLock()


def _binary_ambiguity(probability: float) -> float:
    probability = min(1.0, max(0.0, probability))
    if probability in (0.0, 1.0):
        return 0.0
    entropy = -(
        probability * math.log2(probability)
        + (1 - probability) * math.log2(1 - probability)
    )
    return round(entropy, 4)


@lru_cache(maxsize=1)
def get_model():
    loaded_model = xrv.models.DenseNet(weights=WEIGHTS)
    loaded_model.eval()
    return loaded_model


def predict(tensor: torch.Tensor) -> dict:
    """Devolve o escore normalizado e o limiar coerente por patologia.

    Para pesos com ``op_threshs``, o torchxrayvision já aplica sigmoid seguida
    de ``op_norm`` no ``forward``. Nessa escala normalizada, o ponto de operação
    de cada classe corresponde a 0.5. ``source_op_threshold`` preserva o limiar
    original dos pesos apenas para rastreabilidade; ele não deve ser comparado
    diretamente com o escore retornado pelo modelo.
    """
    loaded_model = get_model()
    with _model_lock:
        with torch.no_grad():
            out = loaded_model(tensor)[0]

    result = {}
    thresholds = loaded_model.op_threshs
    for index, name in enumerate(loaded_model.pathologies):
        if not name:
            continue
        score = float(out[index].item())
        source_threshold = None
        if thresholds is not None and not np.isnan(float(thresholds[index])):
            source_threshold = float(thresholds[index])

        # Quando op_threshs existe, o forward da biblioteca transforma o
        # escore de modo que o ponto de operação fique exatamente em 0.5.
        threshold = 0.5 if source_threshold is not None else None
        margin = score - threshold if threshold is not None else None
        if margin is None:
            threshold_band = "unavailable"
        elif margin >= 0.1:
            threshold_band = "above"
        elif margin <= -0.1:
            threshold_band = "below"
        else:
            threshold_band = "borderline"
        result[name] = {
            # Mantém ``prob`` por compatibilidade com a API/UI existente.
            # Semanticamente, trata-se de um escore normalizado pelo ponto de
            # operação, não de probabilidade diagnóstica calibrada.
            "prob": score,
            "score_type": "operating-point-normalized" if threshold is not None else "model-output",
            "op_threshold": threshold,
            "source_op_threshold": source_threshold,
            "threshold_margin": margin,
            "threshold_band": threshold_band,
            "ambiguity": _binary_ambiguity(score),
        }
    return result


def decision_context(probabilities: dict) -> dict:
    """Contextualiza saídas sem tratá-las como confiança clínica."""
    ranked = sorted(
        probabilities.items(),
        key=lambda item: item[1]["prob"],
        reverse=True,
    )
    top_gap = (
        ranked[0][1]["prob"] - ranked[1][1]["prob"]
        if len(ranked) > 1
        else 0.0
    )
    borderline = [
        name
        for name, values in probabilities.items()
        if values.get("threshold_band") == "borderline"
    ]
    highest_ambiguity = sorted(
        (
            {"pathology": name, "ambiguity": values["ambiguity"]}
            for name, values in probabilities.items()
        ),
        key=lambda item: item["ambiguity"],
        reverse=True,
    )[:3]
    return {
        "top_probability_gap": round(float(top_gap), 4),
        "borderline_classes": borderline,
        "highest_ambiguity": highest_ambiguity,
        "score_semantics": (
            "Os escores podem estar normalizados pelo ponto de operação do modelo; "
            "não representam probabilidade diagnóstica calibrada."
        ),
        "note": (
            "Ambiguidade e margem descrevem a saída matemática do modelo; "
            "não representam certeza diagnóstica."
        ),
    }


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

    # O hook precisa existir apenas enquanto nenhum outro forward usa a mesma
    # instância. Registrar o hook fora do lock permitia que um predict sob
    # torch.no_grad() disparasse retain_grad() em um tensor sem gradiente.
    with _model_lock:
        handle = loaded_model.features.register_forward_hook(forward_hook)
        try:
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
            loaded_model.zero_grad(set_to_none=True)

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
