from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from jose import JWTError

from app.api import deps
from app.core.security import decode_token
from app.models.user import User
from app.schemas.notification import Notification as NotificationSchema, NotificationList
from app.services import notification_service
from app.services.ws_manager import manager

router = APIRouter()
ws_router = APIRouter()


async def _authenticate_ws(websocket: WebSocket) -> User:
    token = None
    token = websocket.query_params.get("token")
    if not token and "access_token" in websocket.cookies:
        token = websocket.cookies["access_token"]
    if not token:
        return None

    try:
        payload = decode_token(token)
        if payload is None or not payload.sub:
            return None
        user_id = payload.sub
    except JWTError:
        return None

    db = next(deps.get_db())
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


@ws_router.websocket("/ws/notifications")
async def notification_ws(websocket: WebSocket) -> None:
    user = await _authenticate_ws(websocket)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user.id)
    try:
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)


@router.get("", response_model=NotificationList)
def read_notifications(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    List the current user's notifications (newest first).
    """
    items = notification_service.get_notifications(db, current_user.id, skip=skip, limit=limit)
    unread = notification_service.get_unread_count(db, current_user.id)
    return NotificationList(total=len(items), unread=unread, items=items)


@router.get("/unread-count")
def read_unread_count(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Number of unread notifications for the current user.
    """
    return {
        "unread": notification_service.get_unread_count(db, current_user.id),
    }


@router.post("/{notification_id}/read", response_model=NotificationSchema)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Mark a single notification as read.
    """
    notification = notification_service.mark_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return notification


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Mark all notifications as read for the current user.
    """
    updated = notification_service.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read", "updated": updated}