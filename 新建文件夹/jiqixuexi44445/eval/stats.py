import numpy as np
from scipy.stats import chi2

def mcnemar_test(correct_a: np.ndarray, correct_b: np.ndarray) -> float:
    """
    McNemar's test for paired binary outcomes.
    Returns p-value.
    """
    # 构建列联表
    # b00: both wrong
    # b01: A wrong, B correct
    # b10: A correct, B wrong
    # b11: both correct
    b01 = np.sum((~correct_a) & correct_b)
    b10 = np.sum(correct_a & (~correct_b))
    if b01 + b10 == 0:
        return 1.0
    chi2_stat = ((b01 - b10) ** 2) / (b01 + b10)
    p_value = 1 - chi2.cdf(chi2_stat, df=1)
    return p_value