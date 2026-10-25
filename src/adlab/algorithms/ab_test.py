"""两组独立随机分配用户的比例检验与实验前样本量规划。"""

from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from typing import Literal

from scipy.stats import fisher_exact, norm


PrimaryMetric = Literal["ctr", "conversion_per_user"]
Interval = tuple[float, float]


@dataclass(frozen=True)
class Arm:
    users: int
    clicks: int
    conversions: int


@dataclass(frozen=True)
class ABInput:
    a: Arm
    b: Arm
    duration_days: int
    alpha: float = 0.05
    primary_metric: PrimaryMetric = "ctr"


@dataclass(frozen=True)
class ArmSummary:
    ctr: float
    cvr: float | None
    conversion_per_user: float
    ctr_ci: Interval
    cvr_ci: Interval | None
    conversion_ci: Interval


@dataclass(frozen=True)
class ABResult:
    a: ArmSummary
    b: ArmSummary
    primary_metric: PrimaryMetric
    a_rate: float
    b_rate: float
    absolute_diff: float
    relative_lift: float | None
    diff_ci: Interval
    test_method: Literal["pooled_z", "fisher_exact"]
    statistic: float | None
    p_value: float
    significant: bool
    alpha: float
    duration_days: int


def _validate_arm(arm: Arm) -> None:
    counts = (arm.users, arm.clicks, arm.conversions)
    if any(isinstance(value, bool) or not isinstance(value, int) for value in counts):
        raise ValueError("人数必须为整数")
    if not 0 <= arm.conversions <= arm.clicks <= arm.users or arm.users == 0:
        raise ValueError("必须满足 0 ≤ 转化人数 ≤ 点击人数 ≤ 独立用户数，且用户数大于 0")


def _validate_probability(value: float, name: str) -> None:
    if not isfinite(value) or not 0 < value < 1:
        raise ValueError(f"{name} 必须在 0 和 1 之间")


def wilson_interval(successes: int, trials: int, alpha: float = 0.05) -> Interval:
    """独立二项比例的双侧 Wilson 得分区间。"""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("成功次数必须介于 0 和正的试验次数之间")
    _validate_probability(alpha, "显著性水平")
    p = successes / trials
    z = norm.ppf(1 - alpha / 2)
    z2 = z * z
    denominator = 1 + z2 / trials
    center = (p + z2 / (2 * trials)) / denominator
    half = z * sqrt(p * (1 - p) / trials + z2 / (4 * trials * trials)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def _newcombe_difference(a: Arm, b: Arm, alpha: float, metric: PrimaryMetric) -> Interval:
    xa = a.clicks if metric == "ctr" else a.conversions
    xb = b.clicks if metric == "ctr" else b.conversions
    pa, pb = xa / a.users, xb / b.users
    la, ua = wilson_interval(xa, a.users, alpha)
    lb, ub = wilson_interval(xb, b.users, alpha)
    difference = pb - pa
    lower = difference - sqrt((pb - lb) ** 2 + (ua - pa) ** 2)
    upper = difference + sqrt((ub - pb) ** 2 + (pa - la) ** 2)
    return max(-1.0, lower), min(1.0, upper)


def _summarize(arm: Arm, alpha: float) -> ArmSummary:
    return ArmSummary(
        ctr=arm.clicks / arm.users,
        cvr=arm.conversions / arm.clicks if arm.clicks else None,
        conversion_per_user=arm.conversions / arm.users,
        ctr_ci=wilson_interval(arm.clicks, arm.users, alpha),
        cvr_ci=wilson_interval(arm.conversions, arm.clicks, alpha) if arm.clicks else None,
        conversion_ci=wilson_interval(arm.conversions, arm.users, alpha),
    )


def analyze_ab(inputs: ABInput) -> ABResult:
    """分析一个预先选定主指标的 A/B 实验；p 值均为双侧。"""
    _validate_arm(inputs.a)
    _validate_arm(inputs.b)
    if isinstance(inputs.duration_days, bool) or not isinstance(inputs.duration_days, int) or inputs.duration_days <= 0:
        raise ValueError("实验周期必须是正整数天")
    _validate_probability(inputs.alpha, "显著性水平")
    if inputs.primary_metric not in ("ctr", "conversion_per_user"):
        raise ValueError("主指标只能选择 CTR 或每用户转化率")

    xa = inputs.a.clicks if inputs.primary_metric == "ctr" else inputs.a.conversions
    xb = inputs.b.clicks if inputs.primary_metric == "ctr" else inputs.b.conversions
    na, nb = inputs.a.users, inputs.b.users
    pa, pb = xa / na, xb / nb
    pooled = (xa + xb) / (na + nb)
    expected = (na * pooled, nb * pooled, na * (1 - pooled), nb * (1 - pooled))

    if pooled in (0.0, 1.0):
        method = "fisher_exact"
        statistic = None
        p_value = 1.0
    elif min(expected) < 5:
        method = "fisher_exact"
        statistic = None
        p_value = float(fisher_exact([[xa, na - xa], [xb, nb - xb]], alternative="two-sided").pvalue)
    else:
        method = "pooled_z"
        statistic = (pb - pa) / sqrt(pooled * (1 - pooled) * (1 / na + 1 / nb))
        p_value = float(2 * norm.sf(abs(statistic)))

    return ABResult(
        a=_summarize(inputs.a, inputs.alpha),
        b=_summarize(inputs.b, inputs.alpha),
        primary_metric=inputs.primary_metric,
        a_rate=pa,
        b_rate=pb,
        absolute_diff=pb - pa,
        relative_lift=(pb - pa) / pa if pa else None,
        diff_ci=_newcombe_difference(inputs.a, inputs.b, inputs.alpha, inputs.primary_metric),
        test_method=method,
        statistic=statistic,
        p_value=p_value,
        significant=p_value < inputs.alpha,
        alpha=inputs.alpha,
        duration_days=inputs.duration_days,
    )


def _validate_planning(baseline_rate: float, mde: float, alpha: float) -> float:
    _validate_probability(baseline_rate, "基线率")
    _validate_probability(alpha, "显著性水平")
    if not isfinite(mde) or mde <= 0 or baseline_rate + mde >= 1:
        raise ValueError("最小可检测差异必须大于 0，且基线率加差异小于 1")
    return baseline_rate + mde


def prospective_power(n_per_group: int, baseline_rate: float, mde: float, alpha: float = 0.05) -> float:
    """双侧两样本比例 z 检验在假定效应下的事前近似功效。"""
    p2 = _validate_planning(baseline_rate, mde, alpha)
    if isinstance(n_per_group, bool) or not isinstance(n_per_group, int) or n_per_group <= 0:
        raise ValueError("每组样本量必须为正整数")
    pooled = (baseline_rate + p2) / 2
    null_sd = sqrt(2 * pooled * (1 - pooled) / n_per_group)
    alternative_sd = sqrt((baseline_rate * (1 - baseline_rate) + p2 * (1 - p2)) / n_per_group)
    critical = norm.ppf(1 - alpha / 2) * null_sd
    return float(norm.sf((critical - mde) / alternative_sd) + norm.cdf((-critical - mde) / alternative_sd))


def estimate_sample_size(
    baseline_rate: float, mde: float, *, alpha: float = 0.05, target_power: float = 0.8
) -> int:
    """返回每组所需独立用户数；正态近似，不含连续性校正。"""
    p2 = _validate_planning(baseline_rate, mde, alpha)
    _validate_probability(target_power, "目标功效")
    pooled = (baseline_rate + p2) / 2
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(target_power)
    numerator = (
        z_alpha * sqrt(2 * pooled * (1 - pooled))
        + z_power * sqrt(baseline_rate * (1 - baseline_rate) + p2 * (1 - p2))
    ) ** 2
    n = max(1, ceil(numerator / (mde * mde)))
    while prospective_power(n, baseline_rate, mde, alpha) < target_power:
        n += 1
    while n > 1 and prospective_power(n - 1, baseline_rate, mde, alpha) >= target_power:
        n -= 1
    return n
