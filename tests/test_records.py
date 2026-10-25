from adlab.algorithms.ab_test import ABInput, Arm, analyze_ab
from adlab.data.records import list_runs, save_run


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
