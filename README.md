# AdLab — Computational Advertising Laboratory

AdLab 是一个免费、开源、可在本地运行的计算广告教学实验平台。当前已完成前五阶段：基础界面、A/B 测试、广告竞价、CTR 预测和预算优化。

代码采用 [MIT 许可证](LICENSE)。

后续将加入多臂老虎机实验，并完成整合交付。未实现的实验不会展示虚构结果。

## 本地运行

需要 Python 3.12 和 `uv`。本项目优先在 Apple Silicon Mac 上验证，也可在其他支持 Python 3.12 的电脑运行。

```bash
uv sync --python 3.12
uv run streamlit run app.py
```

打开终端显示的本地地址。运行测试：

```bash
uv run pytest
```

请始终使用 `uv run`，以保证启动命令与依赖使用同一虚拟环境。项目没有付费 API 和云服务依赖。

## 目前可以使用什么

- 首页：了解学习路径、实验原则和开发状态。
- A/B 测试：输入两组用户、点击和转化人数；选择主指标与显著性水平；查看置信区间、p 值、解释和样本量估算。
- 广告竞价：输入广告主出价、质量分、点击价值、预算与广告位 CTR；比较四种机制的排名、支付、期望收益和平台收入。
- CTR 预测：生成可复现的合成曝光，选择时间或随机划分，比较 Logistic Regression 与 Random Forest，并查看测试集 ROC、概率分布和校准图。
- 预算优化：输入预估 CPA、ROAS、计划最低额和上限，按三种目标比较规则分配与线性规划，并区分预测指标和一次随机模拟实现值。
- 实验记录：将本次输入与计算结果保存到本机 SQLite 数据库，并在记录页查看。
- 学习文档：阅读 A/B 测试、广告竞价、CTR 预测和预算优化的概念、公式、算例与局限。
- 示例文件：[A/B 算例](examples/ab_test_example.json)、[竞价算例](examples/auction_example.json)、[CTR 合成曝光（1,000 行）](examples/ctr_sample.csv)和[预算算例](examples/budget_example.json)，均非真实投放数据。CTR 页面按参数生成数据，不从 CSV 导入。
- 左侧导航：查看八个页面；多臂老虎机明确标为“规划中”。

统计定义、公式与验证算例见 [A/B 测试方法](docs/ab-test-methods.md)、[竞价方法](docs/auction-methods.md)、[CTR 预测方法](docs/ctr-methods.md)和[预算优化方法](docs/budget-methods.md)。算法层、数据层、可视化层和 UI 的职责见 [架构说明](docs/architecture.md)。阶段任务见 [第一阶段](docs/superpowers/plans/2026-10-25-stage-1-foundation.md)、[第二阶段](docs/superpowers/plans/2026-10-25-stage-2-ab-test.md)、[第三阶段](docs/superpowers/plans/2026-10-26-stage-3-auctions.md)、[第四阶段](docs/superpowers/plans/2026-10-26-stage-4-ctr.md)与[第五阶段](docs/superpowers/plans/2026-10-27-stage-5-budget.md)。

## 七阶段路线

1. 项目基础（已完成）
2. A/B 测试与实验记录（已完成，MVP）
3. 广告竞价（已完成）
4. CTR 预测（已完成）
5. 预算优化（已完成）
6. 多臂老虎机
7. 整合、测试和技术文档
