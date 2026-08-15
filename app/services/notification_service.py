from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.role import Role
from app.models.user import User
from app.schemas.notification import NotificationCreate
from app.services.ws_manager import publish_notification_sync


def serialize_notification(notification: Notification) -> dict:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "reference_type": notification.reference_type,
        "reference_id": notification.reference_id,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat()
        if notification.created_at
        else datetime.utcnow().isoformat(),
    }


def get_notifications(
    db: Session, user_id: str, skip: int = 0, limit: int = 100
) -> List[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_unread_count(db: Session, user_id: str) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count()
    )


def get_notification(db: Session, notification_id: int, user_id: str) -> Optional[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )


def mark_as_read(db: Session, notification_id: int, user_id: str) -> Optional[Notification]:
    notification = get_notification(db, notification_id, user_id)
    if not notification:
        return None
    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: str) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return updated


def get_admin_users(db: Session) -> List[User]:
    return (
        db.query(User)
        .filter(or_(User.is_admin.is_(True), User.role.has(Role.name == "admin")))
        .all()
    )


def create_admin_notifications(
    db: Session,
    title: str,
    message: Optional[str] = None,
    notification_type: str = "general",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> List[Notification]:
    """Create a notification for every admin user."""
    created: List[Notification] = []
    for admin in get_admin_users(db):
        created.append(
            create_notification(
                db=db,
                user_id=admin.id,
                title=title,
                message=message,
                notification_type=notification_type,
                reference_type=reference_type,
                reference_id=reference_id,
            )
        )
    return created


def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: Optional[str] = None,
    notification_type: str = "general",
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=str(reference_id) if reference_id is not None else None,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    publish_notification_sync(user_id, _realtime_payload(notification))
    return notification


def create_notification_from_schema(db: Session, data: NotificationCreate) -> Notification:
    return create_notification(
        db=db,
        user_id=data.user_id,
        title=data.title,
        message=data.message,
        notification_type=data.type,
        reference_type=data.reference_type,
        reference_id=data.reference_id,
    )


def _realtime_payload(notification: Notification) -> dict:
    payload = serialize_notification(notification)
    return {
        "event": "notification",
        "data": payload,
    }