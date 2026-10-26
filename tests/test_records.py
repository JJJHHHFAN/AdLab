from adlab.algorithms.ab_test import ABInput, Arm, analyze_ab
from adlab.data.records import list_runs, save_run
from adlab.algorithms.auctions import AuctionRequest, Bidder, compare_auctions
from adlab.data.records import list_auction_runs, save_auction_run
from adlab.algorithms.ctr import run_ctr_experiment, split_ctr_data
from adlab.data.ctr_synthetic import generate_ctr_data
from adlab.data.records import list_ctr_runs, save_ctr_run


def test_saved_run_round_trips_input_result_and_method(tmp_path):
    db_path = tmp_path / "nested" / "runs.sqlite3"
    inputs = ABInput(Arm(100, 10, 2), Arm(100, 15, 3), 7)
    result = analyze_ab(inputs)

    run_id = save_run(db_path, inputs, result)
    saved = list_runs(db_path)

    assert len(saved) == 1
    assert saved[0].id == run_id
    assert saved[0].inputs["a"]["clicks"] == 10
    assert saved[0].result["test_method"] == result.test_method
    assert saved[0].created_at.endswith("Z")


def test_missing_database_has_no_runs_and_is_not_created(tmp_path):
    db_path = tmp_path / "runs.sqlite3"
    assert list_runs(db_path) == []
    assert not db_path.exists()


def test_auction_run_round_trips_all_mechanisms(tmp_path):
    db_path = tmp_path / "runs.sqlite3"
    auction_request = AuctionRequest(
        bidders=(Bidder("A", 5, 1, 8, 1000), Bidder("B", 4, 2, 6, 1000)),
        slot_ctrs=(0.1, 0.05),
        impressions=1000,
    )
    results = compare_auctions(auction_request)
    run_id = save_auction_run(db_path, auction_request, results)
    saved = list_auction_runs(db_path)
    assert len(saved) == 1
    assert saved[0].id == run_id
    assert saved[0].inputs["bidders"][0]["bid"] == 5
    assert set(saved[0].results) == set(results)
    assert saved[0].results["first_price"]["platform_revenue"] == 500
    assert list_runs(db_path) == []


def test_auction_history_handles_database_with_only_ab_table(tmp_path):
    db_path = tmp_path / "runs.sqlite3"
    inputs = ABInput(Arm(100, 10, 2), Arm(100, 15, 3), 7)
    save_run(db_path, inputs, analyze_ab(inputs))
    assert list_auction_runs(db_path) == []


def test_ctr_run_saves_config_and_metrics_without_exposure_rows(tmp_path):
    db_path = tmp_path / "runs.sqlite3"
    split = split_ctr_data(generate_ctr_data(1000, 42), mode="time", seed=42)
    result = run_ctr_experiment(split, seed=42)
    config = {"n_exposures": 1000, "seed": 42, "split_mode": "time"}
    run_id = save_ctr_run(db_path, config, result, {"train": 600, "validation": 200, "test": 200})
    saved = list_ctr_runs(db_path)
    assert len(saved) == 1
    assert saved[0].id == run_id
    assert saved[0].config == config
    assert saved[0].summary["selected_model"] == result.selected_name
    assert saved[0].summary["test_metrics"]["auc_roc"] == result.test_metrics.auc_roc
    assert "U000" not in str(saved[0].summary)
    assert list_runs(db_path) == []


def test_ctr_history_handles_database_with_only_ab_table(tmp_path):
    db_path = tmp_path / "runs.sqlite3"
    inputs = ABInput(Arm(100, 10, 2), Arm(100, 15, 3), 7)
    save_run(db_path, inputs, analyze_ab(inputs))
    assert list_ctr_runs(db_path) == []
