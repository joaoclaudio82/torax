"""
Heurísticas educacionais de qualidade radiográfica (não diagnósticas).

Estima exposição relativa, rotação aparente e lateralidade grosseira
a partir de estatísticas de pixels — apenas para ensino de QC.
"""
from __future__ import annotations

import numpy as np


def estimate_exposure(image: np.ndarray) -> dict:
    """Classifica exposição relativa pela média e percentis de intensidade."""
    flat = np.asarray(image, dtype=np.float32).ravel()
    mean = float(np.mean(flat))
    p5 = float(np.percentile(flat, 5))
    p95 = float(np.percentile(flat, 95))
    dynamic_range = p95 - p5

    if mean < 70:
        label = "subexposta"
        tip = "Imagem escura: considere verificar kVp/mAs ou janela de visualização."
    elif mean > 185:
        label = "superexposta"
        tip = "Imagem clara demais: pode haver perda de contraste em tecidos moles."
    else:
        label = "adequada"
        tip = "Exposição relativa dentro de faixa típica educacional."

    return {
        "label": label,
        "mean_intensity": round(mean, 2),
        "p5": round(p5, 2),
        "p95": round(p95, 2),
        "dynamic_range": round(dynamic_range, 2),
        "tip": tip,
    }


def estimate_rotation(image: np.ndarray) -> dict:
    """
    Estima assimetria esquerda-direita como proxy educacional de rotação.

    Compara a média das metades laterais após crop central.
    """
    arr = np.asarray(image, dtype=np.float32)
    h, w = arr.shape[:2]
    y0, y1 = int(h * 0.2), int(h * 0.8)
    x0, x1 = int(w * 0.15), int(w * 0.85)
    crop = arr[y0:y1, x0:x1]
    mid = crop.shape[1] // 2
    left = float(np.mean(crop[:, :mid]))
    right = float(np.mean(crop[:, mid:]))
    delta = left - right
    ratio = abs(delta) / max((left + right) / 2.0, 1e-6)

    if ratio < 0.04:
        label = "simétrica"
        tip = "Sem assimetria grosseira sugerindo rotação marcada."
    elif delta > 0:
        label = "possível rotação (direita anterior)"
        tip = "Metade esquerda mais clara: revise posicionamento / clavículas."
    else:
        label = "possível rotação (esquerda anterior)"
        tip = "Metade direita mais clara: revise posicionamento / clavículas."

    return {
        "label": label,
        "left_mean": round(left, 2),
        "right_mean": round(right, 2),
        "asymmetry_ratio": round(ratio, 4),
        "tip": tip,
    }


def estimate_projection_hint(image: np.ndarray) -> dict:
    """
    Hint grosseiro PA vs AP pela distribuição superior (ombros/clavículas).

    Não substitui metadados DICOM nem avaliação radiológica.
    """
    arr = np.asarray(image, dtype=np.float32)
    h = arr.shape[0]
    upper = arr[: max(1, h // 5), :]
    lower = arr[h // 2 :, :]
    upper_mean = float(np.mean(upper))
    lower_mean = float(np.mean(lower))
    contrast = upper_mean - lower_mean

    if contrast > 12:
        label = "sugestivo de PA (educacional)"
        tip = "Topo relativamente mais claro; confirme com técnica e metadados."
    elif contrast < -8:
        label = "sugestivo de AP (educacional)"
        tip = "Topo relativamente mais escuro; comum em leito — confirme clinicamente."
    else:
        label = "indeterminado"
        tip = "Não foi possível discriminar PA/AP só por estatística de pixels."

    return {
        "label": label,
        "upper_mean": round(upper_mean, 2),
        "lower_mean": round(lower_mean, 2),
        "contrast_delta": round(contrast, 2),
        "tip": tip,
    }


def _to_display_scale(image: np.ndarray) -> np.ndarray:
    """Mapeia a matriz para 0..255 para heurísticas comparáveis entre formatos."""
    arr = np.asarray(image, dtype=np.float32)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return np.zeros_like(arr, dtype=np.float32)
    lo = float(np.percentile(finite, 1))
    hi = float(np.percentile(finite, 99))
    if hi - lo < 1e-6:
        return np.zeros_like(arr, dtype=np.float32)
    scaled = np.clip((arr - lo) / (hi - lo), 0.0, 1.0) * 255.0
    return scaled.astype(np.float32)


def assess_radiograph_quality(image: np.ndarray) -> dict:
    """Agrega heurísticas de QC radiográfico para o painel educacional."""
    scaled = _to_display_scale(image)
    exposure = estimate_exposure(scaled)
    rotation = estimate_rotation(scaled)
    projection = estimate_projection_hint(scaled)

    flags = []
    if exposure["label"] != "adequada":
        flags.append(f"exposição: {exposure['label']}")
    if "rotação" in rotation["label"]:
        flags.append(rotation["label"])
    if projection["label"] != "indeterminado":
        flags.append(projection["label"])

    return {
        "exposure": exposure,
        "rotation": rotation,
        "projection_hint": projection,
        "flags": flags,
        "disclaimer": (
            "Heurísticas educacionais de qualidade de imagem. "
            "Não substituem checklist técnico radiográfico nem decisão clínica."
        ),
    }
