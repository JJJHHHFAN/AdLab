"""A/B 测试实验室页面；统计计算均委托给算法层。"""

import streamlit as st

from adlab.algorithms.ab_test import (
    ABInput,
    Arm,
    analyze_ab,
    estimate_sample_size,
    prospective_power,
)
from adlab.charts.intervals import ab_interval_figure, difference_interval_figure
from adlab.data.records import DEFAULT_DB_PATH, save_run


def _percent(value: float | None) -> str:
    return "无法计算" if value is None else f"{value:.2%}"


def render_ab_test() -> None:
    st.caption("阶段 2  /  STATISTICAL EXPERIMENT")
    st.title("A/B 测试 · A/B Testing")
    st.write("输入两组独立随机分配用户的数据，检验广告指标差异，并估算下一次实验所需样本量。")

    st.subheader("1 · 实验原理")
    st.write(
        "每位用户只进入 A 或 B 一组。CTR 使用点击用户数除以分配用户数；"
        "点击后 CVR 使用转化用户数除以点击用户数。实验前先选定一个主指标。"
    )
    st.latex(r"\mathrm{CTR}=\frac{\mathrm{Clicks}}{\mathrm{Assigned\ Users}},\qquad "
             r"\mathrm{CVR}=\frac{\mathrm{Conversions}}{\mathrm{Clicks}}")
    st.caption("假设：用户独立、随机分配稳定、两组口径一致。实验周期只是记录，不会自动提高显著性。")

    st.subheader("2 · 参数设置与运行实验")
    st.caption("预填数字是教学算例，不代表真实广告投放。请用独立用户数填写曝光人数。")
    with st.form("ab_inputs"):
        a_col, b_col = st.columns(2)
        with a_col:
            st.markdown("**A 组 · 对照**")
            a_users = st.number_input("A 组曝光人数", min_value=1, value=10_000, step=100)
            a_clicks = st.number_input("A 组点击人数", min_value=0, value=400, step=10)
            a_conversions = st.number_input("A 组转化人数", min_value=0, value=40, step=1)
        with b_col:
            st.markdown("**B 组 · 实验**")
            b_users = st.number_input("B 组曝光人数", min_value=1, value=10_000, step=100)
            b_clicks = st.number_input("B 组点击人数", min_value=0, value=460, step=10)
            b_conversions = st.number_input("B 组转化人数", min_value=0, value=50, step=1)
        duration = st.number_input("实验周期（天）", min_value=1, value=14, step=1)
        metric_label = st.selectbox("预先指定的主指标", ["CTR（点击率）", "每用户转化率"])
        alpha = st.selectbox("显著性水平 α", [0.01, 0.05, 0.10], index=1, format_func=lambda x: f"{x:.0%}")
        submitted = st.form_submit_button("运行实验", type="primary")

    if submitted:
        st.session_state.pop("ab_run", None)
        inputs = ABInput(
            Arm(a_users, a_clicks, a_conversions),
            Arm(b_users, b_clicks, b_conversions),
            duration,
            alpha=alpha,
            primary_metric="ctr" if metric_label.startswith("CTR") else "conversion_per_user",
        )
        try:
            result = analyze_ab(inputs)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["ab_run"] = (inputs, result)

    if "ab_run" in st.session_state:
        inputs, result = st.session_state["ab_run"]
        _render_results(inputs, result)

    st.subheader("实验前规划 · 功效与样本量")
    st.write("用基线率和希望检测到的最小差异规划下一次实验。这里的功效是事前假设下的近似值。")
    with st.form("sample_size"):
        col1, col2, col3 = st.columns(3)
        baseline_percent = col1.number_input("预期基线率 (%)", min_value=0.01, max_value=99.0, value=4.0, step=0.1)
        mde_points = col2.number_input("最小可检测差异（百分点）", min_value=0.01, max_value=99.0, value=0.6, step=0.1)
        target_power = col3.selectbox("目标统计功效", [0.8, 0.9], format_func=lambda x: f"{x:.0%}")
        plan = st.form_submit_button("估算样本量")
    if plan:
        try:
            per_group = estimate_sample_size(
                baseline_percent / 100,
                mde_points / 100,
                alpha=alpha,
                target_power=target_power,
            )
        except ValueError as error:
            st.error(str(error))
        else:
            power = prospective_power(per_group, baseline_percent / 100, mde_points / 100, alpha)
            st.info(f"预计每组至少 **{per_group:,} 位独立用户**，两组共 {2 * per_group:,} 位；近似功效 {power:.1%}。")
            st.caption("按等量分组、双侧比例检验和固定样本量计算；实际流量、丢失与重复曝光会改变所需周期。")

    st.subheader("现实业务应用")
    st.write("可用来评估素材、落地页或投放策略的预先定义指标。上线决策还需结合收益、成本、风险和后续观察。")
    st.subheader("模型局限性")
    st.write(
        "重复曝光、分组污染、提前停止和多重检验都可能让 p 值失真。"
        "点击后 CVR 是经过点击筛选的人群指标，不能单独当作随机分组的因果效应。"
    )


def _render_results(inputs: ABInput, result) -> None:
    st.subheader("3 · 结果可视化")
    main_label = "CTR" if result.primary_metric == "ctr" else "每用户转化率"
    col1, col2, col3 = st.columns(3)
    col1.metric(f"A 组 {main_label}", _percent(result.a_rate))
    col2.metric(f"B 组 {main_label}", _percent(result.b_rate))
    col3.metric("相对提升", _percent(result.relative_lift))

    st.plotly_chart(ab_interval_figure(result), width="stretch")
    st.plotly_chart(difference_interval_figure(result), width="stretch")
    st.caption("区间是抽样不确定性的表达，不表示某个具体参数有相应概率落在本次区间中。")

    st.markdown("**补充指标**")
    st.dataframe(
        [
            {"组别": "A 组", "CTR": _percent(result.a.ctr), "点击后 CVR": _percent(result.a.cvr), "每用户转化率": _percent(result.a.conversion_per_user)},
            {"组别": "B 组", "CTR": _percent(result.b.ctr), "点击后 CVR": _percent(result.b.cvr), "每用户转化率": _percent(result.b.conversion_per_user)},
        ],
        hide_index=True,
        width="stretch",
    )

    st.subheader("4 · 结果解释")
    method = "双侧合并比例 z 检验" if result.test_method == "pooled_z" else "双侧 Fisher 精确检验"
    st.markdown(f"**p 值：{result.p_value:.4f}** · 方法：{method} · 预设 α：{result.alpha:.0%}")
    st.write(
        f"B − A = {result.absolute_diff:+.2%}；"
        f"{1 - result.alpha:.0%} 差值区间为 [{result.diff_ci[0]:+.2%}, {result.diff_ci[1]:+.2%}]。"
    )
    if result.significant:
        st.success("按预先选定的主指标和显著性水平，本次固定样本检验达到统计显著。")
    else:
        st.info("本次固定样本检验未达到预设显著性水平；这不证明两组效果完全相同。")
    st.write(
        "p 值不是原假设成立的概率。统计显著性也不是商业显著性；"
        "请结合绝对提升、区间宽度、收益成本和实验质量决定是否上线。"
    )
    st.caption(f"实验记录周期：{inputs.duration_days} 天。若实验中途反复查看并按显著性提前停止，常规 p 值不再保持原有解释。")
    if st.button("保存本次实验"):
        run_id = save_run(DEFAULT_DB_PATH, inputs, result)
        st.success(f"已保存为本地实验记录 #{run_id}。")
