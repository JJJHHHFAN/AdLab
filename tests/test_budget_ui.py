from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _navigate(app, slug):
    next(radio for radio in app.radio if radio.label == "导航").set_value(slug).run()


def test_budget_page_runs_default_experiment_and_labels_simulation():
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    _navigate(app, "budget")
    next(button for button in app.button if button.label == "运行预算实验").click().run()
    assert not app.exception
    visible = "\n".join(item.value for item in app.markdown)
    assert "规则分配" in visible
    assert "线性规划" in visible
    assert "预测" in visible
    assert "随机模拟" in visible


def test_budget_run_saves_once_and_restores_parameters(tmp_path, monkeypatch):
    import adlab.ui.budget as budget_page
    from adlab.data.records import list_budget_runs

    db_path = tmp_path / "runs.sqlite3"
    monkeypatch.setattr(budget_page, "DEFAULT_DB_PATH", db_path)
    app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
    _navigate(app, "budget")
    next(field for field in app.number_input if field.label == "总预算").set_value(12000.0)
    next(button for button in app.button if button.label == "运行预算实验").click().run()
    assert app.session_state["budget_run"][0].total_budget == 12000

    _navigate(app, "home")
    _navigate(app, "budget")
    assert next(field for field in app.number_input if field.label == "总预算").value == 12000
    next(button for button in app.button if button.label == "保存本次预算实验").click().run()
    assert not app.exception
    assert len(list_budget_runs(db_path)) == 1
    assert next(button for button in app.button if button.label == "保存本次预算实验").disabled
