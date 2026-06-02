from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from kurgin.config import DB_PATH, LOCAL_STATE_DIR


def _connect() -> sqlite3.Connection:
    LOCAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            stone_id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def init_db() -> None:
    with _connect():
        pass


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def add_favorite(record: pd.Series | dict[str, Any]) -> None:
    payload = dict(record)
    stone_id = str(payload.get("stone_id", "")).strip()
    if not stone_id:
        raise ValueError("stone_id is required")

    clean_payload = {key: _json_safe(value) for key, value in payload.items()}
    with _connect() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO favorites (stone_id, payload, created_at)
            VALUES (?, ?, ?)
            """,
            (
                stone_id,
                json.dumps(clean_payload, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        connection.commit()


def remove_favorite(stone_id: str) -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM favorites WHERE stone_id = ?", (stone_id,))
        connection.commit()


def list_favorites() -> pd.DataFrame:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT payload, created_at FROM favorites ORDER BY created_at DESC"
        ).fetchall()

    records: list[dict[str, Any]] = []
    for payload, created_at in rows:
        record = json.loads(payload)
        record["favorite_created_at"] = created_at
        records.append(record)
    return pd.DataFrame(records)


def clear_storage_file() -> None:
    path = Path(DB_PATH)
    if path.exists():
        path.unlink()
