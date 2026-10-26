"""生成带冻结历史快照的合成广告曝光；不包含真实用户数据。"""

import numpy as np
import pandas as pd
from scipy.special import expit


AD_CATEGORIES = ("电商", "游戏", "教育", "出行")
DEVICES = ("手机", "平板", "桌面")
SLOTS = ("顶部", "中部", "底部")


def generate_ctr_data(n_exposures: int, seed: int) -> pd.DataFrame:
    """生成按时间排列的曝光；历史计数只来自模拟期之前。"""
    if isinstance(n_exposures, bool) or not isinstance(n_exposures, int) or not 100 <= n_exposures <= 100_000:
        raise ValueError("曝光数量必须是 100 至 100000 的整数")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("随机种子必须是 0 至 2³²−1 的整数")

    rng = np.random.default_rng(seed)
    n_users = max(100, n_exposures // 8)
    user_bias = rng.normal(0, 0.65, size=n_users)
    history_impressions = rng.integers(5, 100, size=n_users)
    history_clicks = rng.binomial(history_impressions, expit(-2.8 + user_bias))
    ad_bias = rng.normal(0, 0.35, size=12)

    user_index = rng.integers(0, n_users, size=n_exposures)
    ad_index = rng.integers(0, 12, size=n_exposures)
    device_index = rng.choice(3, size=n_exposures, p=[0.72, 0.10, 0.18])
    slot_index = rng.choice(3, size=n_exposures, p=[0.35, 0.40, 0.25])
    event_time = pd.date_range("2026-01-01", periods=n_exposures, freq="min", tz="UTC")
    display_hour = event_time.hour.to_numpy()

    logits = (
        -2.8
        + user_bias[user_index]
        + ad_bias[ad_index]
        + np.array([0.55, 0.0, -0.45])[slot_index]
        + np.array([0.15, 0.0, -0.10])[device_index]
        + 0.20 * np.cos(2 * np.pi * (display_hour - 20) / 24)
        + np.linspace(-0.15, 0.15, n_exposures)
    )
    clicked = rng.binomial(1, expit(logits)).astype(int)
    return pd.DataFrame(
        {
            "user_id": [f"U{index:05d}" for index in user_index],
            "ad_id": [f"AD{index:02d}" for index in ad_index],
            "ad_category": [AD_CATEGORIES[index // 3] for index in ad_index],
            "event_time": event_time,
            "display_hour": display_hour,
            "device": np.asarray(DEVICES)[device_index],
            "slot": np.asarray(SLOTS)[slot_index],
            "prior_impressions": history_impressions[user_index],
            "prior_clicks": history_clicks[user_index],
            "clicked": clicked,
        }
    )
