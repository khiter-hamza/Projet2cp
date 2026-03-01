import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import NotificationType


class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    read_at: Optional[datetime] = None
    demande_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    unread_count: int
