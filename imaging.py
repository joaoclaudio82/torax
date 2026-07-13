"""
Carregamento e pre-processamento de imagens de radiografia de torax.

Aceita PNG, JPG e DICOM. Converte tudo para uma matriz 2D em tons de cinza,
normaliza para a faixa esperada pelo torchxrayvision ([-1024, 1024]) e
redimensiona para 224x224, que e a resolucao dos modelos pre-treinados.
"""
from __future__ import annotations

import io
import numpy as np
from PIL import Image

import torchxrayvision as xrv
import skimage


def assess_quality(arr2d: np.ndarray) -> dict:
    """Calcula indicadores heurísticos de qualidade sem bloquear a análise."""
    if arr2d.ndim != 2 or arr2d.size == 0:
        return {
            "score": 0,
            "level": "insufficient",
            "warnings": ["A imagem não possui uma matriz bidimensional válida."],
            "metrics": {},
        }

    height, width = arr2d.shape
    finite = arr2d[np.isfinite(arr2d)].astype(np.float64)
    if finite.size == 0:
        return {
            "score": 0,
            "level": "insufficient",
            "warnings": ["A imagem não contém valores de pixel válidos."],
            "metrics": {"width": width, "height": height},
        }

    minimum = float(finite.min())
    maximum = float(finite.max())
    dynamic_range = maximum - minimum
    normalized = (finite - minimum) / (dynamic_range + 1e-8)
    contrast = float(normalized.std())
    aspect_ratio = max(width, height) / max(1, min(width, height))
    dark_clip = float(np.mean(normalized <= 0.01))
    light_clip = float(np.mean(normalized >= 0.99))

    score = 100
    warnings = []
    if min(width, height) < 128:
        score -= 30
        warnings.append("Resolução baixa; detalhes finos podem ser perdidos.")
    if aspect_ratio > 2.2:
        score -= 20
        warnings.append("Proporção atípica; verifique recorte e orientação.")
    if dynamic_range <= 1e-6:
        score -= 70
        warnings.append("Imagem praticamente uniforme, sem faixa dinâmica útil.")
    elif contrast < 0.12:
        score -= 20
        warnings.append("Contraste global baixo.")
    if dark_clip > 0.35:
        score -= 10
        warnings.append("Grande parte dos pixels está próxima do preto.")
    if light_clip > 0.35:
        score -= 10
        warnings.append("Grande parte dos pixels está próxima do branco.")

    score = max(0, score)
    if score >= 85:
        level = "good"
    elif score >= 65:
        level = "adequate"
    else:
        level = "attention"

    return {
        "score": score,
        "level": level,
        "warnings": warnings,
        "metrics": {
            "width": width,
            "height": height,
            "aspect_ratio": round(aspect_ratio, 2),
            "contrast": round(contrast, 3),
            "dynamic_range": round(dynamic_range, 2),
            "dark_clip_percent": round(dark_clip * 100, 1),
            "light_clip_percent": round(light_clip * 100, 1),
        },
    }


def _first_number(value) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (str, bytes)):
        try:
            value = value[0]
        except (IndexError, TypeError):
            pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_dicom_metadata(ds, window_applied: bool) -> dict:
    """Expõe apenas campos técnicos sem identificadores do paciente."""
    pixel_spacing = getattr(ds, "PixelSpacing", None)
    spacing = None
    if pixel_spacing is not None:
        try:
            spacing = [round(float(value), 4) for value in pixel_spacing[:2]]
        except (TypeError, ValueError):
            spacing = None

    return {
        "format": "DICOM",
        "anonymized": True,
        "rows": int(getattr(ds, "Rows", 0) or 0),
        "columns": int(getattr(ds, "Columns", 0) or 0),
        "modality": str(getattr(ds, "Modality", "") or ""),
        "view_position": str(getattr(ds, "ViewPosition", "") or ""),
        "body_part_examined": str(getattr(ds, "BodyPartExamined", "") or ""),
        "photometric_interpretation": str(
            getattr(ds, "PhotometricInterpretation", "") or ""
        ),
        "bits_stored": int(getattr(ds, "BitsStored", 0) or 0),
        "pixel_spacing": spacing,
        "window_center": _first_number(getattr(ds, "WindowCenter", None)),
        "window_width": _first_number(getattr(ds, "WindowWidth", None)),
        "window_applied": window_applied,
    }


def _load_dicom(data: bytes) -> tuple[np.ndarray, dict]:
    """Lê DICOM, aplica rescale/window e devolve metadados técnicos seguros."""
    import pydicom

    ds = pydicom.dcmread(io.BytesIO(data), force=True)
    arr = ds.pixel_array.astype(np.float32)

    slope = float(getattr(ds, "RescaleSlope", 1.0) or 1.0)
    intercept = float(getattr(ds, "RescaleIntercept", 0.0) or 0.0)
    arr = arr * slope + intercept

    window_center = _first_number(getattr(ds, "WindowCenter", None))
    window_width = _first_number(getattr(ds, "WindowWidth", None))
    window_applied = (
        window_center is not None
        and window_width is not None
        and window_width > 1
    )
    if window_applied:
        lower = window_center - window_width / 2
        upper = window_center + window_width / 2
        arr = np.clip(arr, lower, upper)

    # Em MONOCHROME1 o branco e o valor minimo; invertemos para ficar
    # coerente com radiografias comuns (osso claro sobre fundo escuro).
    if str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        arr = arr.max() - arr

    return arr, _safe_dicom_metadata(ds, window_applied)


def _load_raster(data: bytes) -> tuple[np.ndarray, dict]:
    """Lê PNG/JPG e devolve pixels e metadados técnicos mínimos."""
    source = Image.open(io.BytesIO(data))
    source_format = source.format or "RASTER"
    img = source.convert("L")
    return np.asarray(img).astype(np.float32), {
        "format": source_format,
        "anonymized": True,
        "rows": img.height,
        "columns": img.width,
        "photometric_interpretation": "MONOCHROME2",
        "window_applied": False,
    }


def load_image_with_metadata(data: bytes, filename: str) -> tuple[np.ndarray, dict]:
    """Roteia por extensão e devolve pixels com metadados técnicos seguros."""
    name = (filename or "").lower()
    if name.endswith((".dcm", ".dicom")) or _looks_like_dicom(data):
        return _load_dicom(data)
    return _load_raster(data)


def load_image(data: bytes, filename: str) -> np.ndarray:
    """Compatibilidade: devolve apenas a matriz de pixels."""
    image, _metadata = load_image_with_metadata(data, filename)
    return image


def _looks_like_dicom(data: bytes) -> bool:
    # DICOM tem a marca "DICM" no offset 128.
    return len(data) > 132 and data[128:132] == b"DICM"


def preprocess(arr2d: np.ndarray):
    """Recebe a matriz 2D bruta e devolve:
      - tensor pronto para o modelo, formato [1, 1, 224, 224]
      - a versao 224x224 em tons de cinza (0..255 uint8) para exibicao/overlay
    """
    import torch

    maxval = float(arr2d.max()) if arr2d.max() > 0 else 255.0
    # Normaliza para a escala interna do torchxrayvision.
    norm = xrv.datasets.normalize(arr2d, maxval)  # faixa aproximada [-1024, 1024]

    if norm.ndim == 2:
        norm = norm[None, ...]  # canal unico -> [1, H, W]

    transform = xrv.datasets.XRayCenterCrop()
    norm = transform(norm)
    norm = xrv.datasets.XRayResizer(224, engine="cv2" if _has_cv2() else "skimage")(norm)

    tensor = torch.from_numpy(norm).float().unsqueeze(0)  # [1, 1, 224, 224]

    # Versao visivel: reaproveita a mesma matriz normalizada, reescalada 0..255.
    vis = norm[0]
    vis = (vis - vis.min()) / (vis.max() - vis.min() + 1e-8)
    vis_u8 = (vis * 255).astype(np.uint8)

    return tensor, vis_u8


def _has_cv2() -> bool:
    try:
        import cv2  # noqa: F401
        return True
    except Exception:
        return False
