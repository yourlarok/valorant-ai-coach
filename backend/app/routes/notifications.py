from fastapi import APIRouter, HTTPException

from app import notifications

router = APIRouter(prefix="/api")


@router.get("/notifications")
def get_notifications(unread_only: bool = False):
    items, unread = notifications.list_notifications(unread_only)
    return {"items": items, "unread": unread}


@router.post("/notifications/{notification_id}/read")
def read_notification(notification_id: int):
    if not notifications.mark_notification_read(notification_id):
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"ok": True}


@router.post("/notifications/read-all")
def read_all_notifications():
    updated = notifications.mark_all_notifications_read()
    return {"ok": True, "updated": updated}
