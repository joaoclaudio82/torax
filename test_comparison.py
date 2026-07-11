from comparison import build_prediction_deltas


def test_prediction_deltas_are_sorted_by_magnitude():
    probabilities_a = {
        "Pneumonia": {"prob": 0.2},
        "Effusion": {"prob": 0.8},
        "Mass": {"prob": 0.4},
    }
    probabilities_b = {
        "Pneumonia": {"prob": 0.7},
        "Effusion": {"prob": 0.6},
        "Mass": {"prob": 0.4},
    }

    deltas = build_prediction_deltas(probabilities_a, probabilities_b)

    assert [item["pathology"] for item in deltas] == [
        "Pneumonia",
        "Effusion",
        "Mass",
    ]
    assert deltas[0]["delta"] == 0.5
    assert deltas[0]["direction"] == "higher_in_b"
    assert deltas[1]["direction"] == "higher_in_a"
    assert deltas[2]["direction"] == "stable"


def test_prediction_deltas_only_compare_shared_classes():
    deltas = build_prediction_deltas(
        {"Pneumonia": {"prob": 0.1}},
        {"Effusion": {"prob": 0.2}},
    )

    assert deltas == []
