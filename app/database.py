"""SQLite persistence."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "eventpilot.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {r[1] for r in rows}


def _migrate_participants(conn: sqlite3.Connection) -> None:
    cols = _column_names(conn, "participants")
    additions = {
        "pass_token": "TEXT",
        "pass_sent_at": "TEXT",
        "certificate_sent_at": "TEXT",
        "sheet_id": "TEXT",
        "checked_in_at": "TEXT",
    }
    for name, sql_type in additions.items():
        if name not in cols:
            conn.execute(f"ALTER TABLE participants ADD COLUMN {name} {sql_type}")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_participants_pass_token ON participants(pass_token)"
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_participants_sheet_id
        ON participants(sheet_id) WHERE sheet_id IS NOT NULL AND sheet_id != ''
        """
    )


def init_db() -> None:
    with db_session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'confirmed')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                confirmed_at TEXT,
                pass_token TEXT,
                pass_sent_at TEXT,
                certificate_sent_at TEXT,
                sheet_id TEXT,
                checked_in_at TEXT
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_participants_email
                ON participants(email);

            CREATE TABLE IF NOT EXISTS action_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            );

            CREATE TABLE IF NOT EXISTS confirm_idempotency (
                idempotency_key TEXT PRIMARY KEY,
                participant_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            );

            CREATE TABLE IF NOT EXISTS pass_idempotency (
                idempotency_key TEXT PRIMARY KEY,
                participant_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            );

            CREATE TABLE IF NOT EXISTS certificate_idempotency (
                idempotency_key TEXT PRIMARY KEY,
                participant_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (participant_id) REFERENCES participants(id)
            );
            """
        )
        _migrate_participants(conn)
