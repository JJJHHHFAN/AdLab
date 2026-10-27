"""预算分配实验的策略对比图。"""

import plotly.graph_objects as go

from adlab.algorithms.budget import BudgetComparison


def allocation_figure(results: BudgetComparison) -> go.Figure:
    """显示每个计划在规则法和线性规划下获得的周期预算。"""
    labels = [item.campaign_id for item in results.rule.allocations]
    figure = go.Figure()
    for outcome, name, color in (
        (results.rule, "规则分配", "#7A98A0"),
        (results.optimized, "线性规划", "#176B7A"),
    ):
        figure.add_trace(
            go.Bar(x=labels, y=[item.spend for item in outcome.allocations], name=name, marker_color=color)
        )
    figure.update_layout(
        title="各计划预算分配", barmode="group", template="plotly_white", height=380,
        margin=dict(l=24, r=24, t=58, b=40), xaxis_title="广告计划", yaxis_title="预算（抽象货币单位）",
        font=dict(family="Arial, sans-serif", color="#173143"),
        legend=dict(orientation="h", y=-0.25),
    )
    return figure
