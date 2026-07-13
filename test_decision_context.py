from xray_model import _binary_ambiguity, decision_context


def test_ambiguity_is_highest_near_half_probability():
    assert _binary_ambiguity(0.5) == 1.0
    assert _binary_ambiguity(0.99) < 0.1
    assert _binary_ambiguity(0.01) < 0.1


def test_decision_context_lists_borderline_classes_and_top_gap():
    probabilities = {
        "Pneumonia": {
            "prob": 0.62,
            "threshold_band": "borderline",
            "ambiguity": 0.95,
        },
        "Effusion": {
            "prob": 0.51,
            "threshold_band": "above",
            "ambiguity": 1.0,
        },
        "Mass": {
            "prob": 0.1,
            "threshold_band": "below",
            "ambiguity": 0.47,
        },
    }

    context = decision_context(probabilities)

    assert context["borderline_classes"] == ["Pneumonia"]
    assert context["top_probability_gap"] == 0.11
    assert context["highest_ambiguity"][0]["pathology"] == "Effusion"
