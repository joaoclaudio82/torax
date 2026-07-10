"""Composicao do mapa de calor sobre a radiografia, sem dependencia de
matplotlib. Implementa um mapa de cores tipo 'jet' em numpy e faz a mistura
alfa com a imagem em tons de cinza."""
from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image


def _jet(x: np.ndarray) -> np.ndarray:
    """Mapa de cores aproximado 'jet'. Entrada em [0,1], saida RGB uint8."""
    x = np.clip(x, 0.0, 1.0)
    r = np.clip(1.5 - np.abs(4 * x - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * x - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * x - 1), 0, 1)
    rgb = np.stack([r, g, b], axis=-1)
    return (rgb * 255).astype(np.uint8)


def to_png_b64(arr: np.ndarray) -> str:
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def make_overlay(gray_u8: np.ndarray, cam: np.ndarray, alpha: float = 0.45,
                 floor: float = 0.35) -> str:
    """Sobrepoe o Grad-CAM na radiografia. Regioes de baixa ativacao ficam
    transparentes para nao poluir a imagem."""
    gray_rgb = np.stack([gray_u8] * 3, axis=-1).astype(np.float32)
    heat = _jet(cam).astype(np.float32)

    # Mascara: so mistura onde a ativacao passa de um piso.
    mask = np.clip((cam - floor) / (1 - floor + 1e-8), 0, 1)[..., None]
    blended = gray_rgb * (1 - alpha * mask) + heat * (alpha * mask)
    return to_png_b64(blended.astype(np.uint8))


def gray_to_b64(gray_u8: np.ndarray) -> str:
    return to_png_b64(gray_u8)
