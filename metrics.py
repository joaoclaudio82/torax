"""
Métricas educacionais para validação de classificadores multirrótulo.

Funções puras e determinísticas, sem dependência de frameworks clínicos.
"""
from __future__ import annotations


def confusion_counts(y_true: list[int], y_pred: list[int]) -> dict:
    """Conta VP, VN, FP e FN para rótulos binários 0/1."""
    if len(y_true) != len(y_pred):
        raise ValueError("y_true e y_pred devem ter o mesmo tamanho.")
    if not y_true:
        raise ValueError("Listas vazias não são válidas.")

    tp = tn = fp = fn = 0
    for truth, prediction in zip(y_true, y_pred):
        if truth not in (0, 1) or prediction not in (0, 1):
            raise ValueError("Rótulos devem ser 0 ou 1.")
        if truth == 1 and prediction == 1:
            tp += 1
        elif truth == 0 and prediction == 0:
            tn += 1
        elif truth == 0 and prediction == 1:
            fp += 1
        else:
            fn += 1
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def sensitivity(counts: dict) -> float | None:
    """Recall / sensibilidade: VP / (VP + FN)."""
    denominator = counts["tp"] + counts["fn"]
    if denominator == 0:
        return None
    return round(counts["tp"] / denominator, 4)


def specificity(counts: dict) -> float | None:
    """Especificidade: VN / (VN + FP)."""
    denominator = counts["tn"] + counts["fp"]
    if denominator == 0:
        return None
    return round(counts["tn"] / denominator, 4)


def precision(counts: dict) -> float | None:
    denominator = counts["tp"] + counts["fp"]
    if denominator == 0:
        return None
    return round(counts["tp"] / denominator, 4)


def f1_score(counts: dict) -> float | None:
    prec = precision(counts)
    sens = sensitivity(counts)
    if prec is None or sens is None or (prec + sens) == 0:
        return None
    return round(2 * prec * sens / (prec + sens), 4)


def binary_auroc(y_true: list[int], scores: list[float]) -> float | None:
    """AUROC por ranking (Mann-Whitney) para uma classe binária."""
    if len(y_true) != len(scores) or not y_true:
        raise ValueError("Entradas inválidas para AUROC.")

    positives = [score for label, score in zip(y_true, scores) if label == 1]
    negatives = [score for label, score in zip(y_true, scores) if label == 0]
    if not positives or not negatives:
        return None

    greater = equal = 0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                greater += 1
            elif positive == negative:
                equal += 1
    return round((greater + 0.5 * equal) / (len(positives) * len(negatives)), 4)


def summarize_binary_evaluation(
    y_true: list[int],
    y_pred: list[int],
    scores: list[float] | None = None,
) -> dict:
    """Resume métricas binárias usadas em painéis educacionais."""
    counts = confusion_counts(y_true, y_pred)
    summary = {
        "counts": counts,
        "sensitivity": sensitivity(counts),
        "specificity": specificity(counts),
        "precision": precision(counts),
        "f1": f1_score(counts),
        "auroc": None,
        "note": (
            "Métricas de pesquisa. Não constituem desempenho clínico "
            "validado para uso diagnóstico."
        ),
    }
    if scores is not None:
        summary["auroc"] = binary_auroc(y_true, scores)
    return summary
