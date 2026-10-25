# A/B 测试的统计方法

## 观察单位与输入

每一组的 `users` 是独立随机分配且只计一次的用户数。输入必须满足
`0 ≤ conversions ≤ clicks ≤ users`。若业务记录的是重复展示次数，不能直接把它当作本实验的独立样本量。

CTR 为 `clicks / users`，点击后 CVR 为 `conversions / clicks`，每用户转化率为 `conversions / users`。当点击数为 0 时，点击后 CVR 未定义，界面显示“无法计算”。主指标只能预先选择 CTR 或每用户转化率；点击后 CVR 仍展示，但不作为随机分组因果结论。

## 显著性检验

原假设是两组主指标的真实比例相同。令 A/B 组成功人数为 `x_A, x_B`，独立用户数为 `n_A, n_B`：

\[
\hat p_A=\frac{x_A}{n_A},\quad
\hat p_B=\frac{x_B}{n_B},\quad
\hat p=\frac{x_A+x_B}{n_A+n_B}.
\]

当原假设下的四个预期成功/失败人数均不少于 5 时，使用双侧合并比例 z 检验：

\[
z=\frac{\hat p_B-\hat p_A}{\sqrt{\hat p(1-\hat p)(1/n_A+1/n_B)}},
\qquad p\text{-value}=2\Phi(-|z|).
\]

否则使用 SciPy 的双侧 Fisher 精确检验；两组全为成功或全为失败时，p 值为 1。方法切换会在结果中显示。显著性判定使用 `p ≤ α`。这里的预期频数阈值是教学平台的保守约定，不是检验有效性的万能界线。

## 置信区间

单组比例使用 Wilson 得分区间。令 `z = Φ⁻¹(1−α/2)`，则中心和半宽为：

\[
c=\frac{\hat p+z^2/(2n)}{1+z^2/n},\qquad
h=\frac{z\sqrt{\hat p(1-\hat p)/n+z^2/(4n^2)}}{1+z^2/n}.
\]

差值 `B − A` 使用 Newcombe 的 Wilson 组合区间。若 A、B 的 Wilson 界分别为 `[L_A,U_A]` 和 `[L_B,U_B]`，差值下界和上界为：

\[
\Delta-\sqrt{(\hat p_B-L_B)^2+(U_A-\hat p_A)^2},\qquad
\Delta+\sqrt{(U_B-\hat p_B)^2+(\hat p_A-L_A)^2}.
\]

置信区间与 p 值采用不同但明确标注的方法，边界情形下两者的“是否跨 0”和“是否小于 α”判断可能不完全一致。显著性标记以预先指定的检验 p 值为准。

## 实验前样本量规划

输入基线率 `p₁`、最小可检测绝对差异 `δ`、显著性水平 `α` 和目标功效 `1−β`，设 `p₂=p₁+δ`，`p̄=(p₁+p₂)/2`。等量分组的初始估计为：

\[
n=\left\lceil\frac{\left[z_{1-\alpha/2}\sqrt{2\bar p(1-\bar p)}+
z_{1-\beta}\sqrt{p_1(1-p_1)+p_2(1-p_2)}\right]^2}{\delta^2}\right\rceil.
\]

实现再用相同的正态近似功效函数调整整数 `n`，返回达到目标功效的最小整数。若规划样本量下任一组在基线率、预期新比例或合并比例下的预期成功/失败人数不足 5，系统会拒绝给出近似结果；这种参数组合需要精确功效规划。规划值不含流量损失、重复曝光、分层设计或连续性校正；它不是事后“观察功效”。

## 校验算例与解释

A 组 10,000 人、400 次点击；B 组 10,000 人、460 次点击。CTR 分别为 4.0% 和 4.6%，差值 +0.6 个百分点，相对提升 15%。双侧 z 检验得到 `z≈2.09144`、`p≈0.03648836`。在预先设定 `α=0.05` 且固定样本量的条件下，本次检验达到统计显著。

这个结果不能单独决定上线：仍须评估收益、成本、置信区间、数据质量及长期影响。p 值不是原假设成立的概率；多重检验和提前停止会提高误报风险。实验周期仅作元数据，不参与 p 值计算。

## 方法参考

- [NIST：两组比例差异检验](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/diffprci.htm)
- [SciPy：Fisher 精确检验](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html)
- [statsmodels：独立比例的 Newcombe 区间](https://www.statsmodels.org/devel/generated/statsmodels.stats.proportion.confint_proportions_2indep.html)
