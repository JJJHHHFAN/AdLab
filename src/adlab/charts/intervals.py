"""A/B 测试比例和差值的置信区间图。"""

import plotly.graph_objects as go

from adlab.algorithms.ab_test import ABResult


def ab_interval_figure(result: ABResult) -> go.Figure:
    """并列展示主指标两组区间及 B 减 A 的差值区间。"""
    a_ci = result.a.ctr_ci if result.primary_metric == "ctr" else result.a.conversion_ci
    b_ci = result.b.ctr_ci if result.primary_metric == "ctr" else result.b.conversion_ci
    confidence = round((1 - result.alpha) * 100)

    figure = go.Figure()
    for label, rate, interval, color in (
        ("A 组", result.a_rate, a_ci, "#617986"),
        ("B 组", result.b_rate, b_ci, "#176B7A"),
    ):
        figure.add_trace(
            go.Scatter(
                x=[rate],
                y=[label],
                mode="markers",
                marker=dict(color=color, size=12),
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=[interval[1] - rate],
                    arrayminus=[rate - interval[0]],
                    color=color,
                    thickness=2,
                    width=8,
                ),
                name=label,
                hovertemplate=f"{label}: %{{x:.2%}}<extra></extra>",
            )
        )
    figure.update_layout(
        title=f"两组主指标及 {confidence}% Wilson 置信区间",
        template="plotly_white",
        height=250,
        showlegend=False,
        xaxis_tickformat=".1%",
        xaxis_title="每位随机分配用户的比例",
        margin=dict(l=24, r=24, t=55, b=30),
    )
    return figure


def difference_interval_figure(result: ABResult) -> go.Figure:
    """展示 B 减 A 的 Newcombe 差值区间与零差异参考线。"""
    lower, upper = result.diff_ci
    difference = result.absolute_diff
    figure = go.Figure(
        go.Scatter(
            x=[difference],
            y=["B − A"],
            mode="markers",
            marker=dict(color="#176B7A", size=13),
            error_x=dict(
                type="data",
                symmetric=False,
                array=[upper - difference],
                arrayminus=[difference - lower],
                color="#176B7A",
                thickness=2,
                width=8,
            ),
            hovertemplate="B − A: %{x:+.2%}<extra></extra>",
        )
    )
    figure.add_vline(x=0, line_dash="dash", line_color="#9AAAB3")
    figure.update_layout(
        title=f"主指标差值及 {round((1 - result.alpha) * 100)}% Newcombe 置信区间",
        template="plotly_white",
        height=220,
        showlegend=False,
        xaxis_tickformat="+.1%",
        xaxis_title="差值（百分点）",
        margin=dict(l=24, r=24, t=55, b=30),
    )
    return figure
