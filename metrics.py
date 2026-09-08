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
    """F1 = 2*VP / (2*VP + FP + FN).

    A forma por contagens evita transformar o caso válido F1=0 em ``None``
    quando precisão e sensibilidade são ambas zero.
    """
    denominator = 2 * counts["tp"] + counts["fp"] + counts["fn"]
    if denominator == 0:
        return None
    return round((2 * counts["tp"]) / denominator, 4)


def binary_auroc(y_true: list[int], scores: list[float]) -> float | None:
    """AUROC por ranks com tratamento de empates em O(n log n)."""
    if len(y_true) != len(scores) or not y_true:
        raise ValueError("Entradas inválidas para AUROC.")
    if any(label not in (0, 1) for label in y_true):
        raise ValueError("Rótulos devem ser 0 ou 1.")

    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None

    ordered = sorted(zip(scores, y_true), key=lambda item: item[0])
    rank = 1
    positive_rank_sum = 0.0
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]:
            end += 1
        # Ranks são 1-based; empates recebem a média dos ranks ocupados.
        group_size = end - index
        average_rank = (rank + (rank + group_size - 1)) / 2
        positives_in_group = sum(label for _score, label in ordered[index:end])
        positive_rank_sum += positives_in_group * average_rank
        rank += group_size
        index = end

    u_statistic = positive_rank_sum - n_pos * (n_pos + 1) / 2
    return round(u_statistic / (n_pos * n_neg), 4)


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
