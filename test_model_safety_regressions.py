import io

import numpy as np
import torch
from PIL import Image

import imaging
import xray_model


class FakeModel:
    pathologies = ["Pneumonia"]
    op_threshs = torch.tensor([0.1])

    def __call__(self, _tensor):
        # Simula saída já normalizada por op_norm. Nessa escala, 0.5 é o ponto
        # de operação; 0.4 deve permanecer abaixo do limiar.
        return torch.tensor([[0.4]], dtype=torch.float32)


def test_predict_uses_normalized_operating_threshold(monkeypatch):
    monkeypatch.setattr(xray_model, "get_model", lambda: FakeModel())
    result = xray_model.predict(torch.zeros((1, 1, 224, 224)))
    prediction = result["Pneumonia"]

    assert prediction["prob"] == pytest_approx(0.4)
    assert prediction["op_threshold"] == 0.5
    assert prediction["source_op_threshold"] == pytest_approx(0.1)
    assert prediction["threshold_margin"] == pytest_approx(-0.1)
    assert prediction["threshold_band"] == "below"
    assert prediction["score_type"] == "operating-point-normalized"


def test_png_16bit_preserves_distinct_intensities():
    source = np.array([[0, 256], [1024, 4095]], dtype=np.uint16)
    buffer = io.BytesIO()
    Image.fromarray(source, mode="I;16").save(buffer, format="PNG")

    image, metadata = imaging.load_image_with_metadata(buffer.getvalue(), "study.png")

    assert image.shape == (2, 2)
    assert image[0, 1] == 256
    assert image[1, 0] == 1024
    assert image[1, 1] == 4095
    assert len(np.unique(image)) == 4
    assert metadata["source_bit_depth"] in {16, 32}
    assert metadata["pixel_phi_checked"] is False
    assert metadata["anonymized"] is False


def pytest_approx(value):
    import pytest

    return pytest.approx(value, abs=1e-6)
