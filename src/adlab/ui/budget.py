"""预算分配优化的交互式教学页面。"""

import streamlit as st

from adlab.algorithms.budget import (
    MAX_BUDGET,
    MAX_CPA,
    MAX_ROAS,
    BudgetComparison,
    BudgetRequest,
    Campaign,
    run_budget_experiment,
)
from adlab.charts.budget import allocation_figure
from adlab.charts.comparison import comparison_bar
from adlab.data.records import DEFAULT_DB_PATH, save_budget_run


OBJECTIVE_LABELS = {
    "conversions": "最大化预测转化量",
    "revenue": "最大化预测收入",
    "target_cpa": "在目标 CPA 约束下最大化预测转化量",
}
DEFAULT_CAMPAIGNS = (
    Campaign("A", 20, 3, 1000, 5000),
    Campaign("B", 30, 4, 1000, 5000),
    Campaign("C", 40, 2, 500, 4000),
)


def _default_campaign(index: int) -> Campaign:
    if index < len(DEFAULT_CAMPAIGNS):
        return DEFAULT_CAMPAIGNS[index]
    return Campaign(chr(ord("A") + index), 35 + 5 * index, 2, 0, 3000)


def render_budget() -> None:
    st.caption("阶段 5  /  BUDGET ALLOCATION")
    st.title("预算优化 · Budget Allocation")
    st.write("为多个广告计划分配一个周期的预算，比较规则分配和线性规划在相同约束下的预测结果。")

    st.subheader("1 · 实验原理")
    st.write(
        "每个计划有预估 CPA、预估 ROAS、最低投放额和预算上限。"
        "规则法按指标权重分配；线性规划直接求给定预测目标的最优可行金额。"
    )
    st.latex(r"\widehat{\mathrm{Conv}}_i=\frac{x_i}{CPA_i},\quad "
             r"\widehat{\mathrm{Revenue}}_i=x_i ROAS_i,\quad "
             r"\sum_i x_i\le B,\quad m_i\le x_i\le u_i")
    st.caption("目标 CPA 是所有计划合计的预测支出 ÷ 合计预测转化量；它不是每个计划都低于目标。")

    previous = st.session_state.get("budget_run")
    previous_request = previous[0] if previous else None
    st.subheader("2 · 参数设置与运行实验")
    campaign_count = st.number_input(
        "广告计划数量", min_value=2, max_value=6,
        value=len(previous_request.campaigns) if previous_request else 3, step=1,
    )
    if st.session_state.get("budget_shape") != campaign_count:
        st.session_state["budget_shape"] = campaign_count
        if previous_request and len(previous_request.campaigns) != campaign_count:
            st.session_state.pop("budget_run", None)
            st.session_state.pop("budget_saved_id", None)
            previous_request = None

    with st.form("budget_inputs"):
        left, right = st.columns(2)
        total_budget = left.number_input(
            "总预算", min_value=0.01, max_value=MAX_BUDGET,
            value=float(previous_request.total_budget) if previous_request else 10000.0,
            step=500.0,
        )
        seed = right.number_input(
            "随机种子", min_value=0, max_value=2**32 - 1,
            value=previous_request.seed if previous_request else 42, step=1,
        )
        objective_options = tuple(OBJECTIVE_LABELS)
        objective = st.selectbox(
            "优化目标", options=objective_options,
            format_func=lambda value: OBJECTIVE_LABELS[value],
            index=objective_options.index(previous_request.objective) if previous_request else 0,
        )
        target_cpa = st.number_input(
            "目标 CPA（仅目标模式使用）", min_value=0.01, max_value=MAX_CPA,
            value=float(previous_request.target_cpa) if previous_request and previous_request.target_cpa else 23.0,
            step=1.0,
        )
        st.caption("各计划 CPA 和 ROAS 是预估输入。金额使用抽象货币单位，不代表真实投放报价。")
        campaigns: list[Campaign] = []
        for index in range(campaign_count):
            defaults = (
                previous_request.campaigns[index] if previous_request and index < len(previous_request.campaigns)
                else _default_campaign(index)
            )
            campaign_id = chr(ord("A") + index)
            with st.container(border=True):
                st.markdown(f"**广告计划 {campaign_id}**")
                first, second = st.columns(2)
                cpa = first.number_input(
                    f"{campaign_id} 预估 CPA", min_value=0.01, max_value=MAX_CPA,
                    value=float(defaults.cpa), step=1.0,
                )
                roas = second.number_input(
                    f"{campaign_id} 预估 ROAS", min_value=0.0, max_value=MAX_ROAS,
                    value=float(defaults.roas), step=0.1,
                )
                minimum = first.number_input(
                    f"{campaign_id} 最低投放金额", min_value=0.0, max_value=MAX_BUDGET,
                    value=float(defaults.min_spend), step=100.0,
                )
                maximum = second.number_input(
                    f"{campaign_id} 最大预算上限", min_value=0.0, max_value=MAX_BUDGET,
                    value=float(defaults.max_spend), step=100.0,
                )
                campaigns.append(Campaign(campaign_id, cpa, roas, minimum, maximum))
        submitted = st.form_submit_button("运行预算实验", type="primary")

    if submitted:
        st.session_state.pop("budget_run", None)
        st.session_state.pop("budget_saved_id", None)
        request = BudgetRequest(
            total_budget=float(total_budget), campaigns=tuple(campaigns),
            objective=objective, target_cpa=float(target_cpa) if objective == "target_cpa" else None,
            seed=int(seed),
        )
        try:
            results = run_budget_experiment(request)
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["budget_run"] = (request, results)

    if "budget_run" in st.session_state:
        request, results = st.session_state["budget_run"]
        _render_results(request, results)

    st.subheader("6 · 现实业务应用")
    st.write("可用于理解多个广告计划之间的机会成本、最低投放承诺和目标 CPA 对预算使用率的影响。上线前需用可靠的预测、投放实验和风险约束重新评估。")
    st.subheader("7 · 模型局限性")
    st.write(
        "模型把 CPA 与 ROAS 当作预算变化时不变的常数，没有边际收益递减、流量上限的不确定性、学习期、转化延迟或跨计划重叠。"
        "一次随机模拟实现值只是教学抽样，不能当作实际投放表现或策略优劣的证据。"
    )


def _money(value: float | None) -> str:
    return "N/A" if value is None else f"{value:,.2f}"


def _render_results(request: BudgetRequest, results: BudgetComparison) -> None:
    st.subheader("3 · 预测结果与预算分配")
    st.info(
        f"以下结果对应上次运行参数：总预算 {_money(request.total_budget)} · "
        f"{len(request.campaigns)} 个计划 · {OBJECTIVE_LABELS[request.objective]} · 种子 {request.seed}。"
    )
    if request.objective == "target_cpa":
        st.caption(f"整体预测 CPA 目标：不超过 {_money(request.target_cpa)}。若约束限制进一步投放，预算可保持未使用。")
    st.plotly_chart(allocation_figure(results), width="stretch")
    st.plotly_chart(
        comparison_bar(
            ["规则分配", "线性规划"],
            [results.rule.predicted_conversions, results.optimized.predicted_conversions],
            title="合计预测转化量", unit="次",
        ),
        width="stretch",
    )
    st.plotly_chart(
        comparison_bar(
            ["规则分配", "线性规划"],
            [results.rule.predicted_revenue, results.optimized.predicted_revenue],
            title="合计预测收入", unit="抽象货币单位",
        ),
        width="stretch",
    )
    st.dataframe(
        [
            {
                "策略": name,
                "已分配预算": _money(outcome.total_spend),
                "未使用预算": _money(outcome.unspent_budget),
                "预测转化": f"{outcome.predicted_conversions:,.2f}",
                "预测收入": _money(outcome.predicted_revenue),
                "整体预测 CPA": _money(outcome.predicted_cpa),
                "整体预测 ROAS": _money(outcome.predicted_roas),
            }
            for name, outcome in (("规则分配", results.rule), ("线性规划", results.optimized))
        ],
        hide_index=True, width="stretch",
    )
    for outcome, name in ((results.rule, "规则分配"), (results.optimized, "线性规划")):
        with st.expander(f"{name}：各计划预测结果"):
            st.dataframe(
                [
                    {
                        "计划": item.campaign_id,
                        "预算": _money(item.spend),
                        "预测转化": f"{item.predicted_conversions:,.2f}",
                        "预测收入": _money(item.predicted_revenue),
                    }
                    for item in outcome.allocations
                ],
                hide_index=True, width="stretch",
            )

    st.subheader("4 · 一次随机模拟实现值")
    st.warning("下面是按固定种子抽取的一次教学模拟，不是真实投放数据；单次差异不能证明某策略在线上更好。")
    st.dataframe(
        [
            {
                "策略": name,
                "模拟转化": outcome.simulated_conversions,
                "模拟收入": _money(outcome.simulated_revenue),
                "模拟 CPA": _money(outcome.simulated_cpa),
                "模拟 ROAS": _money(outcome.simulated_roas),
            }
            for name, outcome in (("规则分配", results.rule), ("线性规划", results.optimized))
        ],
        hide_index=True, width="stretch",
    )

    st.subheader("5 · 结果解释")
    st.write("预测转化量 = 分配预算 ÷ 预估 CPA；预测收入 = 分配预算 × 预估 ROAS。线性规划在这些固定估计和约束下求最优，不保证真实投放也如此。")
    st.markdown(
        "**独立手算示例：** 总预算 100，A 的 CPA=10、上限 60，B 的 CPA=20、上限 70。"
        "若各至少投 10，以预测转化量为目标，A 投 60、B 投 40，预测转化为 6+2=8。"
    )
    st.button(
        "保存本次预算实验", disabled="budget_saved_id" in st.session_state,
        on_click=_save_current_run, args=(request, results),
    )
    if "budget_saved_id" in st.session_state:
        st.success(f"已保存为本地预算记录 #{st.session_state['budget_saved_id']}。")


def _save_current_run(request: BudgetRequest, results: BudgetComparison) -> None:
    if "budget_saved_id" not in st.session_state:
        st.session_state["budget_saved_id"] = save_budget_run(DEFAULT_DB_PATH, request, results)
