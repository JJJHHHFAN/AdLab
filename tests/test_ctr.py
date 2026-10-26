import numpy as np
import pytest

from adlab.algorithms.ctr import MODEL_FEATURES, run_ctr_experiment, split_ctr_data
from adlab.data.ctr_synthetic import generate_ctr_data


def test_time_split_preserves_order_and_has_disjoint_rows():
    frame = generate_ctr_data(1500, 42).sample(frac=1, random_state=3)
    split = split_ctr_data(frame, mode="time", seed=42)
    assert len(split.train) == 900
    assert len(split.validation) == 300
    assert len(split.test) == 300
    assert set(split.train.index).isdisjoint(split.validation.index)
    assert set(split.train.index).isdisjoint(split.test.index)
    assert set(split.validation.index).isdisjoint(split.test.index)
    assert split.train.event_time.max() < split.validation.event_time.min()
    assert split.validation.event_time.max() < split.test.event_time.min()


def test_random_split_is_reproducible_and_stratified():
    frame = generate_ctr_data(1500, 42)
    first = split_ctr_data(frame, mode="random", seed=19)
    second = split_ctr_data(frame, mode="random", seed=19)
    assert first.train.index.tolist() == second.train.index.tolist()
    assert first.validation.index.tolist() == second.validation.index.tolist()
    assert first.test.index.tolist() == second.test.index.tolist()
    assert set(first.train.index).isdisjoint(first.validation.index)
    for part in (first.train, first.validation, first.test):
        assert abs(part.clicked.mean() - frame.clicked.mean()) < 0.02


def test_only_prediction_time_fields_enter_model():
    assert "clicked" not in MODEL_FEATURES
    assert "user_id" not in MODEL_FEATURES
    assert "event_time" not in MODEL_FEATURES
    assert {"ad_id", "ad_category", "display_hour", "device", "slot", "prior_clicks"} <= set(MODEL_FEATURES)


def test_models_are_compared_on_validation_and_selected_model_is_tested():
    split = split_ctr_data(generate_ctr_data(1500, 42), mode="time", seed=42)
    result = run_ctr_experiment(split, seed=42, threshold=0.10)
    assert set(result.validation_metrics) == {"Logistic Regression", "Random Forest"}
    assert result.selected_name == min(
        result.validation_metrics, key=lambda name: result.validation_metrics[name].log_loss
    )
    assert len(result.test_probabilities) == len(split.test)
    assert np.all((result.test_probabilities >= 0) & (result.test_probabilities <= 1))
    assert np.array_equal(result.test_labels, split.test.clicked.to_numpy())
    for metrics in [*result.validation_metrics.values(), result.test_metrics]:
        assert 0 <= metrics.auc_roc <= 1
        assert metrics.log_loss >= 0
        assert 0 <= metrics.precision <= 1
        assert 0 <= metrics.recall <= 1
        assert 0 <= metrics.brier_score <= 1


def test_preprocessor_learns_categories_only_from_train():
    split = split_ctr_data(generate_ctr_data(1500, 42), mode="time", seed=42)
    split.validation.loc[:, "device"] = "新设备"
    split.test.loc[:, "device"] = "新设备"
    result = run_ctr_experiment(split, seed=42)
    assert len(result.test_probabilities) == len(split.test)
    for pipeline in result.fitted_models.values():
        preprocess = pipeline.named_steps["preprocess"]
        encoder = preprocess.named_transformers_["categorical"]
        assert "新设备" not in encoder.categories_[2]
        scaler = preprocess.named_transformers_["numeric"]
        assert scaler.mean_[0] == pytest.approx(split.train.display_hour.mean())


def test_model_selection_does_not_use_test_labels():
    split = split_ctr_data(generate_ctr_data(1500, 42), mode="time", seed=42)
    first = run_ctr_experiment(split, seed=42)
    split.test.loc[:, "clicked"] = 1 - split.test.clicked
    second = run_ctr_experiment(split, seed=42)
    assert first.selected_name == second.selected_name
    assert first.validation_metrics == second.validation_metrics


def test_missing_class_in_time_window_has_clear_error():
    frame = generate_ctr_data(1000, 42)
    frame.loc[frame.index[-200:], "clicked"] = 0
    with pytest.raises(ValueError, match="同时包含点击和未点击"):
        split_ctr_data(frame, mode="time", seed=42)


def test_invalid_split_mode_and_threshold_are_rejected():
    frame = generate_ctr_data(1000, 42)
    with pytest.raises(ValueError):
        split_ctr_data(frame, mode="future", seed=42)
    split = split_ctr_data(frame, mode="random", seed=42)
    with pytest.raises(ValueError):
        run_ctr_experiment(split, seed=42, threshold=0)
