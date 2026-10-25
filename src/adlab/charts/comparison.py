"""用于并列比较数值的通用图表。"""

from collections.abc import Sequence

import plotly.graph_objects as go


def comparison_bar(
    labels: Sequence[str], values: Sequence[float], *, title: str, unit: str = ""
) -> go.Figure:
    """返回可复用图表，图表不推断数据的业务含义。"""
    if len(labels) != len(values) or not labels:
        raise ValueError("标签和值必须非空且数量相同")

    figure = go.Figure(
        go.Bar(
            x=list(labels),
            y=list(values),
            marker_color="#176B7A",
            hovertemplate=f"%{{x}}<br>%{{y:.3g}}{unit}<extra></extra>",
        )
    )
    figure.update_layout(
        title=title,
        template="plotly_white",
        height=340,
        margin=dict(l=24, r=24, t=58, b=30),
        yaxis_title=unit,
        font=dict(family="Arial, sans-serif", color="#173143"),
        showlegend=False,
    )
    return figure
