import torch

from uncertainty import estimate_prediction_stability


def test_estimate_prediction_stability_structure():
    tensor = torch.zeros(1, 1, 224, 224)
    report = estimate_prediction_stability(tensor, samples=2)
    assert report["samples"] == 2
    assert "mean_std" in report
    assert "stability_label" in report
    assert len(report["most_variable"]) <= 5
    assert "clínico" in report["note"] or "clinico" in report["note"].lower()
