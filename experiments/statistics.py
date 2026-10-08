"""
Phase 6 Statistical Analysis Module
Provides statistical functions for aggregating multi-seed trials:
- Mean, Median, Std, Min, Max
- 95% Confidence Intervals (Student-t / normal approximation)
- Effect size calculations (Cohen's d)
- Documented significance tests
"""

import math
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import stats


def calculate_distribution_stats(values: List[float], confidence: float = 0.95) -> Dict[str, float]:
    """
    Computes summary distribution metrics and parametric confidence intervals.
    If sample size n < 2, returns std=0 and CI bounds equal to mean.
    """
    if not values:
        return {
            "count": 0, "mean": 0.0, "median": 0.0, "std": 0.0,
            "min": 0.0, "max": 0.0, "ci_lower": 0.0, "ci_upper": 0.0
        }

    n = len(values)
    mean_val = float(np.mean(values))
    median_val = float(np.median(values))
    min_val = float(np.min(values))
    max_val = float(np.max(values))

    if n < 2:
        return {
            "count": n, "mean": mean_val, "median": median_val, "std": 0.0,
            "min": min_val, "max": max_val, "ci_lower": mean_val, "ci_upper": mean_val
        }

    std_val = float(np.std(values, ddof=1))
    sem = std_val / math.sqrt(n)

    # Student-t distribution critical value for two-tailed CI
    t_crit = float(stats.t.ppf((1.0 + confidence) / 2.0, df=n - 1))
    margin = t_crit * sem

    return {
        "count": n,
        "mean": mean_val,
        "median": median_val,
        "std": std_val,
        "min": min_val,
        "max": max_val,
        "ci_lower": float(mean_val - margin),
        "ci_upper": float(mean_val + margin)
    }


def compute_cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculates Cohen's d effect size between two independent groups:
    d = (mean1 - mean2) / s_pooled
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0

    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

    s_pooled = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if s_pooled <= 1e-12:
        return 0.0

    return float((mean1 - mean2) / s_pooled)


def perform_welch_ttest(group1: List[float], group2: List[float]) -> Dict[str, Any]:
    """
    Performs Welch's t-test (unequal variance two-sample test).
    Welch's t-test is appropriate because variances between honest and adversarial
    populations are not assumed to be equal.
    """
    if len(group1) < 2 or len(group2) < 2:
        return {"t_stat": 0.0, "p_value": 1.0, "note": "Insufficient sample size (n < 2)"}

    # If both groups have identical zero variance, avoid division by zero
    if np.var(group1) == 0.0 and np.var(group2) == 0.0:
        return {
            "t_stat": 0.0 if np.mean(group1) == np.mean(group2) else float("inf"),
            "p_value": 1.0 if np.mean(group1) == np.mean(group2) else 0.0,
            "note": "Zero variance in both sample distributions"
        }

    res = stats.ttest_ind(group1, group2, equal_var=False)
    return {
        "t_stat": float(res.statistic),
        "p_value": float(res.pvalue),
        "cohens_d": compute_cohens_d(group1, group2)
    }
