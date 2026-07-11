import numpy as np

from imaging import assess_quality


def test_quality_accepts_detailed_image():
    rng = np.random.default_rng(42)
    image = rng.normal(120, 35, (512, 512)).clip(0, 255).astype(np.float32)

    quality = assess_quality(image)

    assert quality["score"] >= 65
    assert quality["level"] in {"good", "adequate"}
    assert quality["metrics"]["width"] == 512
    assert quality["metrics"]["height"] == 512


def test_quality_warns_about_uniform_image():
    image = np.full((256, 256), 80, dtype=np.float32)

    quality = assess_quality(image)

    assert quality["score"] <= 30
    assert quality["level"] == "attention"
    assert any("uniforme" in warning for warning in quality["warnings"])


def test_quality_warns_about_low_resolution_and_extreme_ratio():
    image = np.arange(64 * 320, dtype=np.float32).reshape(64, 320)

    quality = assess_quality(image)

    assert quality["score"] <= 50
    assert len(quality["warnings"]) >= 2
