import json
import os
import sqlite3
from pathlib import Path

from app.config import DB_PATH


def _db_path() -> Path:
    override = os.environ.get("DB_PATH_OVERRIDE")
    return Path(override) if override else DB_PATH


def init_db() -> None:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                player_name TEXT NOT NULL,
                task_name TEXT NOT NULL,
                task_json TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (player_name, task_name)
            )
        """)


def save_plan(player_name: str, tasks: list[dict]) -> None:
    with sqlite3.connect(_db_path()) as conn:
        for t in tasks:
            conn.execute(
                "INSERT OR REPLACE INTO plans (player_name, task_name, task_json, done) VALUES (?,?,?,?)",
                (player_name, t["name"], json.dumps(t, ensure_ascii=False),
                 1 if t.get("done") else 0),
            )


def load_plan(player_name: str) -> list[dict]:
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            "SELECT task_json, done FROM plans WHERE player_name = ? ORDER BY rowid",
            (player_name,),
        ).fetchall()
    result = []
    for task_json, done in rows:
        t = json.loads(task_json)
        t["done"] = bool(done)
        result.append(t)
    return result


def set_task_done(player_name: str, task_name: str, done: bool) -> bool:
    with sqlite3.connect(_db_path()) as conn:
        cur = conn.execute(
            "UPDATE plans SET done = ? WHERE player_name = ? AND task_name = ?",
            (1 if done else 0, player_name, task_name),
        )
        return cur.rowcount > 0
