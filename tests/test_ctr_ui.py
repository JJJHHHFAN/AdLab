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


def test_ctr_form_restores_last_run_settings_after_navigation():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()
    app.radio[0].set_value("ctr").run()
    next(field for field in app.number_input if field.label == "合成曝光数量").set_value(6000)
    next(button for button in app.button if button.label == "运行 CTR 实验").click().run()
    assert app.session_state["ctr_run"][3]["n_exposures"] == 6000

    next(radio for radio in app.radio if radio.label == "导航").set_value("home").run()
    app.radio[0].set_value("ctr").run()
    restored = next(field for field in app.number_input if field.label == "合成曝光数量")
    assert restored.value == 6000
    assert any("6,000 条" in item.value for item in app.info)


def test_ctr_page_explains_undefined_precision_at_high_threshold():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()
    app.radio[0].set_value("ctr").run()
    next(field for field in app.number_input if field.label.startswith("分类阈值")).set_value(0.99)
    next(button for button in app.button if button.label == "运行 CTR 实验").click().run()
    assert not app.exception
    assert app.session_state["ctr_run"][2].test_metrics.precision is None
    assert any("Precision 未定义" in item.value for item in app.warning)
