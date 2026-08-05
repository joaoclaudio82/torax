"""
Estimativas educacionais de estabilidade da saída do modelo.

Usa pequenas perturbações (TTA leve) para medir variação das probabilidades.
Não representa incerteza clínica calibrada.
"""
from __future__ import annotations

import numpy as np
import torch

import xray_model


def _augment_tensor(tensor: torch.Tensor, seed: int) -> torch.Tensor:
    """Aplica flip horizontal e ruído leve de forma determinística por seed."""
    rng = np.random.default_rng(seed)
    variant = tensor.clone()
    if seed % 2 == 1:
        variant = torch.flip(variant, dims=[-1])
    noise = torch.from_numpy(
        rng.normal(0.0, 8.0, size=variant.shape).astype(np.float32)
    )
    return variant + noise


def estimate_prediction_stability(
    tensor: torch.Tensor,
    samples: int = 4,
) -> dict:
    """
    Executa TTA leve e resume dispersão das top classes.

    Retorna desvio médio e classes com maior variação relativa.
    """
    samples = max(2, min(samples, 8))
    baseline = xray_model.predict(tensor)
    names = list(baseline.keys())
    runs = [baseline]

    for index in range(1, samples):
        augmented = _augment_tensor(tensor, seed=index)
        runs.append(xray_model.predict(augmented))

    per_class = {}
    for name in names:
        values = [run[name]["prob"] for run in runs]
        mean = float(np.mean(values))
        std = float(np.std(values))
        per_class[name] = {
            "mean": round(mean, 4),
            "std": round(std, 4),
            "min": round(float(np.min(values)), 4),
            "max": round(float(np.max(values)), 4),
        }

    ranked_unstable = sorted(
        (
            {"pathology": name, "std": values["std"], "mean": values["mean"]}
            for name, values in per_class.items()
        ),
        key=lambda item: item["std"],
        reverse=True,
    )[:5]
    mean_std = float(np.mean([values["std"] for values in per_class.values()]))

    if mean_std < 0.02:
        stability_label = "estável"
    elif mean_std < 0.05:
        stability_label = "moderada"
    else:
        stability_label = "sensível a perturbações"

    return {
        "samples": samples,
        "mean_std": round(mean_std, 4),
        "stability_label": stability_label,
        "most_variable": ranked_unstable,
        "note": (
            "Estabilidade sob TTA leve descreve sensibilidade matemática "
            "da saída; não é intervalo de confiança clínico."
        ),
    }
