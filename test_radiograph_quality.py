import numpy as np

from radiograph_quality import (
    assess_radiograph_quality,
    estimate_exposure,
    estimate_rotation,
)


def test_exposure_labels_dark_and_bright_images():
    dark = np.full((128, 128), 40.0, dtype=np.float32)
    bright = np.full((128, 128), 220.0, dtype=np.float32)
    assert estimate_exposure(dark)["label"] == "subexposta"
    assert estimate_exposure(bright)["label"] == "superexposta"


def test_rotation_detects_asymmetric_halves():
    image = np.zeros((200, 200), dtype=np.float32)
    image[:, :100] = 180
    image[:, 100:] = 40
    result = estimate_rotation(image)
    assert "rotação" in result["label"]
    assert result["asymmetry_ratio"] > 0.04


def test_assess_radiograph_quality_structure():
    rng = np.random.default_rng(0)
    image = rng.uniform(60, 180, size=(256, 256)).astype(np.float32)
    report = assess_radiograph_quality(image)
    assert "exposure" in report
    assert "rotation" in report
    assert "projection_hint" in report
    assert "disclaimer" in report
