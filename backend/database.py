import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "panel.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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


def save_snapshot(data: dict):
    conn = get_conn()
    conn.execute(
        "INSERT INTO snapshots (timestamp, data) VALUES (?, ?)",
        (datetime.utcnow().isoformat(), json.dumps(data, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def get_latest_snapshot() -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM snapshots ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row:
        return {"timestamp": row["timestamp"], "data": json.loads(row["data"])}
    return None


def get_history(limit: int = 100) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT timestamp, data FROM snapshots ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        results.append({"timestamp": row["timestamp"], "data": json.loads(row["data"])})
    results.reverse()
    return results


init_db()
