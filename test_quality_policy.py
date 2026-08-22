from quality_policy import summarize_quality


def test_good_input_is_acceptable():
    result = summarize_quality({"score": 90, "warnings": []}, {"flags": []})
    assert result["level"] == "acceptable"
    assert result["review_recommended"] is False


def test_low_score_recommends_technical_review():
    result = summarize_quality(
        {"score": 45, "warnings": ["baixo contraste"]},
        {"flags": []},
    )
    assert result["level"] == "poor"
    assert result["review_recommended"] is True
    assert "input_quality_score=45" in result["reasons"]


def test_multiple_qc_flags_trigger_review_even_with_good_score():
    result = summarize_quality(
        {"score": 88, "warnings": []},
        {"flags": ["exposição: subexposta", "possível rotação"]},
    )
    assert result["level"] == "review"
    assert result["review_recommended"] is True
