from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_ctr_page_runs_default_experiment_and_explains_holdout():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()
    app.radio[0].set_value("ctr").run()
    assert any(button.label == "运行 CTR 实验" for button in app.button)
    next(button for button in app.button if button.label == "运行 CTR 实验").click().run()
    assert not app.exception
    visible = "\n".join(item.value for item in app.markdown)
    assert "Logistic Regression" in visible
    assert "Random Forest" in visible
    assert "测试集" in visible
    assert "合成" in visible


def test_ctr_run_is_saved_once(tmp_path, monkeypatch):
    from adlab.data.records import list_ctr_runs
    import adlab.ui.ctr as ctr_page

    db_path = tmp_path / "ctr.sqlite3"
    monkeypatch.setattr(ctr_page, "DEFAULT_DB_PATH", db_path)
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()
    app.radio[0].set_value("ctr").run()
    next(button for button in app.button if button.label == "运行 CTR 实验").click().run()
    next(button for button in app.button if button.label == "保存本次 CTR 实验").click().run()
    assert not app.exception
    assert len(list_ctr_runs(db_path)) == 1
    assert next(button for button in app.button if button.label == "保存本次 CTR 实验").disabled
