import math

import pytest

from adlab.algorithms.ab_test import (
    ABInput,
    Arm,
    analyze_ab,
    estimate_sample_size,
    prospective_power,
    wilson_interval,
)


def test_known_two_proportion_result_for_ctr():
    result = analyze_ab(ABInput(Arm(10_000, 400, 40), Arm(10_000, 460, 50), 14))
    assert result.a.ctr == pytest.approx(0.04)
    assert result.b.ctr == pytest.approx(0.046)
    assert result.absolute_diff == pytest.approx(0.006)
    assert result.relative_lift == pytest.approx(0.15)
    assert result.p_value == pytest.approx(0.036488361055898304, abs=1e-12)
    assert result.test_method == "pooled_z"
    assert result.significant
    assert result.a.cvr == pytest.approx(0.1)
    assert result.b.cvr == pytest.approx(50 / 460)


def test_small_sample_uses_fisher_exact_test():
    result = analyze_ab(ABInput(Arm(10, 0, 0), Arm(10, 5, 0), 7))
    assert result.test_method == "fisher_exact"
    assert result.p_value == pytest.approx(0.032507739938080496)
    assert result.a.cvr is None
    assert result.a.cvr_ci is None
    assert result.relative_lift is None


def test_zero_success_wilson_interval_has_nonzero_upper_bound():
    lower, upper = wilson_interval(0, 10, 0.05)
    assert lower == pytest.approx(0)
    assert upper == pytest.approx(0.27753279986288926)


def test_conversion_per_user_can_be_primary_metric():
    result = analyze_ab(
        ABInput(Arm(1_000, 100, 10), Arm(1_000, 100, 20), 14, primary_metric="conversion_per_user")
    )
    assert result.a_rate == pytest.approx(0.01)
    assert result.b_rate == pytest.approx(0.02)
    assert result.a.cvr == pytest.approx(0.1)
    assert result.b.cvr == pytest.approx(0.2)


@pytest.mark.parametrize(
    "arm",
    [Arm(0, 0, 0), Arm(10, 11, 0), Arm(10, 5, 6), Arm(10, -1, 0)],
)
def test_invalid_counts_are_rejected(arm):
    with pytest.raises(ValueError):
        analyze_ab(ABInput(arm, Arm(10, 1, 0), 7))


def test_invalid_experiment_configuration_is_rejected():
    with pytest.raises(ValueError):
        analyze_ab(ABInput(Arm(10, 1, 0), Arm(10, 2, 0), 0))
    with pytest.raises(ValueError):
        analyze_ab(ABInput(Arm(10, 1, 0), Arm(10, 2, 0), 7, alpha=1))
    with pytest.raises(ValueError):
        analyze_ab(ABInput(Arm(10, 1, 0), Arm(10, 2, 0), 7, primary_metric="cvr"))


def test_planned_sample_size_meets_target_power():
    n = estimate_sample_size(0.04, 0.006, alpha=0.05, target_power=0.8)
    assert isinstance(n, int) and n > 0
    assert prospective_power(n, 0.04, 0.006, alpha=0.05) >= 0.8
    assert prospective_power(n - 1, 0.04, 0.006, alpha=0.05) < 0.8


def test_identical_all_zero_groups_have_valid_p_value():
    result = analyze_ab(ABInput(Arm(20, 0, 0), Arm(20, 0, 0), 7))
    assert result.p_value == 1.0
    assert not result.significant
    assert math.isfinite(result.diff_ci[0]) and math.isfinite(result.diff_ci[1])
