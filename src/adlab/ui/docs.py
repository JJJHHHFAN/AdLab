"""按当前开发进度提供学习文档。"""

import streamlit as st


def render_docs() -> None:
    st.caption("LEARNING NOTES  /  阶段 3")
    st.title("学习文档 · Learning Notes")
    st.write("当前已完成 A/B 测试与广告竞价章节；其他算法章节会随对应实验加入。")

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

    st.divider()
    st.subheader("广告竞价：排名与支付是两个步骤")
    st.write(
        "第一价格、第二价格按出价排名，仅分配顶部广告位；GSP 为多个广告位分别确定下一名价格。"
        "质量分调整机制按出价与质量分的乘积排序，再把下一名排序分除以获胜者质量分。"
    )
    st.latex(r"s_i=b_iq_i,\qquad CPC_i=\frac{s_{i+1}}{q_i}")
    st.write(
        "教学算例中，A、B、C 出价为 5、4、2，两个广告位 CTR 为 10%、5%，每位有 1,000 次展示机会。"
        "GSP 中 A 支付 4、B 支付 2，平台期望收入为 500。"
    )
    st.write(
        "预算只截断本周期的期望点击，不动态重排；点击价值用于计算广告主期望净收益。"
        "真实平台使用更多实时信号和阈值，本实验公式仅用于理解机制。"
    )
    st.markdown(
        "延伸阅读：[GSP 原始论文](https://web.stanford.edu/~ost/papers/gsp-final.pdf) · "
        "[Google Ads 的 Ad Rank 说明](https://support.google.com/google-ads/answer/1722122?hl=en)"
    )
    st.caption("完整公式与预算规则见项目目录中的 docs/auction-methods.md。")
