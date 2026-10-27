"""展示本地保存的 A/B、竞价、CTR 和预算实验记录。"""

import streamlit as st

from adlab.data.records import list_auction_runs, list_budget_runs, list_ctr_runs, list_runs
from adlab.ui.budget import OBJECTIVE_LABELS
from adlab.ui.formatting import format_p_value


def render_records() -> None:
    st.caption("LOCAL EXPERIMENT HISTORY  /  本地记录")
    st.title("实验记录 · Experiment History")
    st.write("这里保存的是本机运行的实验输入与计算结果。记录不会上传到云端。")
    ab_tab, auction_tab, ctr_tab, budget_tab = st.tabs(["A/B 测试", "广告竞价", "CTR 预测", "预算优化"])

    with ab_tab:
        runs = list_runs()
        if not runs:
            st.info("还没有 A/B 记录。运行实验后，点击「保存本次实验」。")
        for run in runs:
            metric = "CTR" if run.result["primary_metric"] == "ctr" else "每用户转化率"
            with st.expander(f"#{run.id} · {run.created_at} · {metric}"):
                st.write(
                    f"A 组：{run.result['a_rate']:.2%}　"
                    f"B 组：{run.result['b_rate']:.2%}　"
                    f"p 值：{format_p_value(run.result['p_value'])}"
                )
                st.caption(f"检验方法：{run.result['test_method']} · 显著性水平：{run.result['alpha']:.0%}")
                st.json({"输入": run.inputs, "计算结果": run.result}, expanded=False)

    with auction_tab:
        auction_runs = list_auction_runs()
        if not auction_runs:
            st.info("还没有竞价记录。运行竞价实验后，点击「保存本次竞价实验」。")
        for run in auction_runs:
            with st.expander(f"#{run.id} · {run.created_at} · {len(run.inputs['bidders'])} 位广告主"):
                st.write("各机制平台期望收入：")
                st.dataframe(
                    [
                        {"机制": name, "平台期望收入": f"{outcome['platform_revenue']:,.2f}"}
                        for name, outcome in run.results.items()
                    ],
                    hide_index=True,
                    width="stretch",
                )
                st.json({"输入": run.inputs, "计算结果": run.results}, expanded=False)

    with ctr_tab:
        ctr_runs = list_ctr_runs()
        if not ctr_runs:
            st.info("还没有 CTR 记录。运行 CTR 实验后，点击「保存本次 CTR 实验」。")
        for run in ctr_runs:
            with st.expander(f"#{run.id} · {run.created_at} · {run.summary['selected_model']}"):
                metrics = run.summary["test_metrics"]
                st.write(f"测试集 AUC-ROC：{metrics['auc_roc']:.3f} · Log Loss：{metrics['log_loss']:.3f}")
                st.caption("以下为合成数据的配置与聚合指标，不含逐行曝光或模型参数。")
                st.json({"配置": run.config, "指标": run.summary}, expanded=False)

    with budget_tab:
        budget_runs = list_budget_runs()
        if not budget_runs:
            st.info("还没有预算记录。运行预算实验后，点击「保存本次预算实验」。")
        for run in budget_runs:
            with st.expander(
                f"#{run.id} · {run.created_at} · {OBJECTIVE_LABELS.get(run.inputs['objective'], run.inputs['objective'])}"
            ):
                optimized = run.results["optimized"]
                st.write(
                    f"线性规划预测转化：{optimized['predicted_conversions']:,.2f} · "
                    f"预测收入：{optimized['predicted_revenue']:,.2f}"
                )
                st.caption("以下为教学预测和一次随机模拟实现值，不是真实投放结果。")
                st.json({"输入": run.inputs, "策略结果": run.results}, expanded=False)
