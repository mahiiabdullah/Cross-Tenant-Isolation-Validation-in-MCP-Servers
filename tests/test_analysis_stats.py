"""Unit tests for ``analysis.scripts.stats``."""

from __future__ import annotations

import math

import pytest

from analysis.scripts.stats import (
    bonferroni,
    cliffs_delta,
    cohens_d,
    one_sided_z_proportion,
    sign_test,
    welch_t,
)


def test_welch_t_equal_samples_nonsignificant() -> None:
    t, p = welch_t([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert t == 0.0
    assert p == 1.0


def test_welch_t_distinct_distributions_significant() -> None:
    t, p = welch_t([10.0, 11.0, 12.0, 13.0, 14.0], [1.0, 2.0, 3.0, 4.0, 5.0])
    assert t > 5.0  # large t-statistic for this gap
    assert p < 0.001


def test_welch_t_zero_variance_both_groups() -> None:
    t, p = welch_t([5.0, 5.0, 5.0], [5.0, 5.0, 5.0])
    assert t == 0.0 and p == 1.0


def test_welch_t_requires_two_observations() -> None:
    with pytest.raises(ValueError):
        welch_t([1.0], [1.0, 2.0])


def test_cliffs_delta_identical_samples() -> None:
    assert cliffs_delta([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0


def test_cliffs_delta_disjoint_samples_high() -> None:
    a = [10.0, 11.0, 12.0]
    b = [1.0, 2.0, 3.0]
    assert cliffs_delta(a, b) == pytest.approx(1.0)


def test_cliffs_delta_disjoint_samples_low() -> None:
    a = [1.0, 2.0, 3.0]
    b = [10.0, 11.0, 12.0]
    assert cliffs_delta(a, b) == pytest.approx(-1.0)


def test_bonferroni_clamps_to_one() -> None:
    # Two p-values close to 1 → 2.0 → clipped to 1.0.
    assert bonferroni([0.6, 0.6]) == [1.0, 1.0]


def test_bonferroni_scales_below_one() -> None:
    # Three p-values of 0.01 → 0.03.
    out = bonferroni([0.01, 0.01, 0.01])
    assert out == pytest.approx([0.03, 0.03, 0.03])


def test_bonferroni_empty_list() -> None:
    assert bonferroni([]) == []


def test_cohens_d_manual_reference() -> None:
    # a = [1, 2, 3]  → mean 2, var 2/3
    # b = [4, 5, 6]  → mean 5, var 2/3
    # pooled std = sqrt((2*2/3 + 2*2/3)/4) = sqrt(2/3)
    # d = (2 − 5) / sqrt(2/3)
    a = [1.0, 2.0, 3.0]
    b = [4.0, 5.0, 6.0]
    expected = -3.0 / math.sqrt(2.0 / 3.0)
    assert cohens_d(a, b) == pytest.approx(expected)


def test_cohens_d_zero_pooled_std() -> None:
    assert cohens_d([1.0, 1.0, 1.0], [1.0, 1.0, 1.0]) == 0.0


def test_one_sided_z_proportion_extreme() -> None:
    # 100/100 successes with H0 p0=0.5 → uncorrected z = 10.0;
    # with 0.5 continuity correction the z shifts to 9.9.
    z, p = one_sided_z_proportion(100, 100, 0.5)
    assert z == pytest.approx(9.9, abs=1e-9)
    assert p < 1e-10


def test_one_sided_z_proportion_no_evidence() -> None:
    # 50/100 at p0=0.5 → uncorrected z ≈ 0; continuity correction
    # shifts the numerator to (0 − 0.5/100) = −0.005; with
    # SE = sqrt(0.25 / 100) = 0.05, z = −0.1.
    z, p = one_sided_z_proportion(50, 100, 0.5)
    assert z == pytest.approx(-0.1, abs=1e-9)
    assert p == pytest.approx(0.5398, abs=1e-3)


def test_one_sided_z_proportion_invalid() -> None:
    with pytest.raises(ValueError):
        one_sided_z_proportion(10, 0, 0.5)


def test_sign_test_all_above() -> None:
    # Every observation exceeds the median → p = 0.5^n.
    p = sign_test([0.6, 0.7, 0.8, 0.9, 1.0], median0=0.5)
    # 5 of 5 strictly above the median → binom(5,5,0.5) = 0.03125.
    assert p == pytest.approx(0.03125)


def test_sign_test_all_below() -> None:
    # Every observation below the median → p = 1.0.
    p = sign_test([0.1, 0.2, 0.3, 0.4], median0=0.5)
    assert p == pytest.approx(1.0)


def test_sign_test_mixed() -> None:
    # 3 above, 2 below, out of 5 nonzero → binomial(3, 5, 0.5).
    p = sign_test([0.6, 0.7, 0.4, 0.3, 0.8], median0=0.5)
    # scipy.stats.binomtest(3, 5, 0.5, alternative='greater') = 0.5.
    assert p == pytest.approx(0.5)


def test_sign_test_all_ties() -> None:
    # All observations equal the median → no information → p = 1.0.
    p = sign_test([0.5, 0.5, 0.5], median0=0.5)
    assert p == pytest.approx(1.0)
