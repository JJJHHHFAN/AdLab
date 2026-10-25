"""首页：项目目标和学习路径。"""

import streamlit as st

from adlab.config import EXPERIMENTS


def render_home() -> None:
    st.caption("COMPUTATIONAL ADVERTISING LABORATORY  /  本地教学实验平台")
    st.title("看清广告系统如何做决定")
    st.write(
        "AdLab 用可修改参数、可运行算法和可解释的结果，帮助你学习竞价、预测、统计检验和投放优化。"
    )
    st.success("第二阶段已开放：A/B 测试可运行、可解释，并可在本机保存实验记录。")

    col1, col2, col3 = st.columns(3)
    col1.metric("计划实验", "5 个")
    col2.metric("当前阶段", "2 / 7")
    col3.metric("数据来源", "本地 / 合成")

    st.subheader("学习路径")
    st.write("按阶段逐个实现和验证。左侧导航可以查看每个模块的目标与开发状态。")
    for experiment in sorted(EXPERIMENTS[1:6], key=lambda item: item.stage):
        with st.container(border=True):
            st.caption(f"阶段 {experiment.stage} · {'已开放' if experiment.status == 'available' else '规划中'}")
            st.markdown(f"**{experiment.title} · {experiment.english_title}**")
            st.write(experiment.summary)

    st.subheader("实验原则")
    st.markdown(
        """
        - **算法可检验：** 计算逻辑与页面分开，关键算法配有自动测试。
        - **假设要透明：** 模拟机制、数据生成方式与统计前提都会明确写出。
        - **结果要克制：** 合成数据和预测收益不会被称为真实投放效果。
        """
    )
