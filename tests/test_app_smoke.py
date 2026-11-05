"""Exercise the complete app entry point and every navigation destination."""

from functools import partial
from pathlib import Path

from streamlit.testing.v1 import AppTest

from adlab.config import EXPERIMENTS
from adlab.data import records as store
from adlab.ui import records as records_page


def test_all_navigation_pages_start_without_errors(tmp_path, monkeypatch):
    for name in ("list_runs", "list_auction_runs", "list_ctr_runs", "list_budget_runs"):
        monkeypatch.setattr(
            records_page, name, partial(getattr(store, name), db_path=tmp_path / "runs.sqlite3")
        )
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert not app.exception
    for experiment in EXPERIMENTS:
        app.radio[0].set_value(experiment.slug).run()
        assert not app.exception, experiment.slug
        assert len(app.title) > 0, experiment.slug
