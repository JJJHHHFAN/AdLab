"""实验目录是导航、首页和未来实验配置的共同来源。"""

from dataclasses import dataclass
from typing import Literal


Status = Literal["available", "planned"]


@dataclass(frozen=True)
class Experiment:
    slug: str
    title: str
    english_title: str
    summary: str
    stage: int
    status: Status


EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment("home", "首页", "Overview", "从实验理解计算广告的核心机制。", 1, "available"),
    Experiment("auction", "广告竞价", "Ad Auctions", "比较出价、排名与支付规则。", 3, "available"),
    Experiment("ctr", "CTR 预测", "Click-Through Rate", "学习数据划分、概率预测与校准。", 4, "available"),
    Experiment("budget", "预算优化", "Budget Allocation", "在约束条件下分配广告计划预算。", 5, "available"),
    Experiment("ab_test", "A/B 测试", "A/B Testing", "分析比例差异、区间和统计功效。", 2, "available"),
    Experiment("bandit", "多臂老虎机", "Multi-Armed Bandits", "观察探索与利用之间的权衡。", 6, "planned"),
    Experiment("records", "实验记录", "Experiment History", "回顾保存的输入、配置与实验结果。", 2, "available"),
    Experiment("docs", "学习文档", "Learning Notes", "阅读公式、计算示例和延伸资料。", 2, "available"),
)


def get_experiment(slug: str) -> Experiment:
    """按稳定标识查找实验；未知标识会引发 KeyError。"""
    for experiment in EXPERIMENTS:
        if experiment.slug == slug:
            return experiment
    raise KeyError(slug)
