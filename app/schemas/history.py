from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ApplicationHistoryResponse(BaseModel):
    """Response for application history entries"""
    id: UUID
    application_id: UUID
    previous_status: Optional[str] = None
    new_status: str
    action: str
    description: Optional[str] = None
    changed_by: Optional[UUID] = None
    changed_at: datetime
    verification_result: Optional[str] = None
    verification_details: Optional[str] = None
    
    class Config:
        from_attributes = True


class ApplicationHistoryListResponse(BaseModel):
    """Response for list of application history"""
    total: int
    history: list[ApplicationHistoryResponse]
    
    class Config:
        from_attributes = True
