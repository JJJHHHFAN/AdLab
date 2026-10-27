"""固定周期内的教学预算分配、线性规划与随机结果模拟。"""

from dataclasses import dataclass
from math import isfinite
from typing import Literal

import numpy as np
from scipy.optimize import linprog


Objective = Literal["conversions", "revenue", "target_cpa"]
Strategy = Literal["rule", "optimized"]
MAX_BUDGET = 1e9
MAX_CPA = 1e6
MAX_ROAS = 1e3
TOLERANCE = 1e-7


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    cpa: float
    roas: float
    min_spend: float
    max_spend: float


@dataclass(frozen=True)
class BudgetRequest:
    total_budget: float
    campaigns: tuple[Campaign, ...]
    objective: Objective
    target_cpa: float | None = None
    seed: int = 42


@dataclass(frozen=True)
class PlanAllocation:
    campaign_id: str
    spend: float
    predicted_conversions: float
    predicted_revenue: float
    simulated_conversions: int
    simulated_revenue: float


@dataclass(frozen=True)
class BudgetOutcome:
    strategy: Strategy
    allocations: tuple[PlanAllocation, ...]
    total_spend: float
    unspent_budget: float
    predicted_conversions: float
    predicted_revenue: float
    predicted_cpa: float | None
    predicted_roas: float | None
    simulated_conversions: int
    simulated_revenue: float
    simulated_cpa: float | None
    simulated_roas: float | None


@dataclass(frozen=True)
class BudgetComparison:
    rule: BudgetOutcome
    optimized: BudgetOutcome


def _number(value: float, name: str, minimum: float, maximum: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{name} 必须是有限数字")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} 必须介于 {minimum:g} 与 {maximum:g} 之间")


def _validate(request: BudgetRequest) -> None:
    _number(request.total_budget, "总预算", 0.01, MAX_BUDGET)
    if not request.campaigns:
        raise ValueError("至少需要一个广告计划")
    if request.objective not in ("conversions", "revenue", "target_cpa"):
        raise ValueError("未知优化目标")
    if isinstance(request.seed, bool) or not isinstance(request.seed, int) or not 0 <= request.seed < 2**32:
        raise ValueError("随机种子必须是 0 至 2³²−1 的整数")
    if request.objective == "target_cpa":
        if request.target_cpa is None:
            raise ValueError("目标 CPA 模式需要设置目标值")
        _number(request.target_cpa, "目标 CPA", 0.01, MAX_CPA)

    ids: set[str] = set()
    for campaign in request.campaigns:
        if not isinstance(campaign.campaign_id, str) or not campaign.campaign_id.strip():
            raise ValueError("计划 ID 不能为空")
        if campaign.campaign_id in ids:
            raise ValueError("计划 ID 必须唯一")
        ids.add(campaign.campaign_id)
        _number(campaign.cpa, f"{campaign.campaign_id} 的 CPA", 0.01, MAX_CPA)
        _number(campaign.roas, f"{campaign.campaign_id} 的 ROAS", 0, MAX_ROAS)
        _number(campaign.min_spend, f"{campaign.campaign_id} 的最低投放", 0, MAX_BUDGET)
        _number(campaign.max_spend, f"{campaign.campaign_id} 的预算上限", 0, MAX_BUDGET)
        if campaign.min_spend > campaign.max_spend:
            raise ValueError(f"{campaign.campaign_id} 的最低投放不能超过预算上限")
    if sum(campaign.min_spend for campaign in request.campaigns) > request.total_budget + TOLERANCE:
        raise ValueError("各计划最低投放之和超过总预算")


def _rule_allocation(request: BudgetRequest) -> np.ndarray:
    campaigns = request.campaigns
    spend = np.array([campaign.min_spend for campaign in campaigns], dtype=float)
    caps = np.array([campaign.max_spend for campaign in campaigns], dtype=float)
    cpas = np.array([campaign.cpa for campaign in campaigns], dtype=float)
    remaining = request.total_budget - float(spend.sum())

    if request.objective == "target_cpa":
        coefficients = 1 - float(request.target_cpa) / cpas
        for index in np.argsort(cpas, kind="stable"):
            room = min(caps[index] - spend[index], remaining)
            if coefficients[index] > 0:
                slack = -float(coefficients @ spend)
                room = min(room, max(0.0, slack / coefficients[index]))
            addition = max(0.0, room)
            spend[index] += addition
            remaining -= addition
        if float(coefficients @ spend) > TOLERANCE or float(spend.sum()) <= TOLERANCE:
            raise ValueError("规则法找不到满足目标 CPA 的正投放方案")
        return spend

    scores = 1 / cpas if request.objective == "conversions" else np.array(
        [campaign.roas for campaign in campaigns], dtype=float
    )
    while remaining > TOLERANCE:
        room = np.maximum(0, caps - spend)
        active = room > TOLERANCE
        if not active.any():
            break
        weights = np.where(active, scores, 0.0)
        if not weights.any():
            weights = active.astype(float)
        addition = np.minimum(room, remaining * weights / weights.sum())
        applied = float(addition.sum())
        if applied <= TOLERANCE:
            break
        spend += addition
        remaining -= applied
    return spend


def _optimal_allocation(request: BudgetRequest) -> np.ndarray:
    cpas = np.array([campaign.cpa for campaign in request.campaigns], dtype=float)
    roas = np.array([campaign.roas for campaign in request.campaigns], dtype=float)
    objective = -roas if request.objective == "revenue" else -1 / cpas
    inequalities = [np.ones(len(cpas))]
    limits = [request.total_budget]
    if request.objective == "target_cpa":
        inequalities.append(1 - float(request.target_cpa) / cpas)
        limits.append(0.0)
    result = linprog(
        c=objective,
        A_ub=np.array(inequalities),
        b_ub=np.array(limits),
        bounds=[(campaign.min_spend, campaign.max_spend) for campaign in request.campaigns],
        method="highs",
    )
    if not result.success:
        raise ValueError("预算、上下限与目标 CPA 约束没有可行解")
    spend = np.where(np.abs(result.x) < 1e-9, 0.0, result.x)
    if request.objective == "target_cpa" and float(np.sum(spend / cpas)) <= TOLERANCE:
        raise ValueError("目标 CPA 下只有零投放解，无法定义整体 CPA")
    return spend


def _summarize(request: BudgetRequest, spend: np.ndarray, strategy: Strategy) -> BudgetOutcome:
    cpas = np.array([campaign.cpa for campaign in request.campaigns], dtype=float)
    roas = np.array([campaign.roas for campaign in request.campaigns], dtype=float)
    predicted_conversions = spend / cpas
    predicted_revenue = spend * roas
    # 两种策略分别从相同种子重新开始；相同分配会得到相同模拟值。
    simulated_conversions = np.random.default_rng(request.seed).poisson(predicted_conversions)
    simulated_revenue = simulated_conversions * cpas * roas
    allocations = tuple(
        PlanAllocation(
            campaign_id=campaign.campaign_id,
            spend=float(spend[index]),
            predicted_conversions=float(predicted_conversions[index]),
            predicted_revenue=float(predicted_revenue[index]),
            simulated_conversions=int(simulated_conversions[index]),
            simulated_revenue=float(simulated_revenue[index]),
        )
        for index, campaign in enumerate(request.campaigns)
    )
    total_spend = float(spend.sum())
    total_predicted_conversions = float(predicted_conversions.sum())
    total_predicted_revenue = float(predicted_revenue.sum())
    total_simulated_conversions = int(simulated_conversions.sum())
    total_simulated_revenue = float(simulated_revenue.sum())
    return BudgetOutcome(
        strategy=strategy,
        allocations=allocations,
        total_spend=total_spend,
        unspent_budget=max(0.0, request.total_budget - total_spend),
        predicted_conversions=total_predicted_conversions,
        predicted_revenue=total_predicted_revenue,
        predicted_cpa=total_spend / total_predicted_conversions if total_predicted_conversions else None,
        predicted_roas=total_predicted_revenue / total_spend if total_spend else None,
        simulated_conversions=total_simulated_conversions,
        simulated_revenue=total_simulated_revenue,
        simulated_cpa=total_spend / total_simulated_conversions if total_simulated_conversions else None,
        simulated_roas=total_simulated_revenue / total_spend if total_spend else None,
    )


def run_budget_experiment(request: BudgetRequest) -> BudgetComparison:
    """比较规则法与线性规划；模拟值仅为一次随机示例。"""
    _validate(request)
    rule_spend = _rule_allocation(request)
    optimized_spend = _optimal_allocation(request)
    return BudgetComparison(
        rule=_summarize(request, rule_spend, "rule"),
        optimized=_summarize(request, optimized_spend, "optimized"),
    )
