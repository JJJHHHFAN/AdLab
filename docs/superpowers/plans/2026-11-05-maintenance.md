# AdLab 维护实现计划

> 在当前会话内逐任务执行；用户已授权继续和同步。优先复用现有干净工作区。

**目标：** 修复已确认的问题并建立自动回归检查。

**架构：** 保留现有运行方式，测试与发布各自独立；只修改已确认范围。

**技术栈：** Python、GitHub Actions；沿用各项目依赖。

## 文件与步骤
- [x] 创建 `.github/workflows/test.yml`：push、pull_request、workflow_dispatch；contents: read；Ubuntu；checkout；setup-uv；`uv sync --locked --python 3.12`；`uv run --frozen pytest -q`。
- [x] 创建 `tests/test_app_smoke.py`：用现有 Streamlit AppTest 依次打开八个导航页面，断言无异常，临时数据库隔离记录页。
- [x] 更新 `README.md`，写明锁定安装与自动测试范围。
- [x] 执行 `uv run --frozen pytest -q`，预期至少原有 85 项和新增冒烟检查全部通过；实际启动应用并用浏览器检查导航。
- [ ] `git diff --check` 后以白名单暂存、提交并推送，验证远端测试通过。

## 本地验证记录

2026-11-05：本地测试与相关检查已完成；远端同步及自动运行结果由交付报告记录。复选框记录本次实施内容，最终结果以交付报告为准。
