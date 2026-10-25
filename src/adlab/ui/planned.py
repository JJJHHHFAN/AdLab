"""尚未开发的页面会说明目标和阶段，不展示虚构结果。"""

import streamlit as st

from adlab.config import Experiment


def render_planned(experiment: Experiment) -> None:
    st.caption(f"阶段 {experiment.stage}  /  PLANNED")
    st.title(f"{experiment.title} · {experiment.english_title}")
    st.write(experiment.summary)
    st.info("这个模块尚未开放。对应的算法、可视化与验证将按开发阶段加入。", icon="🧪")
    st.subheader("完成后你将能够")
    goals = {
        "auction": "设置出价、质量分和广告位，比较排名、支付与平台收入。",
        "ctr": "生成合成曝光数据，训练基准模型与随机森林，并检查概率校准。",
        "budget": "在预算约束下对比规则分配与数学优化结果。",
        "ab_test": "输入两组广告数据，计算 CTR、CVR、置信区间、p 值与所需样本量。",
        "bandit": "比较 Epsilon-Greedy、UCB1 与 Thompson Sampling 的流量分配。",
        "records": "查看本机保存的实验参数和结果，便于复现与比较。",
        "docs": "阅读各实验的概念、公式、示例、业务用途与局限。",
    }
    st.write(goals[experiment.slug])
