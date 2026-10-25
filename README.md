# AdLab — Computational Advertising Laboratory

AdLab 是一个免费、开源、可在本地运行的计算广告教学实验平台。当前已完成第一版 MVP：基础界面与 A/B 测试实验室。

代码采用 [MIT 许可证](LICENSE)。

后续将依次加入广告竞价、CTR 预测、预算优化和多臂老虎机实验。未实现的实验不会展示虚构结果。

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
- 实验记录：将本次输入与计算结果保存到本机 SQLite 数据库，并在记录页查看。
- 学习文档：阅读 A/B 测试的概念、公式、完整算例与风险提示。
- 示例输入：[A/B 教学算例](examples/ab_test_example.json)，与页面预填值一致，非真实投放数据。
- 左侧导航：查看八个页面；其余实验明确标为“规划中”。

统计定义、公式与验证算例见 [A/B 测试方法](docs/ab-test-methods.md)。算法层、数据层、可视化层和 UI 的职责见 [架构说明](docs/architecture.md)。阶段任务见 [第一阶段](docs/superpowers/plans/2026-10-25-stage-1-foundation.md)与[第二阶段](docs/superpowers/plans/2026-10-25-stage-2-ab-test.md)。

## 七阶段路线

1. 项目基础（已完成）
2. A/B 测试与实验记录（已完成，MVP）
3. 广告竞价
4. CTR 预测
5. 预算优化
6. 多臂老虎机
7. 整合、测试和技术文档
