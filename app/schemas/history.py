from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.schemas.application import ApplicationResponse
from app.models.enums import Status, CSDecision


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
    """Response for list of application history entries"""
    total: int
    history: list[ApplicationHistoryResponse]
    
    class Config:
        from_attributes = True


class ApplicationHistoryPageResponse(BaseModel):
    """Response for the application history/overview page"""
    total: int
    approved_count: int
    in_progress_count: int
    rejected_count: int
    closed_count: int
    cancelled_count: int  # Added for cancellation tracking
    applications: list[ApplicationResponse]
    has_more: bool  # Pagination indicator
    current_page: int
    total_pages: int

    class Config:
        from_attributes = True
