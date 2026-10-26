"""无泄漏的 CTR 划分、模型比较与概率评估。"""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SplitMode = Literal["random", "time"]
CATEGORICAL_FEATURES = ("ad_id", "ad_category", "device", "slot")
NUMERIC_FEATURES = ("display_hour", "prior_impressions", "prior_clicks")
MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
REQUIRED_COLUMNS = set(MODEL_FEATURES) | {"user_id", "event_time", "clicked"}


@dataclass(frozen=True)
class CTRDataSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    mode: SplitMode


@dataclass(frozen=True)
class CTRMetrics:
    auc_roc: float
    log_loss: float
    precision: float | None
    recall: float
    brier_score: float


@dataclass(frozen=True)
class CTRExperimentResult:
    validation_metrics: dict[str, CTRMetrics]
    selected_name: str
    test_metrics: CTRMetrics
    test_labels: np.ndarray
    test_probabilities: np.ndarray
    fitted_models: dict[str, Pipeline]
    threshold: float


def split_ctr_data(frame: pd.DataFrame, mode: SplitMode, seed: int) -> CTRDataSplit:
    """先切分原始行；任何类别编码或标准化都留到训练管线中。"""
    if mode not in ("random", "time"):
        raise ValueError("划分方式只能是 random 或 time")
    if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed < 2**32:
        raise ValueError("随机种子必须是 0 至 2³²−1 的整数")
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"数据缺少字段：{', '.join(sorted(missing))}")
    if len(frame) < 100 or not frame.index.is_unique:
        raise ValueError("至少需要 100 行且行索引必须唯一")
    if frame[list(MODEL_FEATURES) + ["event_time", "clicked"]].isna().any().any():
        raise ValueError("模型字段、时间与标签不能缺失")
    if not frame.clicked.isin([0, 1]).all():
        raise ValueError("点击标签必须是 0 或 1")

    if mode == "time":
        ordered = frame.sort_values("event_time", kind="stable")
        if ordered.event_time.duplicated().any():
            raise ValueError("时间顺序划分需要唯一的展示时间")
        first, second = int(len(ordered) * 0.6), int(len(ordered) * 0.8)
        train, validation, test = ordered.iloc[:first], ordered.iloc[first:second], ordered.iloc[second:]
    else:
        try:
            train, remainder = train_test_split(
                frame, train_size=0.6, stratify=frame.clicked, random_state=seed
            )
            validation, test = train_test_split(
                remainder, test_size=0.5, stratify=remainder.clicked, random_state=seed
            )
        except ValueError as error:
            raise ValueError("随机分层划分失败：请增加样本量或调整随机种子") from error

    parts = (train.copy(), validation.copy(), test.copy())
    if any(part.clicked.nunique() != 2 for part in parts):
        raise ValueError("训练、验证和测试集都必须同时包含点击和未点击；请增加样本量或更换种子")
    return CTRDataSplit(*parts, mode=mode)


def _pipeline(estimator: LogisticRegression | RandomForestClassifier) -> Pipeline:
    preprocess = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), list(CATEGORICAL_FEATURES)),
            ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
        ],
        remainder="drop",
    )
    return Pipeline([("preprocess", preprocess), ("model", estimator)])


def _metrics(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> CTRMetrics:
    predictions = (probabilities >= threshold).astype(int)
    return CTRMetrics(
        auc_roc=float(roc_auc_score(labels, probabilities)),
        log_loss=float(log_loss(labels, probabilities, labels=[0, 1])),
        precision=float(precision_score(labels, predictions)) if predictions.any() else None,
        recall=float(recall_score(labels, predictions, zero_division=0)),
        brier_score=float(brier_score_loss(labels, probabilities)),
    )


def run_ctr_experiment(
    split: CTRDataSplit, seed: int, threshold: float = 0.10
) -> CTRExperimentResult:
    """在训练集拟合两种模型，用验证集选模型，最后评估一次测试集。"""
    if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed < 2**32:
        raise ValueError("随机种子必须是 0 至 2³²−1 的整数")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 < threshold < 1:
        raise ValueError("分类阈值必须介于 0 和 1 之间")
    estimators = {
        "Logistic Regression": LogisticRegression(max_iter=500, random_state=seed),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=8, min_samples_leaf=5, random_state=seed, n_jobs=-1
        ),
    }
    x_train, y_train = split.train.loc[:, MODEL_FEATURES], split.train.clicked.to_numpy()
    x_validation = split.validation.loc[:, MODEL_FEATURES]
    y_validation = split.validation.clicked.to_numpy()
    fitted_models: dict[str, Pipeline] = {}
    validation_metrics: dict[str, CTRMetrics] = {}
    for name, estimator in estimators.items():
        pipeline = _pipeline(estimator)
        pipeline.fit(x_train, y_train)
        probabilities = pipeline.predict_proba(x_validation)[:, 1]
        validation_metrics[name] = _metrics(y_validation, probabilities, threshold)
        fitted_models[name] = pipeline

    selected_name = min(validation_metrics, key=lambda name: validation_metrics[name].log_loss)
    test_labels = split.test.clicked.to_numpy()
    test_probabilities = fitted_models[selected_name].predict_proba(split.test.loc[:, MODEL_FEATURES])[:, 1]
    return CTRExperimentResult(
        validation_metrics=validation_metrics,
        selected_name=selected_name,
        test_metrics=_metrics(test_labels, test_probabilities, threshold),
        test_labels=test_labels,
        test_probabilities=test_probabilities,
        fitted_models=fitted_models,
        threshold=threshold,
    )
