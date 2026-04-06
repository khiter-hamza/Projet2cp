from pydantic import BaseModel
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, date
from app.schemas.application import ApplicationResponse
from app.models.enums import Status, CSDecision, StageType, Countries, UserGrade
from fastapi import Query

class StatusCount(BaseModel):
    status: Status
    count: int

class CSDecisionCount(BaseModel):
    decision: CSDecision | None
    count: int

class BudgetStatus(BaseModel):
    """Budget information for a session."""
    total_budget: float
    committed_amount: float
    percentage_used: float
    remaining_budget: float
    beneficiary_count: int  # Number of researchers funded

class ResearcherDashboardResponse(BaseModel):
    application: ApplicationResponse | None
    current_session_name: Optional[str] = None
    current_session_opened: bool = False

class AdminDashboardFilters(BaseModel):
    session_id: Optional[str] = None
    status: Optional[Status] = None
    cs_decision: Optional[CSDecision] = None
    stage_type: Optional[StageType] = None
    destination_country: Optional[Countries] = None
    zone_id: Optional[str] = None
    user_grade: Optional[UserGrade] = None
    is_eligible: Optional[bool] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0

def get_admin_dashboard_filters(
    session_id: Optional[str] = Query(None),
    status: Optional[Status] = Query(None),
    cs_decision: Optional[CSDecision] = Query(None),
    stage_type: Optional[StageType] = Query(None),
    destination_country: Optional[Countries] = Query(None),
    zone_id: str | None = Query(None),
    user_grade: Optional[UserGrade] = Query(None),
    is_eligible: Optional[bool] = Query(None),
    start_date_from: Optional[date] = Query(None),
    start_date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> AdminDashboardFilters:
    return AdminDashboardFilters(
        session_id=session_id,
        status=status,
        cs_decision=cs_decision,
        stage_type=stage_type,
        destination_country=destination_country,
        zone_id=zone_id,
        user_grade=user_grade,
        is_eligible=is_eligible,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        search=search,
        limit=limit,
        offset=offset,
    )

class AdminDashboardResponse(BaseModel):
    """Admin dashboard with comprehensive application overview."""
    total_applications: int
    applications_by_status: List[StatusCount]
    applications_by_decision: List[CSDecisionCount]
    
    # Paginated applications list
    applications: List[ApplicationResponse]
    has_more: bool
    
    # Summary counts
    eligible_count: int
    approved_count: int
    rejected_count: int
    pending_cs_count: int
    
    # Budget information
    budget_status: Optional[BudgetStatus] = None
    
    # Session info
    current_session_name: Optional[str] = None
    session_id: Optional[str] = None
    filters_applied: AdminDashboardFilters

class CSDashboardResponse(BaseModel):
    ready_for_deliberation: List[ApplicationResponse]
    total_ready: int
    average_score: float | None
    high_priority_count: int  # Score > 80
    current_session_name: Optional[str] = None

class StatisticsResponse(BaseModel):
    total_applications_all_time: int
    total_sessions: int
    current_session_applications: int
    total_users: int
    total_funding_allocated: float
    average_processing_time_days: float | None