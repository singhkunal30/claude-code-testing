"""SQLite connection helper and schema setup."""
from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DB_PATH_ENV = "TIL_DB_PATH"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "til.db"


def _db_path() -> Path:
    return Path(os.environ.get(DB_PATH_ENV, DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    text        TEXT    NOT NULL,
    source      TEXT,
    tags_json   TEXT    NOT NULL DEFAULT '[]',
    created_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entries_created_at ON entries(created_at);

CREATE TABLE IF NOT EXISTS digests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    period        TEXT    NOT NULL,
    start_date    TEXT    NOT NULL,
    end_date      TEXT    NOT NULL,
    content       TEXT    NOT NULL,
    entry_ids_json TEXT   NOT NULL DEFAULT '[]',
    created_at    TEXT    NOT NULL
);
"""


def init_db() -> None:
    with db_session() as conn:
        conn.executescript(SCHEMA)
