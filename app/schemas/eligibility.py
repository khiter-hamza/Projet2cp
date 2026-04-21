from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class EligibilityCheckResult(BaseModel):
    """Result of eligibility verification"""
    is_eligible: bool
    
    # Details
    eligible_by_grade: bool
    eligible_by_history: bool
    eligible_by_documents: bool
    
    # Errors if ineligible
    errors: List[str]
    
    class Config:
        from_attributes = True


class HistoryCheckDetail(BaseModel):
    """Details about user's application history"""
    total_applications: int
    completed_applications: int
    total_days_consumed: int
    last_stage_date: Optional[datetime] = None
    days_since_last_stage: Optional[int] = None
    
    class Config:
        from_attributes = True


class DocumentCheckDetail(BaseModel):
    """Details about required documents"""
    required_documents: List[str]
    uploaded_documents: List[str]
    missing_documents: List[str]
    all_documents_present: bool
    
    class Config:
        from_attributes = True


class EligibilityDetailedResponse(BaseModel):
    """Complete eligibility check response"""
    application_id: UUID
    is_eligible: bool
    verified_at: datetime
    
    errors: List[str]
    
    class Config:
        from_attributes = True
