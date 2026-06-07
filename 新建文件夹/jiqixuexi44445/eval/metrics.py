import numpy as np
from typing import List, Dict, Any

def accuracy(results: List[Dict]) -> float:
    """计算准确率"""
    if not results:
        return 0.0
    correct = sum(1 for r in results if r.get("correct", False))
    return correct / len(results)

def wilson_interval(n_correct: int, n_total: int, confidence: float = 0.95) -> tuple:
    """Wilson score interval for proportion"""
    from scipy.stats import norm
    if n_total == 0:
        return (0, 0)
    z = norm.ppf(1 - (1 - confidence) / 2)
    p = n_correct / n_total
    denominator = 1 + z**2 / n_total
    centre_adjusted = (p + z**2 / (2 * n_total)) / denominator
    half_width = z * np.sqrt((p * (1 - p) + z**2 / (4 * n_total)) / n_total) / denominator
    return (centre_adjusted - half_width, centre_adjusted + half_width)

def bootstrap_ci(scores: List[bool], n_resamples: int = 1000, confidence: float = 0.95) -> tuple:
    """Bootstrap confidence interval for accuracy"""
    rng = np.random.RandomState(42)
    n = len(scores)
    accs = []
    for _ in range(n_resamples):
        sample = rng.choice(scores, size=n, replace=True)
        accs.append(np.mean(sample))
    lower = np.percentile(accs, (1 - confidence) / 2 * 100)
    upper = np.percentile(accs, (1 + confidence) / 2 * 100)
    return (lower, upper)

def win_matrix(results_by_strategy: Dict[str, List[Dict]]) -> Dict[str, Dict[str, int]]:
    """
    results_by_strategy: {"ReAct": [{"correct": bool, ...}, ...], ...}
    返回 win_matrix: {"ReAct": {"PlanAndExecute": 5, "SelfConsistency": 8}, ...}
    """
    strategies = list(results_by_strategy.keys())
    matrix = {s: {t: 0 for t in strategies if t != s} for s in strategies}
    n_problems = len(next(iter(results_by_strategy.values())))
    for i in range(n_problems):
        correct = {s: results_by_strategy[s][i]["correct"] for s in strategies}
        for s1 in strategies:
            for s2 in strategies:
                if s1 == s2:
                    continue
                if correct[s1] and not correct[s2]:
                    matrix[s1][s2] += 1
    return matrix