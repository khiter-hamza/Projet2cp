from pydantic import BaseModel , Field
from uuid import UUID
from app.models.enums import *
from datetime import date , datetime
from typing import Literal, List
from fastapi import Query

class ApplicationResponse(BaseModel):
    """Représentation des champs de la table Application (sans relations)"""
    id: UUID
    user_id: UUID
    session_id: UUID | None = None
    
    stage_type: StageType
    status: Status
    
    start_date: date | None = None
    end_date: date | None = None

    host_institution: str | None = None
    host_supervisor : str | None = None
    supervisor_email : str | None = None
    host_department : str | None = None
    title_of_stay : str | None = None
    research_axis : str | None = None
    expected_outcomes : str | None = None
    destination_country: str | None = None
    destination_city: str | None = None
    
    scientific_objective: str | None = None
    
    score: float | None = None
    
    is_eligible: bool | None = None
    verification_errors: str | None = None
    
    cs_decision: CSDecision | None = None
    rejection_reason: str | None = None
    
    stage_report_id: UUID | None = None
    stage_report_submitted: bool = False
    stage_report_submitted_at: datetime | None = None
    
    attestation_id: UUID | None = None
    attestation_submitted: bool = False
    attestation_submitted_at: datetime | None = None
    
    calculated_fees: float | None = None
    
    cancellation_reason: str | None = None
    action_confirmation_by_id: UUID | None = None

    created_at: datetime
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    completed_at: datetime | None = None
    closed_at: datetime | None = None
    cancelled_at: datetime | None = None

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
    host_institution: str | None = None
    host_supervisor : str | None = None
    supervisor_email : str | None = None
    host_department : str | None = None
    title_of_stay : str | None = None
    research_axis : str | None = None
    expected_outcomes : str | None = None
    scientific_objective: str | None = None

    destination_country: str | None = None
    destination_city: str | None = None
    class Config:
        from_attributes = True

class flag_reason(BaseModel):
    reason:str   

class ApplicationSubmission(BaseModel):
    """Schema de validation avant soumission"""
    id: UUID
    user_id: UUID
    status: Status
    stage_type: StageType 
    start_date: date 
    end_date: date 
    host_institution: str 
    host_supervisor : str 
    supervisor_email : str
    host_department : str 
    title_of_stay : str 
    research_axis : str 
    expected_outcomes : str 
    destination_country: str 
    destination_city: str 
    scientific_objective: str 
    created_at: datetime
    submitted_at: datetime | None = None
    
    class Config:
        from_attributes = True

class ApplicationFilterParams(BaseModel):
    # --- Pagination ---
    skip: int = 0
    limit: int = 20

    # --- Sorting ---
    sort_by: Literal[
        "submitted_at", "created_at", "approved_at", "rejected_at",
        "stage_type", "destination_country", "host_institution",
        "cs_decision", "score", "calculated_fees"
    ] = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
    
    # --- Basic Filters ---
    status: Status | None = None
    user_id: UUID | None = None
    session_id: UUID | None = None
    stage_type: StageType | None = None
    destination_country: str | None = None
    user_grade: UserGrade | None = None
    cs_decision: CSDecision | None = None
    
    # --- Quantitative Filters ---
    min_score: float | None = None
    max_score: float | None = None
    is_eligible: bool | None = None
    
    # --- Document Workflow Filters ---
    has_report: bool | None = None
    has_attestation: bool | None = None
    
    # --- Date Ranges (Trip & Submission) ---
    start_date_from: date | None = None
    start_date_to: date | None = None
    submitted_after: date | None = None
    submitted_before: date | None = None
    
    # --- Text Search ---
    search: str | None = None

def get_filter_params(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    status: Status | None = Query(None),
    user_id: UUID | None = Query(None),
    session_id: UUID | None = Query(None),
    stage_type: StageType | None = Query(None),
    destination_country: str | None = Query(None),
    user_grade: UserGrade | None = Query(None),
    cs_decision: CSDecision | None = Query(None),
    min_score: float | None = Query(None),
    max_score: float | None = Query(None),
    is_eligible: bool | None = Query(None),
    has_report: bool | None = Query(None),
    has_attestation: bool | None = Query(None),
    start_date_from: date | None = Query(None),
    start_date_to: date | None = Query(None),
    submitted_after: date | None = Query(None),
    submitted_before: date | None = Query(None),
    search: str | None = Query(None),
) -> ApplicationFilterParams:
    return ApplicationFilterParams(
        skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order,
        status=status, user_id=user_id, session_id=session_id,
        stage_type=stage_type, destination_country=destination_country,
        user_grade=user_grade, cs_decision=cs_decision,
        min_score=min_score, max_score=max_score,
        is_eligible=is_eligible, has_report=has_report,
        has_attestation=has_attestation,
        start_date_from=start_date_from, start_date_to=start_date_to,
        submitted_after=submitted_after, submitted_before=submitted_before,
        search=search
    )
