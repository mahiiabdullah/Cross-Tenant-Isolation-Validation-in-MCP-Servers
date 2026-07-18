"""Statistical helpers used by the Phase-10 analysis pipeline.

Contract (per ``prompts/10_analysis.md``):

* :func:`welch_t`      — Welch's t-test → (t, p).
* :func:`cliffs_delta` — Cliff's δ non-parametric effect size.
* :func:`bonferroni`   — Bonferroni-adjust a list of p-values.
* :func:`cohens_d`     — Cohen's d effect size.

Helpers operate on plain ``list[float]`` inputs so they are
trivially callable from notebooks and tests alike.

The Welch test is delegated to ``scipy.stats.ttest_ind`` with
``equal_var=False``. Cliff's δ and Cohen's d are implemented
from scratch because the reference formulas are short and we
want zero scipy dependency for them (useful for unit tests).
"""

from __future__ import annotations

import math
import statistics
from typing import Sequence

from scipy import stats as scipy_stats


def _as_floats(xs: Sequence[float]) -> list[float]:
    out = [float(x) for x in xs]
    if len(out) < 2:
        raise ValueError(
            "stats helpers require at least two observations per group"
        )
    return out


def welch_t(a: Sequence[float], b: Sequence[float]) -> tuple[float, float]:
    """Welch's t-test for unequal-variance two-sample comparison.

    Returns ``(t_statistic, two_sided_p_value)``. If all values
    in either group are identical the variance is zero; we
    surface ``p = 1.0`` in that case to avoid NaNs (the caller's
    interpretation is "no evidence of difference").
    """
    a = _as_floats(a)
    b = _as_floats(b)
    # scipy returns NaN p-values when one group has zero variance.
    if statistics.pvariance(a) == 0.0 and statistics.pvariance(b) == 0.0:
        return 0.0, 1.0
    res = scipy_stats.ttest_ind(a, b, equal_var=False)
    t = float(res.statistic)  # type: ignore[attr-defined]
    p = float(res.pvalue)  # type: ignore[attr-defined]
    if math.isnan(t) or math.isnan(p):
        return 0.0, 1.0
    return t, p


def cliffs_delta(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute Cliff's δ ∈ [-1, +1].

    δ = (|{a_i > b_j}| − |{a_i < b_j}|) / (|a|·|b|).

    δ ≈ 0 indicates no effect; ±1 indicates perfect separation.
    """
    a = _as_floats(a)
    b = _as_floats(b)
    n_a, n_b = len(a), len(b)
    more = less = 0
    for x in a:
        for y in b:
            if x > y:
                more += 1
            elif x < y:
                less += 1
    return (more - less) / (n_a * n_b)


def bonferroni(pvals: Sequence[float]) -> list[float]:
    """Multiply each p-value by the number of tests, clip to 1.0."""
    n = len(pvals)
    if n == 0:
        return []
    return [min(1.0, float(p) * n) for p in pvals]


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Cohen's d effect size using pooled standard deviation."""
    a = _as_floats(a)
    b = _as_floats(b)
    mean_a = statistics.fmean(a)
    mean_b = statistics.fmean(b)
    var_a = statistics.pvariance(a)
    var_b = statistics.pvariance(b)
    pooled = math.sqrt(((len(a) - 1) * var_a + (len(b) - 1) * var_b) / (len(a) + len(b) - 2))
    if pooled == 0.0:
        return 0.0
    return (mean_a - mean_b) / pooled


def one_sided_z_proportion(
    successes: int, trials: int, p0: float
) -> tuple[float, float]:
    """One-sided z-test for a proportion against ``p0``.

    Returns ``(z_statistic, p_value)`` for the alternative
    ``successes/trials > p0``.

    Implementation uses ``scipy.stats.norm`` for the normal-CDF
    tail with a 0.5 continuity correction (the textbook-correct
    implementation for a discrete proportion test). The
    continuity correction is conservative: it shifts the
    effective threshold by 0.5/trials.
    """
    if trials <= 0:
        raise ValueError("trials must be positive")
    p_hat = successes / trials
    # Continuity-corrected numerator.
    numerator = (p_hat - p0) - (0.5 / trials)
    se = math.sqrt(p0 * (1 - p0) / trials)
    if se == 0:
        return 0.0, 1.0
    z = numerator / se
    # One-sided upper-tail p-value via scipy.stats.norm.sf.
    p = float(scipy_stats.norm.sf(z))
    return z, p


def sign_test(x: Sequence[float], median0: float = 0.0) -> float:
    """One-sided sign test that the median of ``x`` exceeds ``median0``.

    Returns the upper-tail p-value via
    ``scipy.stats.binomtest(successes, trials, 0.5,
    alternative='greater')``, where ``successes`` is the count of
    observations strictly above ``median0``. Ties (== ``median0``)
    are dropped from the count (a standard sign-test convention).
    """
    x = [float(v) - float(median0) for v in x]
    pos = sum(1 for v in x if v > 0)
    neg = sum(1 for v in x if v < 0)
    n = pos + neg
    if n == 0:
        return 1.0
    res = scipy_stats.binomtest(pos, n, 0.5, alternative="greater")
    return float(res.pvalue)


__all__ = [
    "bonferroni",
    "cliffs_delta",
    "cohens_d",
    "one_sided_z_proportion",
    "sign_test",
    "welch_t",
]
