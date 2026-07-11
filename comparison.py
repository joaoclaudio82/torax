from __future__ import annotations


def build_prediction_deltas(probabilities_a: dict, probabilities_b: dict) -> list[dict]:
    """Compara duas saídas do mesmo modelo, ordenando pela maior variação."""
    shared = sorted(set(probabilities_a) & set(probabilities_b))
    deltas = []
    for pathology in shared:
        probability_a = float(probabilities_a[pathology]["prob"])
        probability_b = float(probabilities_b[pathology]["prob"])
        delta = probability_b - probability_a
        deltas.append(
            {
                "pathology": pathology,
                "probability_a": round(probability_a, 4),
                "probability_b": round(probability_b, 4),
                "delta": round(delta, 4),
                "absolute_delta": round(abs(delta), 4),
                "direction": "higher_in_b" if delta > 0 else "higher_in_a" if delta < 0 else "stable",
            }
        )

    return sorted(deltas, key=lambda item: item["absolute_delta"], reverse=True)
