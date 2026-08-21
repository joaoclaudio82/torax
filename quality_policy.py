"""Agrega sinais de qualidade em uma recomendação técnica não clínica."""
from __future__ import annotations


def summarize_quality(input_quality: dict, radiograph_quality: dict) -> dict:
    score = int(input_quality.get("score", 0) or 0)
    warnings = list(input_quality.get("warnings", []) or [])
    qc_flags = list(radiograph_quality.get("flags", []) or [])

    if score < 50:
        level = "poor"
        review_recommended = True
    elif score < 70 or len(qc_flags) >= 2:
        level = "review"
        review_recommended = True
    else:
        level = "acceptable"
        review_recommended = False

    reasons: list[str] = []
    if score < 70:
        reasons.append(f"input_quality_score={score}")
    reasons.extend(qc_flags[:4])
    reasons.extend(warnings[:2])

    return {
        "level": level,
        "review_recommended": review_recommended,
        "reasons": reasons,
        "note": (
            "Sinal técnico de qualidade de entrada para fins educacionais; "
            "não valida adequação diagnóstica da radiografia."
        ),
    }
