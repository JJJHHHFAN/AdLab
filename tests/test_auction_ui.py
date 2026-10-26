from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_auction_page_runs_default_example():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()
    app.radio[0].set_value("auction").run()
    assert any(button.label == "运行竞价实验" for button in app.button)
    next(button for button in app.button if button.label == "运行竞价实验").click().run()
    assert not app.exception
    assert any("第一价格" in item.value for item in app.markdown)
    assert any("第二价格" in item.value for item in app.markdown)
