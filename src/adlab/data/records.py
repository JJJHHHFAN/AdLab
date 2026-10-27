"""A/B、竞价、CTR 与预算实验的本地 SQLite 记录。"""

from dataclasses import asdict, dataclass
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from adlab.algorithms.ab_test import ABInput, ABResult
from adlab.algorithms.auctions import AuctionOutcome, AuctionRequest, Mechanism
from adlab.algorithms.ctr import CTRExperimentResult
from adlab.algorithms.budget import BudgetComparison, BudgetRequest


DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "adlab.sqlite3"


@dataclass(frozen=True)
class SavedRun:
    id: int
    created_at: str
    inputs: dict
    result: dict


@dataclass(frozen=True)
class SavedAuctionRun:
    id: int
    created_at: str
    inputs: dict
    results: dict


@dataclass(frozen=True)
class SavedCTRRun:
    id: int
    created_at: str
    config: dict
    summary: dict


@dataclass(frozen=True)
class SavedBudgetRun:
    id: int
    created_at: str
    inputs: dict
    results: dict


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def save_run(db_path: Path, inputs: ABInput, result: ABResult) -> int:
    """保存输入与完整计算结果，返回新的本地记录编号。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS ab_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    input_json TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )"""
            )
            cursor = connection.execute(
                "INSERT INTO ab_runs (created_at, schema_version, input_json, result_json) VALUES (?, ?, ?, ?)",
                (
                    timestamp,
                    1,
                    json.dumps(asdict(inputs), ensure_ascii=False, allow_nan=False),
                    json.dumps(asdict(result), ensure_ascii=False, allow_nan=False),
                ),
            )
            return int(cursor.lastrowid)


def list_runs(db_path: Path = DEFAULT_DB_PATH) -> list[SavedRun]:
    """按最近记录优先读取；数据库尚不存在时返回空列表。"""
    db_path = Path(db_path)
    if not db_path.exists():
        return []
    with closing(sqlite3.connect(db_path)) as connection:
        if not _table_exists(connection, "ab_runs"):
            return []
        rows = connection.execute(
            "SELECT id, created_at, input_json, result_json FROM ab_runs ORDER BY id DESC"
        ).fetchall()
    return [
        SavedRun(id=row[0], created_at=row[1], inputs=json.loads(row[2]), result=json.loads(row[3]))
        for row in rows
    ]


def save_auction_run(
    db_path: Path, inputs: AuctionRequest, results: dict[Mechanism, AuctionOutcome]
) -> int:
    """保存四种竞价机制的输入及结构化输出。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS auction_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    input_json TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )"""
            )
            cursor = connection.execute(
                "INSERT INTO auction_runs (created_at, schema_version, input_json, result_json) VALUES (?, ?, ?, ?)",
                (
                    timestamp,
                    1,
                    json.dumps(asdict(inputs), ensure_ascii=False, allow_nan=False),
                    json.dumps({name: asdict(outcome) for name, outcome in results.items()}, ensure_ascii=False, allow_nan=False),
                ),
            )
            return int(cursor.lastrowid)


def list_auction_runs(db_path: Path = DEFAULT_DB_PATH) -> list[SavedAuctionRun]:
    """按最近记录优先读取竞价实验。"""
    db_path = Path(db_path)
    if not db_path.exists():
        return []
    with closing(sqlite3.connect(db_path)) as connection:
        if not _table_exists(connection, "auction_runs"):
            return []
        rows = connection.execute(
            "SELECT id, created_at, input_json, result_json FROM auction_runs ORDER BY id DESC"
        ).fetchall()
    return [
        SavedAuctionRun(id=row[0], created_at=row[1], inputs=json.loads(row[2]), results=json.loads(row[3]))
        for row in rows
    ]


def save_ctr_run(
    db_path: Path, config: dict, result: CTRExperimentResult, split_counts: dict[str, int]
) -> int:
    """只保存可复现实验配置和聚合指标，不保存逐行曝光或模型。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary = {
        "selected_model": result.selected_name,
        "threshold": result.threshold,
        "split_counts": split_counts,
        "validation_metrics": {name: asdict(metrics) for name, metrics in result.validation_metrics.items()},
        "test_metrics": asdict(result.test_metrics),
    }
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS ctr_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    config_json TEXT NOT NULL,
                    summary_json TEXT NOT NULL
                )"""
            )
            cursor = connection.execute(
                "INSERT INTO ctr_runs (created_at, schema_version, config_json, summary_json) VALUES (?, ?, ?, ?)",
                (
                    timestamp,
                    1,
                    json.dumps(config, ensure_ascii=False, allow_nan=False),
                    json.dumps(summary, ensure_ascii=False, allow_nan=False),
                ),
            )
            return int(cursor.lastrowid)


def list_ctr_runs(db_path: Path = DEFAULT_DB_PATH) -> list[SavedCTRRun]:
    """按最近记录优先读取 CTR 实验；旧数据库可无此表。"""
    db_path = Path(db_path)
    if not db_path.exists():
        return []
    with closing(sqlite3.connect(db_path)) as connection:
        if not _table_exists(connection, "ctr_runs"):
            return []
        rows = connection.execute(
            "SELECT id, created_at, config_json, summary_json FROM ctr_runs ORDER BY id DESC"
        ).fetchall()
    return [
        SavedCTRRun(id=row[0], created_at=row[1], config=json.loads(row[2]), summary=json.loads(row[3]))
        for row in rows
    ]


def save_budget_run(db_path: Path, inputs: BudgetRequest, results: BudgetComparison) -> int:
    """保存预算实验输入、预测值与一次模拟实现值。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS budget_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL,
                    input_json TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )"""
            )
            cursor = connection.execute(
                "INSERT INTO budget_runs (created_at, schema_version, input_json, result_json) VALUES (?, ?, ?, ?)",
                (
                    timestamp,
                    1,
                    json.dumps(asdict(inputs), ensure_ascii=False, allow_nan=False),
                    json.dumps(asdict(results), ensure_ascii=False, allow_nan=False),
                ),
            )
            return int(cursor.lastrowid)


def list_budget_runs(db_path: Path = DEFAULT_DB_PATH) -> list[SavedBudgetRun]:
    """按最近记录优先读取预算实验；旧数据库可无此表。"""
    db_path = Path(db_path)
    if not db_path.exists():
        return []
    with closing(sqlite3.connect(db_path)) as connection:
        if not _table_exists(connection, "budget_runs"):
            return []
        rows = connection.execute(
            "SELECT id, created_at, input_json, result_json FROM budget_runs ORDER BY id DESC"
        ).fetchall()
    return [
        SavedBudgetRun(id=row[0], created_at=row[1], inputs=json.loads(row[2]), results=json.loads(row[3]))
        for row in rows
    ]
