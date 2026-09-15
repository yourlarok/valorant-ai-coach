import json
import os
import sqlite3
from datetime import datetime, timezone
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                link TEXT NOT NULL DEFAULT '',
                read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        # 段位/RR 无法从对局数据推导，存档案表由绑定/设置流程写入
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                rank_tier TEXT,
                rr INTEGER,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyzed_matches (
                match_id TEXT PRIMARY KEY,
                player_name TEXT NOT NULL,
                analyzed_at TEXT NOT NULL
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


def save_profile(name: str, rank_tier: str | None, rr: int | None) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO profiles (name, rank_tier, rr, updated_at) VALUES (?,?,?,?)",
            (name, rank_tier, rr, datetime.now(timezone.utc).isoformat()),
        )


def load_profile(name: str) -> dict | None:
    with sqlite3.connect(_db_path()) as conn:
        row = conn.execute(
            "SELECT name, rank_tier, rr FROM profiles WHERE name = ?", (name,),
        ).fetchone()
    if row is None:
        return None
    return {"name": row[0], "rank_tier": row[1], "rr": row[2]}


def list_profile_names() -> list[str]:
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute("SELECT name FROM profiles ORDER BY updated_at").fetchall()
    return [r[0] for r in rows]


def is_match_analyzed(match_id: str) -> bool:
    with sqlite3.connect(_db_path()) as conn:
        row = conn.execute(
            "SELECT 1 FROM analyzed_matches WHERE match_id = ?", (match_id,),
        ).fetchone()
    return row is not None


def mark_match_analyzed(match_id: str, player_name: str) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO analyzed_matches (match_id, player_name, analyzed_at) VALUES (?,?,?)",
            (match_id, player_name, datetime.now(timezone.utc).isoformat()),
        )
