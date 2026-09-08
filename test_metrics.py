from metrics import (
    binary_auroc,
    confusion_counts,
    f1_score,
    precision,
    sensitivity,
    specificity,
    summarize_binary_evaluation,
)


def test_confusion_counts_basic():
    counts = confusion_counts([1, 0, 1, 0], [1, 0, 0, 1])
    assert counts == {"tp": 1, "tn": 1, "fp": 1, "fn": 1}


def test_sensitivity_specificity_precision_f1():
    counts = {"tp": 8, "tn": 6, "fp": 2, "fn": 4}
    assert sensitivity(counts) == 0.6667
    assert specificity(counts) == 0.75
    assert precision(counts) == 0.8
    assert f1_score(counts) == 0.7273


def test_f1_is_zero_when_predictions_have_no_true_positives():
    counts = {"tp": 0, "tn": 8, "fp": 1, "fn": 1}
    assert f1_score(counts) == 0.0


def test_f1_is_undefined_only_when_no_positive_case_or_prediction_exists():
    counts = {"tp": 0, "tn": 10, "fp": 0, "fn": 0}
    assert f1_score(counts) is None


def test_binary_auroc_perfect_and_random():
    assert binary_auroc([1, 1, 0, 0], [0.9, 0.8, 0.2, 0.1]) == 1.0
    assert binary_auroc([1, 0, 1, 0], [0.5, 0.5, 0.5, 0.5]) == 0.5


def test_binary_auroc_handles_partial_ties():
    assert binary_auroc([1, 0, 1, 0], [0.8, 0.8, 0.6, 0.2]) == 0.625


def test_summarize_binary_evaluation():
    summary = summarize_binary_evaluation(
        [1, 1, 0, 0],
        [1, 0, 0, 0],
        [0.9, 0.4, 0.2, 0.1],
    )
    assert summary["counts"]["tp"] == 1
    assert summary["auroc"] is not None
    assert "pesquisa" in summary["note"].lower()
