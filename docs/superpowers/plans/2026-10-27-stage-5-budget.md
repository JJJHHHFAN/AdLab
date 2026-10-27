# AdLab 第五阶段：预算分配优化实现计划

**目标：** 在总预算、单计划最低额和上限下，对比规则分配与线性规划；展示预测值及一次随机模拟实现值。

**架构：** `algorithms/budget.py` 负责校验、分配、求解、模拟和结构化结果；`charts/budget.py` 负责预算与结果图；`ui/budget.py` 负责参数、教学说明和解释；`data/records.py` 只保存输入及聚合结果。沿用已有导航、首页、记录和学习文档。

**技术栈：** Python 3.12、NumPy、SciPy HiGHS、Plotly、Streamlit、SQLite、pytest；无需新增依赖。

## 公式与假设

固定一个投放周期。计划 `i` 的预算 `x_i`、预测 CPA `c_i>0`、预测 ROAS `r_i>=0`，则预测转化量为 `x_i/c_i`，预测收入为 `x_i r_i`。满足 `m_i<=x_i<=u_i`、`sum(x_i)<=B`。最大化转化量或收入均为线性目标。

目标 CPA 模式最大化预测转化量，并增加 `sum(x_i) - C*sum(x_i/c_i)<=0`。若只存在零投放解，该比值未定义，实验明确报不可行。最低额、上限或目标约束冲突也明确报错。

规则法对普通目标按 `1/CPA` 或 `ROAS` 权重分配剩余预算并遵守上限；目标 CPA 模式按低 CPA 优先增加预算，逐步检查整体约束。数学法用 `scipy.optimize.linprog(method="highs")` 求解。优化不会自动预测 CPA/ROAS 随预算变化，模型把它们视为常数。

对每个策略，使用固定随机种子从以预测转化量为均值的 Poisson 分布抽取一次模拟转化数；每次转化收入固定为 `CPA*ROAS`。这是教学模拟的“本次实现值”，不是实际投放效果。相同参数和种子可复现；预测收入与模拟收入在页面分开标注。

## 任务

1. [x] 在 `tests/test_budget.py` 写排名/权重、预算上下限、三种目标、目标 CPA、不可行输入及种子复现的失败测试。
2. [x] 实现 `src/adlab/algorithms/budget.py` 的输入类型、规则分配、HiGHS 求解、模拟与聚合；运行核心测试。
3. [x] 在 `tests/test_budget_ui.py` 写默认页面运行及参数恢复测试；实现 `src/adlab/charts/budget.py`、`src/adlab/ui/budget.py`，接入 `app.py` 和 `config.py`。
4. [x] 在 `tests/test_records.py` 写预算记录往返和旧数据库兼容测试；扩展 `src/adlab/data/records.py` 与记录页。
5. [ ] 更新首页、README、架构、学习文档、方法文档及示例配置；完成本地页面和全量测试，并独立审查。

## 验收

两策略均满足预算、最低额与上限；可行的目标 CPA 结果满足整体预测约束；优化目标不低于规则法的可行结果；固定种子复现模拟实现值；页面和记录明确标注“预测”和“随机模拟”，不使用“真实投放效果”描述。
