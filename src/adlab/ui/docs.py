"""按当前开发进度提供学习文档。"""

import streamlit as st


def render_docs() -> None:
    st.caption("LEARNING NOTES  /  阶段 2")
    st.title("学习文档 · Learning Notes")
    st.write("当前已完成 A/B 测试章节；其他算法章节会随对应实验加入。")

    st.subheader("A/B 测试：先定义要比较什么")
    st.write(
        "随机化单位是用户。CTR 衡量每位分组用户点击的比例；"
        "点击后 CVR 衡量点击者中的转化比例。若目标是转化，建议用每用户转化率作为主指标。"
    )
    st.latex(r"\hat p_A=\frac{x_A}{n_A},\quad \hat p_B=\frac{x_B}{n_B},\quad "
             r"\Delta=\hat p_B-\hat p_A")
    st.write("双侧合并比例 z 检验的原假设是两组真实比例相同。")
    st.latex(r"\hat p=\frac{x_A+x_B}{n_A+n_B},\qquad "
             r"z=\frac{\hat p_B-\hat p_A}{\sqrt{\hat p(1-\hat p)(1/n_A+1/n_B)}}")
    st.write("单组比例使用 Wilson 区间，差值使用 Newcombe 区间；小样本时改用 Fisher 精确检验计算 p 值。")

    st.subheader("完整计算示例")
    st.write(
        "A 组 10,000 人中 400 人点击，B 组 10,000 人中 460 人点击。"
        "CTR 分别为 4.0% 和 4.6%，B − A 为 +0.6 个百分点，相对提升 15%。"
        "合并比例为 4.3%，z≈2.091，双侧 p≈0.0365。若预先选择 α=0.05，"
        "固定样本检验达到统计显著；仍需评估收益、成本和区间范围。"
    )

    st.subheader("参数含义与延伸阅读")
    st.markdown(
        """
        - **α：** 预先容许的第一类错误率；本平台可选 1%、5%、10%。
        - **最小可检测差异（MDE）：** 希望实验有能力发现的最小绝对变化，单位为百分点。
        - **功效（Power）：** 若假定差异真实存在，固定样本检验检出它的近似概率。
        - **建议阅读：** [SciPy Fisher 精确检验文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html)；再学习序贯检验、多重比较与实验分流质量。
        """
    )
    st.warning("不要把 p 值读成原假设成立的概率；不要因为中途看见显著就提前停止。")
