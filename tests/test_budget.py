import math

import pytest

from adlab.algorithms.budget import BudgetRequest, Campaign, run_budget_experiment


@pytest.fixture
def campaigns():
    return (
        Campaign("A", cpa=10, roas=2, min_spend=10, max_spend=60),
        Campaign("B", cpa=20, roas=5, min_spend=10, max_spend=70),
        Campaign("C", cpa=50, roas=1, min_spend=0, max_spend=50),
    )


def _spends(outcome):
    return {item.campaign_id: item.spend for item in outcome.allocations}


@pytest.mark.parametrize("objective", ["conversions", "revenue", "target_cpa"])
def test_both_strategies_respect_budget_bounds_and_objective(campaigns, objective):
    request = BudgetRequest(100, campaigns, objective, target_cpa=12 if objective == "target_cpa" else None, seed=7)
    result = run_budget_experiment(request)
    for outcome in (result.rule, result.optimized):
        assert outcome.total_spend <= 100 + 1e-7
        assert outcome.unspent_budget >= -1e-7
        for item, campaign in zip(outcome.allocations, campaigns):
            assert campaign.min_spend - 1e-7 <= item.spend <= campaign.max_spend + 1e-7
            assert item.predicted_conversions == pytest.approx(item.spend / campaign.cpa)
            assert item.predicted_revenue == pytest.approx(item.spend * campaign.roas)
        if objective == "target_cpa":
            assert outcome.predicted_cpa <= 12 + 1e-7
    if objective == "revenue":
        assert result.optimized.predicted_revenue >= result.rule.predicted_revenue - 1e-7
    else:
        assert result.optimized.predicted_conversions >= result.rule.predicted_conversions - 1e-7


def test_conversion_objective_has_known_linear_program_solution(campaigns):
    result = run_budget_experiment(BudgetRequest(100, campaigns, "conversions", seed=7))
    assert _spends(result.optimized) == pytest.approx({"A": 60, "B": 40, "C": 0})
    assert result.optimized.predicted_conversions == pytest.approx(8)
    assert result.rule.predicted_conversions < 8


def test_revenue_objective_has_known_linear_program_solution(campaigns):
    result = run_budget_experiment(BudgetRequest(100, campaigns, "revenue", seed=7))
    assert _spends(result.optimized) == pytest.approx({"A": 30, "B": 70, "C": 0})
    assert result.optimized.predicted_revenue == pytest.approx(410)
    assert result.rule.predicted_revenue < 410


def test_target_cpa_constraint_may_leave_budget_unspent(campaigns):
    result = run_budget_experiment(BudgetRequest(100, campaigns, "target_cpa", target_cpa=12, seed=7))
    assert _spends(result.optimized) == pytest.approx({"A": 60, "B": 30, "C": 0})
    assert result.optimized.total_spend == pytest.approx(90)
    assert result.optimized.predicted_cpa == pytest.approx(12)
    assert result.optimized.unspent_budget == pytest.approx(10)


def test_total_plan_caps_can_leave_budget_unspent(campaigns):
    result = run_budget_experiment(BudgetRequest(200, campaigns, "conversions", seed=7))
    assert result.optimized.total_spend == pytest.approx(180)
    assert result.optimized.unspent_budget == pytest.approx(20)


def test_simulated_realization_is_reproducible_and_separate_from_prediction(campaigns):
    request = BudgetRequest(100, campaigns, "conversions", seed=31)
    first = run_budget_experiment(request)
    second = run_budget_experiment(request)
    assert first == second
    assert isinstance(first.optimized.simulated_conversions, int)
    assert first.optimized.predicted_conversions == pytest.approx(8)
    assert first.optimized.simulated_revenue == pytest.approx(
        sum(item.simulated_conversions * campaign.cpa * campaign.roas
            for item, campaign in zip(first.optimized.allocations, campaigns))
    )


@pytest.mark.parametrize(
    "bad_request",
    [
        BudgetRequest(10, (Campaign("A", 10, 2, 8, 10), Campaign("B", 20, 3, 8, 10)), "conversions"),
        BudgetRequest(100, (Campaign("A", 0, 2, 0, 50),), "conversions"),
        BudgetRequest(100, (Campaign("A", 10, 2, 60, 50),), "conversions"),
        BudgetRequest(100, (Campaign("A", 10, 2, 0, 50), Campaign("A", 20, 3, 0, 50)), "conversions"),
        BudgetRequest(100, (Campaign("A", math.nan, 2, 0, 50),), "conversions"),
        BudgetRequest(100, (Campaign("A", 10, 2, 0, 50),), "target_cpa", target_cpa=5),
    ],
)
def test_invalid_or_infeasible_requests_are_rejected(bad_request):
    with pytest.raises(ValueError):
        run_budget_experiment(bad_request)
