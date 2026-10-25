"""页面和实验记录共用的统计结果显示格式。"""


def format_p_value(value: float) -> str:
    """避免把非零的极小 p 值四舍五入成 0.0000。"""
    return "< 0.0001" if value < 0.0001 else f"{value:.4f}"
