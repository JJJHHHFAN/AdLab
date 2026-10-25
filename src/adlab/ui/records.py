"""展示本地保存的 A/B 实验记录。"""

import streamlit as st

from adlab.data.records import list_runs
from adlab.ui.formatting import format_p_value


def render_records() -> None:
    st.caption("阶段 2  /  LOCAL HISTORY")
    st.title("实验记录 · Experiment History")
    st.write("这里保存的是本机运行的实验输入与计算结果。记录不会上传到服务器。")
    runs = list_runs()
    if not runs:
        st.info("还没有记录。到 A/B 测试页面运行实验后，点击「保存本次实验」。")
        return

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
