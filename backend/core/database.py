"""
core/database.py
All SQLite table creation and query helpers.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "finpop.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        # Kite session (one row, updated on each login)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kite_session (
                id            INTEGER PRIMARY KEY DEFAULT 1,
                api_key       TEXT,
                access_token  TEXT,
                user_id       TEXT,
                user_name     TEXT,
                logged_in_at  TEXT
            )
        """)

        # Alert rules
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                rule_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument   TEXT NOT NULL,
                condition    TEXT NOT NULL,
                threshold    REAL NOT NULL,
                timeframe    TEXT NOT NULL DEFAULT 'absolute',
                description  TEXT NOT NULL,
                source       TEXT NOT NULL DEFAULT 'preset',
                status       TEXT NOT NULL DEFAULT 'active',
                created_at   TEXT NOT NULL,
                triggered_at TEXT
            )
        """)

        # Triggered alert history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id       INTEGER,
                instrument    TEXT,
                trigger_price REAL,
                description   TEXT,
                triggered_at  TEXT
            )
        """)

        # Expo push tokens
        conn.execute("""
            CREATE TABLE IF NOT EXISTS push_tokens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                token      TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# ── Kite Session ───────────────────────────────────────────────────────────────

def save_session(api_key, access_token, user_id, user_name):
    with get_conn() as conn:
        conn.execute("DELETE FROM kite_session")
        conn.execute("""
            INSERT INTO kite_session (id, api_key, access_token, user_id, user_name, logged_in_at)
            VALUES (1, ?, ?, ?, ?, ?)
        """, (api_key, access_token, user_id, user_name, datetime.utcnow().isoformat()))
        conn.commit()


def get_session() -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM kite_session WHERE id = 1").fetchone()
        return dict(row) if row else None


# ── Rules ──────────────────────────────────────────────────────────────────────

def save_rule(rule: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO rules
              (instrument, condition, threshold, timeframe, description, source, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
        """, (
            rule["instrument"], rule["condition"], rule["threshold"],
            rule.get("timeframe", "absolute"), rule["description"],
            rule.get("source", "preset"), datetime.utcnow().isoformat()
        ))
        conn.commit()
        return cur.lastrowid


def get_all_rules(status: str = None) -> list[dict]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM rules WHERE status=? ORDER BY created_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM rules ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def get_rule_by_id(rule_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM rules WHERE rule_id=?", (rule_id,)).fetchone()
        return dict(row) if row else None


def mark_triggered(rule_id: int):
    with get_conn() as conn:
        conn.execute("""
            UPDATE rules SET status='triggered', triggered_at=? WHERE rule_id=?
        """, (datetime.utcnow().isoformat(), rule_id))
        conn.commit()


def reset_rule(rule_id: int):
    with get_conn() as conn:
        conn.execute("""
            UPDATE rules SET status='active', triggered_at=NULL WHERE rule_id=?
        """, (rule_id,))
        conn.commit()


def delete_rule(rule_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM rules WHERE rule_id=?", (rule_id,))
        conn.commit()


# ── Alert History ──────────────────────────────────────────────────────────────

def save_alert(event: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO alert_history (rule_id, instrument, trigger_price, description, triggered_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event["rule_id"], event["instrument"],
            event["trigger_price"], event["description"],
            datetime.utcnow().isoformat()
        ))
        conn.commit()


def get_alert_history(limit: int = 100) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM alert_history ORDER BY triggered_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Push Tokens ────────────────────────────────────────────────────────────────

def upsert_push_token(token: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO push_tokens (token) VALUES (?)", (token,)
        )
        conn.commit()


def get_push_tokens() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT token FROM push_tokens").fetchall()
        return [r["token"] for r in rows]
