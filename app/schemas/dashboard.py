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

class ResearcherDashboardResponse(BaseModel):
    applications: List[ApplicationResponse]
    status_counts: List[StatusCount]
    total_applications: int
    eligible_count: int
    pending_count: int
    current_session_name: Optional[str] = None

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
    )

class AdminDashboardResponse(BaseModel):
    total_applications: int
    applications_by_status: List[StatusCount]
    applications_by_decision: List[CSDecisionCount]
    recent_applications: List[ApplicationResponse]  # Last 10
    eligible_count: int
    approved_count: int
    rejected_count: int
    pending_cs_count: int
    current_session_name: Optional[str] = None
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