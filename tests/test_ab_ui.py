from pathlib import Path

from streamlit.testing.v1 import AppTest

from adlab.data.records import list_runs


def test_ab_page_runs_default_example_and_explains_result():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()
    app.radio[0].set_value("ab_test").run()

    assert not app.exception
    assert any(button.label == "运行实验" for button in app.button)
    run_button = next(button for button in app.button if button.label == "运行实验")
    run_button.click().run()

    assert not app.exception
    assert any("p 值" in item.value for item in app.markdown)
    assert any("0.036" in item.value for item in app.markdown)


def test_one_run_can_be_saved_only_once_and_sample_plan_stays_visible(tmp_path, monkeypatch):
    import adlab.ui.ab_test as ab_page

    db_path = tmp_path / "runs.sqlite3"
    monkeypatch.setattr(ab_page, "DEFAULT_DB_PATH", db_path)
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=15).run()
    app.radio[0].set_value("ab_test").run()
    next(button for button in app.button if button.label == "运行实验").click().run()
    next(button for button in app.button if button.label == "估算样本量").click().run()
    assert any("每组至少" in item.value for item in app.info)

    next(button for button in app.button if button.label == "保存本次实验").click().run()
    assert not app.exception
    assert len(list_runs(db_path)) == 1
    assert any("每组至少" in item.value for item in app.info)
    assert next(button for button in app.button if button.label == "保存本次实验").disabled
