"""AdLab Streamlit 入口。运行：uv run streamlit run app.py。"""

import streamlit as st

from adlab.config import EXPERIMENTS, get_experiment
from adlab.ui.home import render_home
from adlab.ui.planned import render_planned


st.set_page_config(
    page_title="AdLab · 计算广告算法实验室",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.markdown("## AdLab")
    st.caption("计算广告算法实验室")
    selected_slug = st.radio(
        "导航",
        options=[experiment.slug for experiment in EXPERIMENTS],
        format_func=lambda slug: get_experiment(slug).title,
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("本地运行 · 免费开源 · 第一阶段")

if selected_slug == "home":
    render_home()
else:
    render_planned(get_experiment(selected_slug))
