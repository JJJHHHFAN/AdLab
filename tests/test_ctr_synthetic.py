import pandas as pd

from adlab.data.ctr_synthetic import generate_ctr_data


EXPECTED_COLUMNS = {
    "user_id", "ad_id", "ad_category", "event_time", "display_hour",
    "device", "slot", "prior_impressions", "prior_clicks", "clicked",
}


def test_synthetic_exposures_are_reproducible_and_have_required_fields():
    first = generate_ctr_data(1200, seed=42)
    second = generate_ctr_data(1200, seed=42)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 1200
    assert set(first.columns) == EXPECTED_COLUMNS
    assert first.event_time.is_monotonic_increasing
    assert first.clicked.sum() > 0
    assert first.clicked.sum() < len(first)
    assert not first.equals(generate_ctr_data(1200, seed=43))


def test_history_is_a_frozen_pre_experiment_snapshot():
    frame = generate_ctr_data(1200, seed=17)
    history = frame.groupby("user_id")[["prior_impressions", "prior_clicks"]].nunique()
    assert (history == 1).all().all()
    assert (frame.prior_clicks <= frame.prior_impressions).all()
    assert (frame.prior_impressions > 0).all()


def test_invalid_size_and_seed_are_rejected():
    for size, seed in [(0, 42), (100, -1), (True, 1)]:
        try:
            generate_ctr_data(size, seed)
        except ValueError:
            pass
        else:
            raise AssertionError("无效参数应被拒绝")
