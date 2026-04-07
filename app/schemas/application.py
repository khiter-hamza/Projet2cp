from pydantic import BaseModel , Field
from uuid import UUID
from app.models.enums import *
from datetime import date , datetime
from typing import Literal, List
from fastapi import Query
from app.schemas.document import DocumentResponse

#all models has a relation with application

class ApplicationResponse(BaseModel):
    """Réponse complète"""
    id: UUID
    user_id: UUID
    status: Status
    stage_type: StageType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    destination_country: Countries | None = None
    destination_city: str | None = None
    host_institution: str | None = None
    scientific_objective: str | None = None
    score: float | None = None
    is_eligible: bool | None = None
    verified_at: datetime | None = None
    verification_errors: str | None = None
    cs_decision: CSDecision | None = None
    rejection_reason: str | None = None
    cancellation_reason: str | None = None
    cancelled_at: datetime | None = None
    calculated_fees: float | None = None
    created_at: datetime
    submitted_at: datetime | None = None
    documents: List[DocumentResponse] = []
    
    class Config:
        from_attributes = True

class ApplicationCancellationRequest(BaseModel):
    """Request body for researcher cancellation after approval."""
    reason: str

    class Config:
        example = {
            "reason": "Visa refused by the host country"
        }

class ApplicationUpsert(BaseModel):
    """Pour créer OU modifier un brouillon"""
    start_date: date | None = None
    end_date: date | None = None
    destination_country: Countries | None = None
    destination_city: str | None = None
    host_institution: str | None = Field(None, max_length=255)
    scientific_objective: str | None = None
    class Config:
        from_attributes = True

class ApplicationSubmission(BaseModel):
    """Réponse complète"""
    id: UUID
    user_id: UUID
    status: Status
    stage_type: StageType 
    start_date: datetime 
    end_date: datetime 
    destination_country: Countries 
    destination_city: str 
    host_institution: str 
    scientific_objective: str 
    created_at: datetime
    submitted_at: datetime | None = None
    
    class Config:
        from_attributes = True

class ApplicationFilterParams(BaseModel):
    # Sort
    sort_by: Literal[
        "submitted_at",
        "created_at",
        "approved_at",
        "rejected_at",
        "status",
        "stage_type",
        "destination_country",
        "host_institution",
        "cs_decision",
        "zone",
        "user_grade",
        "duration_days",
        "session_id"
    ] = "submitted_at"
    sort_order: Literal["asc", "desc"] = "desc"
    
    # Filters
    status: Status | None = None
    user_id: str | None = None
    session_id: str | None = None
    stage_type: StageType | None = None
    destination_country: Countries | None = None
    cs_decision: CSDecision | None = None
    is_eligible: bool | None = None
    zone_id: str | None = None
    user_grade: UserGrade | None = None
    # Date Range
    start_date_from: date | None = None
    start_date_to: date | None = None
    
    # Search
    search: str | None = None

def get_filter_params(
        sort_by: Literal[
        "submitted_at",
        "created_at",
        "approved_at",
        "rejected_at",
        "stage_type",
        "destination_country",
        "host_institution",
        "cs_decision",
        "zone",
        "user_grade",
        "duration_days",
        "session_id"
    ] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    status: Status | None = Query(None),
    user_id: str | None = Query(None),
    session_id: str | None = Query(None),
    stage_type: StageType | None = Query(None),
    destination_country: Countries | None = Query(None),
    cs_decision: CSDecision | None = Query(None),
    is_eligible: bool | None = Query(None),
    zone_id: str | None = Query(None),
    user_grade: UserGrade | None = Query(None),
    start_date_from: date | None = Query(None),
    start_date_to: date | None = Query(None),
    search: str | None = Query(None),
) -> ApplicationFilterParams:
    return ApplicationFilterParams(
        sort_by=sort_by,
        sort_order=sort_order,
        status=status,
        user_id=user_id,
        session_id=session_id,
        stage_type=stage_type,
        destination_country=destination_country,
        cs_decision=cs_decision,
        is_eligible=is_eligible,
        zone_id=zone_id,
        user_grade=user_grade,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        search=search,
    )