from pathlib import Path

from streamlit.testing.v1 import AppTest


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
