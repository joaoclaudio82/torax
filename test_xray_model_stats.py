import numpy as np

from xray_model import cam_stats


def test_cam_stats_locates_upper_left_activation():
    cam = np.zeros((224, 224), dtype=np.float32)
    cam[20:60, 25:65] = 1.0

    stats = cam_stats(cam)

    assert stats["visual_region"] == "superior esquerda"
    assert stats["peak_activation"] == 1.0
    assert stats["centroid"]["x"] < 0.4
    assert stats["centroid"]["y"] < 0.4


def test_cam_stats_handles_empty_activation():
    stats = cam_stats(np.zeros((224, 224), dtype=np.float32))

    assert stats["mean_activation"] == 0.0
    assert stats["centroid"] == {"x": 0.5, "y": 0.5}
    assert stats["visual_region"] == "média central"
