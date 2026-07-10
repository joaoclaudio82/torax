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


def _load_dicom(data: bytes) -> np.ndarray:
    """Le um DICOM e devolve a matriz de pixels em float, ja tratando
    inclinacao/interceptacao e a inversao de MONOCHROME1."""
    import pydicom

    ds = pydicom.dcmread(io.BytesIO(data), force=True)
    arr = ds.pixel_array.astype(np.float32)

    slope = float(getattr(ds, "RescaleSlope", 1.0) or 1.0)
    intercept = float(getattr(ds, "RescaleIntercept", 0.0) or 0.0)
    arr = arr * slope + intercept

    # Em MONOCHROME1 o branco e o valor minimo; invertemos para ficar
    # coerente com radiografias comuns (osso claro sobre fundo escuro).
    if str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        arr = arr.max() - arr

    return arr


def _load_raster(data: bytes) -> np.ndarray:
    """Le PNG/JPG e devolve matriz 2D em tons de cinza (uint agnostico)."""
    img = Image.open(io.BytesIO(data)).convert("L")
    return np.asarray(img).astype(np.float32)


def load_image(data: bytes, filename: str) -> np.ndarray:
    """Roteia por extensao e devolve a matriz 2D bruta em tons de cinza."""
    name = (filename or "").lower()
    if name.endswith((".dcm", ".dicom")) or _looks_like_dicom(data):
        return _load_dicom(data)
    return _load_raster(data)


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
