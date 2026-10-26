"""CTR 测试集概率表现的 Plotly 图表。"""

import numpy as np
import plotly.graph_objects as go
from sklearn.calibration import calibration_curve
from sklearn.metrics import roc_curve


def _style(figure: go.Figure, title: str, x_label: str, y_label: str) -> go.Figure:
    figure.update_layout(
        title=title,
        template="plotly_white",
        height=360,
        margin=dict(l=24, r=24, t=58, b=35),
        xaxis_title=x_label,
        yaxis_title=y_label,
        font=dict(family="Arial, sans-serif", color="#173143"),
        legend=dict(orientation="h", y=-0.25),
    )
    return figure


def roc_figure(labels: np.ndarray, probabilities: np.ndarray) -> go.Figure:
    false_positive_rate, true_positive_rate, _ = roc_curve(labels, probabilities)
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=false_positive_rate, y=true_positive_rate, mode="lines", name="模型", line=dict(color="#176B7A", width=3)))
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="随机基线", line=dict(color="#9BA9AD", dash="dash")))
    return _style(figure, "测试集 ROC 曲线", "假阳性率", "真阳性率")


def probability_figure(labels: np.ndarray, probabilities: np.ndarray) -> go.Figure:
    figure = go.Figure()
    for label, name, color in ((0, "未点击", "#9BA9AD"), (1, "点击", "#176B7A")):
        figure.add_trace(
            go.Histogram(
                x=probabilities[labels == label], name=name, marker_color=color,
                xbins=dict(start=0, end=1, size=0.05), histnorm="probability density", opacity=0.7,
            )
        )
    figure.update_layout(barmode="overlay")
    return _style(figure, "测试集预测概率分布", "预测点击概率", "各类别内的概率密度")


def calibration_figure(labels: np.ndarray, probabilities: np.ndarray) -> go.Figure:
    observed, predicted = calibration_curve(labels, probabilities, n_bins=8, strategy="quantile")
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=predicted, y=observed, mode="lines+markers", name="模型", line=dict(color="#176B7A", width=3)))
    figure.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="完全校准", line=dict(color="#9BA9AD", dash="dash")))
    return _style(figure, "测试集概率校准图", "平均预测概率", "实际点击比例")
