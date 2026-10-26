# AdLab — Computational Advertising Laboratory

AdLab 是一个免费、开源、可在本地运行的计算广告教学实验平台。当前已完成前四阶段：基础界面、A/B 测试、广告竞价和 CTR 预测。

代码采用 [MIT 许可证](LICENSE)。

后续将依次加入预算优化和多臂老虎机实验。未实现的实验不会展示虚构结果。

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
- 实验记录：将本次输入与计算结果保存到本机 SQLite 数据库，并在记录页查看。
- 学习文档：阅读 A/B 测试、广告竞价和 CTR 预测的概念、公式、算例与局限。
- 示例输入：[A/B 教学算例](examples/ab_test_example.json)、[竞价教学算例](examples/auction_example.json)和[CTR 合成曝光样例](examples/ctr_sample.csv)，均非真实投放数据。
- 左侧导航：查看八个页面；预算优化与多臂老虎机明确标为“规划中”。

统计定义、公式与验证算例见 [A/B 测试方法](docs/ab-test-methods.md)、[竞价方法](docs/auction-methods.md)和[CTR 预测方法](docs/ctr-methods.md)。算法层、数据层、可视化层和 UI 的职责见 [架构说明](docs/architecture.md)。阶段任务见 [第一阶段](docs/superpowers/plans/2026-10-25-stage-1-foundation.md)、[第二阶段](docs/superpowers/plans/2026-10-25-stage-2-ab-test.md)、[第三阶段](docs/superpowers/plans/2026-10-26-stage-3-auctions.md)与[第四阶段](docs/superpowers/plans/2026-10-26-stage-4-ctr.md)。

## 七阶段路线

1. 项目基础（已完成）
2. A/B 测试与实验记录（已完成，MVP）
3. 广告竞价（已完成）
4. CTR 预测（已完成）
5. 预算优化
6. 多臂老虎机
7. 整合、测试和技术文档
