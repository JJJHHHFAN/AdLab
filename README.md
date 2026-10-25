# AdLab — Computational Advertising Laboratory

AdLab 是一个免费、开源、可在本地运行的计算广告教学实验平台。当前项目处于第一阶段：基础界面与项目结构。

代码采用 [MIT 许可证](LICENSE)。

后续将依次加入 A/B 测试、广告竞价、CTR 预测、预算优化和多臂老虎机实验。未实现的实验不会展示虚构结果。

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
- 左侧导航：查看八个页面的目标；尚未开发的实验会明确标为“规划中”。
- 通用 Plotly 比较图组件：供后续实验复用，目前不把示例数据伪装成实验结果。

第一版 MVP 将在下一阶段加入完整的 A/B 测试。算法层、数据层、可视化层和 UI 的职责见 [架构说明](docs/architecture.md)。当前阶段的实现任务见 [阶段计划](docs/superpowers/plans/2026-10-25-stage-1-foundation.md)。

## 七阶段路线

1. 项目基础（当前）
2. A/B 测试与实验记录（MVP 完成）
3. 广告竞价
4. CTR 预测
5. 预算优化
6. 多臂老虎机
7. 整合、测试和技术文档
