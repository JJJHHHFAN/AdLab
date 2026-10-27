"""按当前开发进度提供学习文档。"""

import streamlit as st


def render_docs() -> None:
    st.caption("LEARNING NOTES  /  阶段 5")
    st.title("学习文档 · Learning Notes")
    st.write("当前已完成 A/B 测试、广告竞价、CTR 预测与预算优化章节；多臂老虎机章节会随实验加入。")

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

    st.divider()
    st.subheader("CTR 预测：先划分，再拟合")
    st.write(
        "一条合成曝光对应一个点击标签。前期历史互动是模拟期以前的固定快照；"
        "用户 ID 与目标标签不进入模型。时间划分让较晚的曝光只用于验证和测试。"
    )
    st.latex(r"\hat p=\sigma(\beta_0+\beta^\top x),\qquad "
             r"\mathrm{Brier}=\frac1n\sum_i(\hat p_i-y_i)^2")
    st.write(
        "Logistic Regression 与 Random Forest 都在训练集拟合。验证集 Log Loss 用于选模型；"
        "测试集只评估选中的模型。Precision 和 Recall 的阈值可调，其余概率指标不使用该阈值。"
    )
    st.write(
        "手算示例：预测概率 0.1、0.7、0.2、0.6 对应真实点击 0、1、0、1，"
        "Brier Score = (0.01 + 0.09 + 0.04 + 0.16) / 4 = 0.075。"
    )
    st.warning("合成数据的测试集指标不能推断真实平台 CTR；Brier Score 也不能单独代表校准程度。")
    st.markdown(
        "延伸阅读：[scikit-learn 数据泄漏建议](https://scikit-learn.org/stable/common_pitfalls) · "
        "[模型评估指标](https://scikit-learn.org/stable/modules/model_evaluation.html) · "
        "[校准曲线](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.calibration_curve.html)"
    )
    st.caption("字段、划分和完整公式见项目目录中的 docs/ctr-methods.md。")

    st.divider()
    st.subheader("预算优化：预算是约束，CPA 与 ROAS 是预估输入")
    st.write(
        "设计划 i 分得预算 xᵢ，预估 CPA 为 cᵢ、预估 ROAS 为 rᵢ。"
        "预测转化为 xᵢ/cᵢ，预测收入为 xᵢrᵢ。规则法按权重分配，线性规划在相同约束下求最优。"
    )
    st.latex(r"\max\sum_i\frac{x_i}{c_i},\qquad \sum_i x_i\le B,\qquad m_i\le x_i\le u_i")
    st.write(
        "若目标 CPA 为 C，整体预测约束是 Σxᵢ − C·Σ(xᵢ/cᵢ) ≤ 0。"
        "预算可能因计划上限或目标 CPA 而剩余。"
    )
    st.write(
        "手算示例：总预算 100，A 的 CPA=10、上限 60，B 的 CPA=20、上限 70；"
        "最大化预测转化时 A 投 60、B 投 40，预测转化为 6+2=8。"
    )
    st.warning("预估收入与一次 Poisson 模拟实现值都不是实际广告投放结果；模型假定 CPA 和 ROAS 不随预算变化。")
    st.markdown(
        "延伸阅读：[SciPy 线性规划文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html) · "
        "[NumPy Poisson 抽样](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.poisson.html)"
    )
    st.caption("规则、完整计算示例与局限见项目目录中的 docs/budget-methods.md。")
