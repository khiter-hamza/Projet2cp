"""
CS (Commission Scientifique) Schemas

Request/Response models for CS Workflow operations:
- Deliberation preparation
- Decision making (approve/reject)
- Dashboard and statistics
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from app.models.enums import CSDecision, Status, StageType, UserGrade, Countries


# ============================================================================
# Request Schemas
# ============================================================================

class CSDecisionRequest(BaseModel):
    """Request body for CS decision (approve/reject)"""
    decision: str = Field(..., description="'approuve' or 'rejete'")
    notes: Optional[str] = Field(None, description="Additional notes or rejection reason")
    
    class Config:
        example = {
            "decision": "approuve",
            "notes": "Excellent candidate, highly recommended"
        }


# ============================================================================
# Response Schemas
# ============================================================================

class CSPreparationResponse(BaseModel):
    """Response from CS preparation endpoint"""
    message: str
    session_id: str
    session_name: str
    total_applications: int
    ready_for_deliberation: bool
    
    class Config:
        from_attributes = True


class CSDashboardApplication(BaseModel):
    """Single application in CS dashboard"""
    id: str = Field(..., description="Application UUID")
    user_name: str = Field(..., description="Full name of applicant (username + lastname)")
    user_grade: UserGrade | None = Field(None, description="User's academic grade")
    stage_type: StageType | None = Field(None, description="Type of stage/séjour")
    destination_country: Countries | None = Field(None, description="Destination country")
    host_institution: str | None = Field(None, description="Host institution name")
    start_date: date | None = Field(None, description="Stage/séjour start date")
    end_date: date | None = Field(None, description="Stage/séjour end date")
    score: float | None = Field(None, description="Application score (for CS recommendation)")
    is_eligible: bool | None = Field(None, description="Eligibility verification result")
    status: Status = Field(..., description="Current application status")
    submitted_at: datetime | None = Field(None, description="Submission timestamp")
    session_id: str | None = Field(None, description="Session UUID")
    cs_decision: CSDecision | None = Field(None, description="CS decision status (if made)")
    rejection_reason: str | None = Field(None, description="Rejection reason (if rejected)")
    
    class Config:
        from_attributes = True


class CSDashboardResponse(BaseModel):
    """CS dashboard response with list of applications ready for review"""
    count: int = Field(..., description="Total number of applications ready for CS")
    applications: List[CSDashboardApplication] = Field(
        ..., 
        description="List of applications in CS_PREPARATION status, sorted by score"
    )
    
    class Config:
        from_attributes = True


class CSDecisionResponse(BaseModel):
    """Response from CS decision endpoint (approve/reject)"""
    message: str = Field(..., description="Confirmation message")
    application_id: str = Field(..., description="Application UUID")
    cs_decision: CSDecision = Field(..., description="Decision made: approuve or rejete")
    status: Status = Field(..., description="New application status")
    approved_at: datetime | None = Field(None, description="Approval timestamp (if approved)")
    rejected_at: datetime | None = Field(None, description="Rejection timestamp (if rejected)")
    rejection_reason: str | None = Field(None, description="Reason (if rejected)")
    
    class Config:
        from_attributes = True


class CSStatisticsResponse(BaseModel):
    """CS decision statistics"""
    total_decisions: int = Field(..., description="Total number of CS decisions made")
    approved: int = Field(..., description="Number of approved applications")
    rejected: int = Field(..., description="Number of rejected applications")
    approval_rate: str = Field(..., description="Percentage of approved applications")
    
    class Config:
        from_attributes = True
