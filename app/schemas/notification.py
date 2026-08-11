from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Notification(BaseModel):
    id: int
    user_id: str
    type: str
    title: str
    message: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    user_id: str
    type: str = "general"
    title: str
    message: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None


class NotificationList(BaseModel):
    total: int
    unread: int
    items: List[Notification]
