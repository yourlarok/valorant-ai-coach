import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.config import DB_PATH

DRILLS = ("headline_flick", "reaction", "tracking")
# reaction 科目分数是毫秒，越低越好；其余科目越高越好
LOWER_IS_BETTER = {"reaction"}


def _better(drill: str, a: float, b: float) -> float:
    """返回 a、b 中对科目 drill 更好的成绩。"""
    return min(a, b) if drill in LOWER_IS_BETTER else max(a, b)


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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS training_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                drill TEXT NOT NULL,
                score REAL NOT NULL,
                extra TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_training_scores_player_drill
            ON training_scores (player_name, drill)
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


def remove_profile(name: str) -> None:
    """移除档案表记录，使自动化轮询不再为该玩家工作。
    仅删 profiles 行，不影响训练成绩 / 通知 / 已分析标记等历史数据。"""
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM profiles WHERE name = ?", (name,))


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


def best_score(player_name: str, drill: str) -> float | None:
    with sqlite3.connect(_db_path()) as conn:
        order = "ASC" if drill in LOWER_IS_BETTER else "DESC"
        row = conn.execute(
            f"SELECT score FROM training_scores WHERE player_name = ? AND drill = ?"
            f" ORDER BY score {order} LIMIT 1",
            (player_name, drill),
        ).fetchone()
    return row[0] if row else None


def save_training_score(player_name: str, drill: str, score: float,
                        extra: dict) -> tuple[float, bool]:
    """写入成绩，返回 (历史最佳, 是否新纪录)。"""
    prev_best = best_score(player_name, drill)
    created_at = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT INTO training_scores (player_name, drill, score, extra, created_at)"
            " VALUES (?,?,?,?,?)",
            (player_name, drill, score, json.dumps(extra, ensure_ascii=False),
             created_at),
        )
    if prev_best is None:
        return score, True
    best = _better(drill, prev_best, score)
    return best, best == score and score != prev_best


def load_training_scores(player_name: str,
                         drill: str | None = None) -> tuple[list[dict], dict]:
    """返回 (成绩列表按时间倒序, 各科最佳成绩)。"""
    where = "WHERE player_name = ?"
    params: list = [player_name]
    if drill:
        where += " AND drill = ?"
        params.append(drill)
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            f"SELECT drill, score, extra, created_at FROM training_scores"
            f" {where} ORDER BY id DESC",
            params,
        ).fetchall()
    scores = [{"drill": d, "score": s, "extra": json.loads(e), "created_at": c}
              for d, s, e, c in rows]
    bests: dict[str, float] = {}
    for d, s, _, _ in rows:
        bests[d] = s if d not in bests else _better(d, bests[d], s)
    return scores, bests
