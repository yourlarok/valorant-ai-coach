import sqlite3
from datetime import datetime, timezone

from pydantic import BaseModel

from app.db import _db_path


class Notification(BaseModel):
    id: int
    type: str  # analysis_done / retest_reminder / ...
    title: str
    body: str = ""
    link: str = ""  # 前端路由，如 /report/<match_id>
    read: bool = False
    created_at: datetime


def _row_to_notification(row) -> Notification:
    return Notification(
        id=row[0], type=row[1], title=row[2], body=row[3], link=row[4],
        read=bool(row[5]), created_at=datetime.fromisoformat(row[6]),
    )


def create_notification(type: str, title: str, body: str = "", link: str = "") -> Notification:
    created_at = datetime.now(timezone.utc)
    with sqlite3.connect(_db_path()) as conn:
        cur = conn.execute(
            "INSERT INTO notifications (type, title, body, link, read, created_at)"
            " VALUES (?,?,?,?,0,?)",
            (type, title, body, link, created_at.isoformat()),
        )
        row = conn.execute(
            "SELECT id, type, title, body, link, read, created_at"
            " FROM notifications WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
    return _row_to_notification(row)


def list_notifications(unread_only: bool = False) -> tuple[list[Notification], int]:
    with sqlite3.connect(_db_path()) as conn:
        unread = conn.execute(
            "SELECT COUNT(*) FROM notifications WHERE read = 0"
        ).fetchone()[0]
        sql = "SELECT id, type, title, body, link, read, created_at FROM notifications"
        if unread_only:
            sql += " WHERE read = 0"
        sql += " ORDER BY id DESC"
        rows = conn.execute(sql).fetchall()
    return [_row_to_notification(r) for r in rows], unread


def mark_notification_read(notification_id: int) -> bool:
    with sqlite3.connect(_db_path()) as conn:
        cur = conn.execute(
            "UPDATE notifications SET read = 1 WHERE id = ?", (notification_id,),
        )
        return cur.rowcount > 0


def mark_all_notifications_read() -> int:
    with sqlite3.connect(_db_path()) as conn:
        cur = conn.execute("UPDATE notifications SET read = 1 WHERE read = 0")
        return cur.rowcount
