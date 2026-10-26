"""展示本地保存的 A/B 实验记录。"""

import streamlit as st

from adlab.data.records import list_auction_runs, list_runs
from adlab.ui.formatting import format_p_value


def render_records() -> None:
    st.caption("阶段 2  /  LOCAL HISTORY")
    st.title("实验记录 · Experiment History")
    st.write("这里保存的是本机运行的实验输入与计算结果。记录不会上传到云端。")
    ab_tab, auction_tab = st.tabs(["A/B 测试", "广告竞价"])

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
