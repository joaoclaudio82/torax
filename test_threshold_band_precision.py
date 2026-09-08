"""Regressões de precisão nas bordas das faixas do escore normalizado."""
import pytest
import torch

import xray_model


class FixedScoreModel:
    pathologies = ["Pneumonia"]

    def __init__(self, score, dtype, source_threshold=0.1):
        self.output = torch.tensor([[score]], dtype=dtype)
        self.op_threshs = (
            None
            if source_threshold is None
            else torch.tensor([source_threshold], dtype=dtype)
        )

    def __call__(self, _tensor):
        return self.output


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
@pytest.mark.parametrize(
    ("score", "expected_band"),
    [
        (0.0, "below"),
        (0.39999, "below"),
        (0.4, "below"),
        (0.40001, "borderline"),
        (0.49, "borderline"),
        (0.5, "borderline"),
        (0.51, "borderline"),
        (0.59999, "borderline"),
        (0.6, "above"),
        (0.60001, "above"),
        (1.0, "above"),
    ],
)
def test_threshold_band_preserves_inclusive_edges(monkeypatch, dtype, score, expected_band):
    model = FixedScoreModel(score, dtype)
    monkeypatch.setattr(xray_model, "get_model", lambda: model)

    result = xray_model.predict(torch.zeros((1, 1, 224, 224)))["Pneumonia"]

    assert result["threshold_band"] == expected_band
    assert result["op_threshold"] == 0.5
    assert result["source_op_threshold"] == pytest.approx(0.1)
    assert result["score_type"] == "operating-point-normalized"
    # A tolerância afeta somente a faixa; não arredonda o escore nem a margem.
    assert result["prob"] == model.output[0, 0].item()
    assert result["threshold_margin"] == model.output[0, 0].item() - 0.5


@pytest.mark.parametrize("source_threshold", [None, float("nan")])
def test_missing_threshold_remains_unavailable(monkeypatch, source_threshold):
    model = FixedScoreModel(0.4, torch.float32, source_threshold)
    monkeypatch.setattr(xray_model, "get_model", lambda: model)

    result = xray_model.predict(torch.zeros((1, 1, 224, 224)))["Pneumonia"]

    assert result["threshold_band"] == "unavailable"
    assert result["op_threshold"] is None
    assert result["source_op_threshold"] is None
    assert result["threshold_margin"] is None
