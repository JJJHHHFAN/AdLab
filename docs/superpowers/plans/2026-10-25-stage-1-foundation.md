# AdLab 第一阶段实现计划

**目标：** 建立可在 Apple Silicon Mac 本地启动的教学平台骨架。

**架构：** `app.py` 只负责页面入口；`src/adlab/config.py` 保存实验目录；`src/adlab/ui/` 负责中文界面；`src/adlab/charts/` 负责通用图表。算法模块将在后续阶段加入，不把计算逻辑写进页面。

**技术栈：** Python 3.12、Streamlit、Plotly、pytest、uv。

## 任务

- [x] 创建项目元数据、独立环境与锁文件。
- [x] 先写实验目录测试，确认其因功能缺失而失败。
- [x] 实现实验目录与阶段状态，使导航顺序和唯一性测试通过。
- [x] 实现首页、左侧导航、后续阶段说明页和通用 Plotly 图表组件。
- [x] 编写 README，说明环境、运行、测试及各阶段范围。
- [x] 运行自动测试、页面测试和图表组件检查，并记录结果。

## 下一步

第二阶段：实现 A/B 测试的输入校验、比例区间、显著性检验、样本量估算、界面及记录。

## 遇到的问题

| 问题 | 处理 |
|---|---|
| 首次 `uv sync` 构建失败：`pyproject.toml` 引用的 README 尚不存在 | 创建 README 后重试 |
| 安装后 `adlab` 无法导入：首次构建发生在源码写入前，生成了空的本地包 | 执行 `uv sync --reinstall-package adlab`，随后测试通过 |

## 第一阶段验收

- Python 3.12 虚拟环境与 43 个锁定依赖已创建。
- `uv run pytest -q`：3 项测试通过。
- Streamlit `AppTest`：首页和 A/B 测试规划页均无执行异常。
- Plotly 通用比较图：输入标签和值保留正确。
- `compileall`：入口、源码与测试无语法错误。
- 实际启动本地服务：`/` 与 `/_stcore/health` 均返回 HTTP 200。
