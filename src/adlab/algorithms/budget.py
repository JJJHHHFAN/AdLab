"""固定周期内的教学预算分配、线性规划与随机结果模拟。"""

from dataclasses import dataclass
from decimal import Decimal
from math import fsum, isfinite, ulp
from typing import Literal

import numpy as np
from scipy.optimize import linprog


Objective = Literal["conversions", "revenue", "target_cpa"]
Strategy = Literal["rule", "optimized"]
MAX_BUDGET = 1e9
MAX_CPA = 1e6
MAX_ROAS = 1e3


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
    if sum(Decimal(str(campaign.min_spend)) for campaign in request.campaigns) > Decimal(
        str(request.total_budget)
    ):
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
        total_spend = float(spend.sum())
        conversions = float(np.sum(spend / cpas))
        if conversions == 0 or total_spend / conversions > float(request.target_cpa) * (1 + 1e-7):
            raise ValueError("规则法找不到满足目标 CPA 的正投放方案")
        return spend

    scores = 1 / cpas if request.objective == "conversions" else np.array(
        [campaign.roas for campaign in campaigns], dtype=float
    )
    while remaining > 0:
        room = np.maximum(0, caps - spend)
        active = room > 0
        if not active.any():
            break
        weights = np.where(active, scores, 0.0)
        if not weights.any():
            weights = active.astype(float)
        addition = np.minimum(room, remaining * weights / weights.sum())
        new_spend = np.minimum(caps, spend + addition)
        applied = float((new_spend - spend).sum())
        if applied <= 0:
            break
        spend = new_spend
        remaining = max(0.0, request.total_budget - float(spend.sum()))
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
    spend = np.maximum(result.x, 0.0)
    if request.objective == "target_cpa":
        conversions = float(np.sum(spend / cpas))
        if conversions == 0:
            raise ValueError("目标 CPA 下只有零投放解，无法定义整体 CPA")
        if float(spend.sum()) / conversions > float(request.target_cpa) * (1 + 1e-7):
            raise ValueError("求解结果未满足整体预测目标 CPA，请调整输入范围")
    return spend


def _normalize_allocation(request: BudgetRequest, spend: np.ndarray) -> np.ndarray:
    """只修正浮点舍入误差；真正违反预算或上下限时拒绝结果。"""
    spend = spend.copy()
    budget_tolerance = 8 * len(spend) * ulp(max(1.0, request.total_budget))
    for index, campaign in enumerate(request.campaigns):
        limit = 8 * ulp(max(1.0, campaign.max_spend))
        if spend[index] < campaign.min_spend - limit or spend[index] > campaign.max_spend + limit:
            raise ValueError("分配结果未满足单计划预算上下限，请调整输入范围")
        spend[index] = min(campaign.max_spend, max(campaign.min_spend, spend[index]))

    excess = fsum(float(value) for value in spend) - request.total_budget
    if excess > budget_tolerance:
        raise ValueError("分配结果超过总预算，请调整输入范围")
    if excess > 0:
        # 优先削减高 CPA 计划；每次重算，以免一次浮点减法后仍超出一 ULP。
        for index in sorted(range(len(spend)), key=lambda i: request.campaigns[i].cpa, reverse=True):
            room = spend[index] - request.campaigns[index].min_spend
            if room <= 0:
                continue
            spend[index] = max(request.campaigns[index].min_spend, spend[index] - min(excess, room))
            excess = fsum(float(value) for value in spend) - request.total_budget
            if excess <= 0:
                break
    return spend


def _summarize(request: BudgetRequest, spend: np.ndarray, strategy: Strategy) -> BudgetOutcome:
    spend = _normalize_allocation(request, spend)
    cpas = np.array([campaign.cpa for campaign in request.campaigns], dtype=float)
    roas = np.array([campaign.roas for campaign in request.campaigns], dtype=float)
    predicted_conversions = spend / cpas
    if request.objective == "target_cpa":
        conversions = float(np.sum(predicted_conversions))
        if conversions == 0 or float(spend.sum()) / conversions > float(request.target_cpa) * (1 + 1e-7):
            raise ValueError("分配结果未满足整体预测目标 CPA，请调整输入范围")
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
    total_spend = min(request.total_budget, fsum(float(value) for value in spend))
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
