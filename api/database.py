import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta

# Vercel serverless: /tmp is the only writable directory
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/panel.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "panel.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if os.path.dirname(DB_PATH) else None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        conn = get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                data JSON NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except Exception:
        pass  # Graceful fail in serverless


def save_snapshot(data: dict):
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO snapshots (timestamp, data) VALUES (?, ?)",
            (datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"), json.dumps(data, ensure_ascii=False)),
        )
        conn.execute(
            "DELETE FROM snapshots WHERE id NOT IN (SELECT id FROM snapshots ORDER BY id DESC LIMIT 5)"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_latest_snapshot() -> dict | None:
    try:
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if row:
            return {"timestamp": row["timestamp"], "data": json.loads(row["data"])}
    except Exception:
        pass
    return None


init_db()
