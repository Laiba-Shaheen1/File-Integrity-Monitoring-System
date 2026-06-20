"""
Database Manager
Handles all SQLite operations for the FIM system.
Tables: baseline, alerts, logs, settings
"""

import sqlite3
import os
import json
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fim_data.db")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            sha256_hash TEXT NOT NULL,
            file_size INTEGER,
            last_modified REAL,
            baseline_created TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            event_type TEXT NOT NULL,
            old_hash TEXT,
            new_hash TEXT,
            severity TEXT DEFAULT 'MEDIUM',
            acknowledged INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            file_path TEXT NOT NULL,
            event_type TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS watch_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL UNIQUE,
            path_type TEXT NOT NULL,
            added_on TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


# ── Baseline ──────────────────────────────────────────────────────────────────

def upsert_baseline(file_path, sha256_hash, file_size, last_modified):
    conn = get_connection()
    conn.execute("""
        INSERT INTO baseline (file_path, sha256_hash, file_size, last_modified, baseline_created)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            sha256_hash=excluded.sha256_hash,
            file_size=excluded.file_size,
            last_modified=excluded.last_modified,
            baseline_created=excluded.baseline_created
    """, (file_path, sha256_hash, file_size, last_modified,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_baseline(file_path=None):
    conn = get_connection()
    if file_path:
        row = conn.execute("SELECT * FROM baseline WHERE file_path=?", (file_path,)).fetchone()
        conn.close()
        return dict(row) if row else None
    else:
        rows = conn.execute("SELECT * FROM baseline").fetchall()
        conn.close()
        return [dict(r) for r in rows]


def delete_baseline_entry(file_path):
    conn = get_connection()
    conn.execute("DELETE FROM baseline WHERE file_path=?", (file_path,))
    conn.commit()
    conn.close()


def clear_baseline():
    conn = get_connection()
    conn.execute("DELETE FROM baseline")
    conn.commit()
    conn.close()


def get_baseline_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM baseline").fetchone()[0]
    conn.close()
    return count


# ── Alerts ────────────────────────────────────────────────────────────────────

def insert_alert(file_path, event_type, old_hash=None, new_hash=None, severity="MEDIUM"):
    conn = get_connection()
    conn.execute("""
        INSERT INTO alerts (timestamp, file_path, event_type, old_hash, new_hash, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          file_path, event_type, old_hash, new_hash, severity))
    conn.commit()
    conn.close()


def get_alerts(limit=100, unacknowledged_only=False):
    conn = get_connection()
    query = "SELECT * FROM alerts"
    if unacknowledged_only:
        query += " WHERE acknowledged=0"
    query += " ORDER BY id DESC LIMIT ?"
    rows = conn.execute(query, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def acknowledge_alert(alert_id):
    conn = get_connection()
    conn.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()


def acknowledge_all_alerts():
    conn = get_connection()
    conn.execute("UPDATE alerts SET acknowledged=1")
    conn.commit()
    conn.close()


def get_alert_counts():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    modified = conn.execute("SELECT COUNT(*) FROM alerts WHERE event_type='MODIFIED'").fetchone()[0]
    deleted = conn.execute("SELECT COUNT(*) FROM alerts WHERE event_type='DELETED'").fetchone()[0]
    created = conn.execute("SELECT COUNT(*) FROM alerts WHERE event_type='CREATED'").fetchone()[0]
    unread = conn.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged=0").fetchone()[0]
    conn.close()
    return {"total": total, "modified": modified, "deleted": deleted,
            "created": created, "unread": unread}


# ── Logs ──────────────────────────────────────────────────────────────────────

def insert_log(file_path, event_type, status, details=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO logs (timestamp, file_path, event_type, status, details)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          file_path, event_type, status, details))
    conn.commit()
    conn.close()


def get_logs(limit=200):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_logs():
    conn = get_connection()
    conn.execute("DELETE FROM logs")
    conn.commit()
    conn.close()


# ── Watch Paths ───────────────────────────────────────────────────────────────

def add_watch_path(path, path_type="file"):
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO watch_paths (path, path_type, added_on)
            VALUES (?, ?, ?)
        """, (path, path_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()


def remove_watch_path(path):
    conn = get_connection()
    conn.execute("DELETE FROM watch_paths WHERE path=?", (path,))
    conn.commit()
    conn.close()


def get_watch_paths():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM watch_paths WHERE active=1").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "theme": "dark",
    "scan_interval": 30,
    "alert_sound": True,
    "auto_baseline": False,
    "log_retention_days": 30,
    "report_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
