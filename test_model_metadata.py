import math

from model_metadata import build_model_card


class FakeModel:
    pathologies = ["Pneumonia", "Effusion", ""]
    op_threshs = [0.4, math.nan, 0.3]


def test_model_card_reports_public_model_contract():
    card = build_model_card(FakeModel(), weights="demo-weights")
    assert card["model_card_version"] == "1.1"
    assert card["architecture"] == "DenseNet-121"
    assert card["weights"] == "demo-weights"
    assert card["pathology_count"] == 2
    assert card["operating_thresholds_available"] == 1
    assert card["clinical_use"] is False
    assert card["input_shape"] == [1, 1, 224, 224]


def test_model_card_does_not_present_scores_as_calibrated_probabilities():
    card = build_model_card(FakeModel(), weights="demo-weights")
    semantics = card["score_semantics"]

    assert semantics["legacy_api_field"] == "prob"
    assert semantics["recommended_name"] == "model_score"
    assert semantics["calibrated_probability"] is False
    assert semantics["normalized_operating_threshold"] == 0.5
    assert card["explainability"]["lesion_segmentation"] is False
    assert any("External validation" in item for item in card["limitations"])
