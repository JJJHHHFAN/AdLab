"""A/B 实验结果的本地 SQLite 记录。"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from adlab.algorithms.ab_test import ABInput, ABResult


DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "data" / "adlab.sqlite3"


@dataclass(frozen=True)
class SavedRun:
    id: int
    created_at: str
    inputs: dict
    result: dict


def save_run(db_path: Path, inputs: ABInput, result: ABResult) -> int:
    """保存输入与完整计算结果，返回新的本地记录编号。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    with sqlite3.connect(db_path) as connection:
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
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, created_at, input_json, result_json FROM ab_runs ORDER BY id DESC"
        ).fetchall()
    return [
        SavedRun(id=row[0], created_at=row[1], inputs=json.loads(row[2]), result=json.loads(row[3]))
        for row in rows
    ]
