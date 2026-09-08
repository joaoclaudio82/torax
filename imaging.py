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
    """Expõe apenas campos técnicos permitidos, sem prometer anonimização total."""
    pixel_spacing = getattr(ds, "PixelSpacing", None)
    spacing = None
    if pixel_spacing is not None:
        try:
            spacing = [round(float(value), 4) for value in pixel_spacing[:2]]
        except (TypeError, ValueError):
            spacing = None

    laterality = str(getattr(ds, "ImageLaterality", "") or "") or str(
        getattr(ds, "Laterality", "") or ""
    )
    patient_orientation = getattr(ds, "PatientOrientation", None)
    orientation = None
    if patient_orientation is not None:
        try:
            orientation = [str(value) for value in list(patient_orientation)[:4]]
        except (TypeError, ValueError):
            orientation = None

    return {
        "format": "DICOM",
        "metadata_filtered": True,
        "pixel_phi_checked": False,
        "anonymized": False,
        "deidentification_note": (
            "A API filtra identificadores do cabeçalho retornado, mas não verifica "
            "informações identificáveis gravadas nos pixels."
        ),
        "rows": int(getattr(ds, "Rows", 0) or 0),
        "columns": int(getattr(ds, "Columns", 0) or 0),
        "modality": str(getattr(ds, "Modality", "") or ""),
        "view_position": str(getattr(ds, "ViewPosition", "") or ""),
        "body_part_examined": str(getattr(ds, "BodyPartExamined", "") or ""),
        "image_laterality": laterality,
        "patient_orientation": orientation,
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
    from pydicom.pixels import apply_modality_lut, apply_voi_lut

    ds = pydicom.dcmread(io.BytesIO(data), force=True)
    arr = ds.pixel_array
    if arr.ndim != 2:
        raise ValueError("Apenas radiografias DICOM bidimensionais são suportadas.")

    # Aplica transformações padronizadas quando presentes. A VOI LUT é usada
    # somente quando o dataset fornece parâmetros válidos; caso contrário, os
    # pixels após modality LUT seguem para a normalização do modelo.
    arr = apply_modality_lut(arr, ds).astype(np.float32)
    window_applied = False
    try:
        if hasattr(ds, "VOILUTSequence") or (
            getattr(ds, "WindowCenter", None) is not None
            and getattr(ds, "WindowWidth", None) is not None
        ):
            arr = np.asarray(apply_voi_lut(arr, ds), dtype=np.float32)
            window_applied = True
    except Exception:
        # Datasets DICOM reais frequentemente têm metadados de windowing
        # inconsistentes. Falhar na VOI LUT não deve invalidar pixels decodificados.
        window_applied = False

    if str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        arr = arr.max() + arr.min() - arr

    return arr, _safe_dicom_metadata(ds, window_applied)


def _load_raster(data: bytes) -> tuple[np.ndarray, dict]:
    """Lê PNG/JPG preservando profundidade de bits quando o formato permitir."""
    source = Image.open(io.BytesIO(data))
    source_format = source.format or "RASTER"
    original_mode = source.mode

    # ``convert('L')`` satura PNGs de 16 bits. Modos escalares de alta
    # profundidade são lidos diretamente; imagens RGB/RGBA continuam sendo
    # convertidas para luminância em 8 bits, comportamento esperado para JPG.
    if original_mode in {"I", "I;16", "I;16B", "I;16L", "F"}:
        arr = np.asarray(source, dtype=np.float32)
    else:
        arr = np.asarray(source.convert("L"), dtype=np.float32)

    if arr.ndim != 2:
        raise ValueError("A imagem raster precisa resultar em uma matriz bidimensional.")

    return arr, {
        "format": source_format,
        "metadata_filtered": True,
        "pixel_phi_checked": False,
        "anonymized": False,
        "deidentification_note": (
            "Metadados não são usados na resposta; texto ou identificadores "
            "visíveis nos pixels não são detectados automaticamente."
        ),
        "rows": int(arr.shape[0]),
        "columns": int(arr.shape[1]),
        "source_mode": original_mode,
        "source_bit_depth": _raster_bit_depth(original_mode),
        "photometric_interpretation": "MONOCHROME2",
        "window_applied": False,
    }


def _raster_bit_depth(mode: str) -> int | None:
    if mode in {"1"}:
        return 1
    if mode in {"L", "P", "RGB", "RGBA", "CMYK", "YCbCr"}:
        return 8
    if mode in {"I;16", "I;16B", "I;16L"}:
        return 16
    if mode in {"I", "F"}:
        return 32
    return None


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
    return len(data) > 132 and data[128:132] == b"DICM"


def preprocess(arr2d: np.ndarray):
    """Recebe a matriz 2D bruta e devolve tensor e imagem de visualização."""
    import torch

    arr2d = np.asarray(arr2d, dtype=np.float32)
    if arr2d.ndim != 2 or arr2d.size == 0:
        raise ValueError("Imagem inválida para pré-processamento.")
    if not np.all(np.isfinite(arr2d)):
        arr2d = np.nan_to_num(arr2d, copy=False)

    maximum = float(arr2d.max())
    minimum = float(arr2d.min())
    if maximum - minimum <= 1e-8:
        raise ValueError("Imagem sem faixa dinâmica suficiente para inferência.")

    # Radiografias podem conter valores negativos após modality LUT. Deslocar
    # preserva as diferenças relativas antes da normalização do torchxrayvision.
    shifted = arr2d - minimum if minimum < 0 else arr2d
    maxval = float(shifted.max())
    if maxval <= 0:
        raise ValueError("Imagem sem intensidade positiva após normalização.")

    norm = xrv.datasets.normalize(shifted, maxval)
    if norm.ndim == 2:
        norm = norm[None, ...]

    transform = xrv.datasets.XRayCenterCrop()
    norm = transform(norm)
    norm = xrv.datasets.XRayResizer(224, engine="cv2" if _has_cv2() else "skimage")(norm)

    tensor = torch.from_numpy(norm).float().unsqueeze(0)

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
