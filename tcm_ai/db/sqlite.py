# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""SQLite 连接与 schema 初始化。"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterator

from tcm_ai.core.paths import DATA_DIR

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "diagnosis_history.sql"
DEFAULT_DB_PATH = os.path.join(DATA_DIR, "diagnosis_history.sqlite3")


def parse_sqlite_path(database_url: str = "") -> str:
    url = (database_url or "").strip()
    if not url:
        return DEFAULT_DB_PATH
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///") :]
    if url.startswith("sqlite://"):
        return url[len("sqlite://") :]
    return url


def connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    if not SCHEMA_PATH.is_file():
        raise RuntimeError(f"缺少 schema 文件: {SCHEMA_PATH}")
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def ensure_database(db_path: str) -> None:
    with connect(db_path) as conn:
        init_schema(conn)


def db_connection(db_path: str) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
