from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSession
from app.models.application import Application
from app.models.user import User
from app.models.session import Session
from app.schemas.dashboard import *
from app.services.auth_service_utils import verify_chercheur_role, verify_cs_admin_role
from app.services.application.application_service import get_current_session
from typing import List
from uuid import UUID

async def get_researcher_dashboard(user_id: str, db: AsyncSession):
    """
    Get dashboard for researcher: their applications and status counts
    """
    user = await verify_chercheur_role(user_id, db)
    
    current_session = await get_current_session(db)
    if not current_session:
        return ResearcherDashboardResponse(
            applications=[],
            status_counts=[],
            total_applications=0,
            eligible_count=0,
            pending_count=0
        )
    
    # Get applications
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.user_id == user.id)
        .where(Application.session_id == current_session.id)
        .order_by(desc(Application.created_at))
    )
    applications = result.scalars().all()
    
    # Count by status
    status_counts = []
    eligible_count = 0
    pending_count = 0
    
    for app in applications:
        if app.is_eligible:
            eligible_count += 1
        if app.status in [Status.SUBMITTED, Status.CS_PREPARATION]:
            pending_count += 1
    
    # Group by status
    status_dict = {}
    for app in applications:
        status = app.status
        status_dict[status] = status_dict.get(status, 0) + 1
    
    for status, count in status_dict.items():
        status_counts.append(StatusCount(status=status, count=count))
    
    return ResearcherDashboardResponse(
        applications=[ApplicationResponse.model_validate(app) for app in applications],
        status_counts=status_counts,
        total_applications=len(applications),
        eligible_count=eligible_count,
        pending_count=pending_count,
        current_session_name=current_session.name if current_session else None
    )

async def get_admin_dashboard(user_id: str, db: AsyncSession, filters: AdminDashboardFilters = None):
    """
    Get dashboard for admin: applications statistics with optional filters
    """
    user = await verify_cs_admin_role(user_id, db)
    
    if filters is None:
        filters = AdminDashboardFilters()
    
    # Determine which session to use
    target_session = None
    if filters.session_id:
        # If specific session requested, use it
        result = await db.execute(
            select(Session).where(Session.id == UUID(filters.session_id))
        )
        target_session = result.scalar_one_or_none()
    else:
        # Default to current session
        target_session = await get_current_session(db)
    
    if not target_session:
        return AdminDashboardResponse(
            total_applications=0,
            applications_by_status=[],
            applications_by_decision=[],
            recent_applications=[],
            eligible_count=0,
            approved_count=0,
            rejected_count=0,
            pending_cs_count=0,
            current_session_name=None,
            filters_applied=filters
        )
    
    # Build query for applications
    query = select(Application).where(Application.session_id == target_session.id).options(selectinload(Application.documents))
    
    # Apply filters
    if filters.status:
        query = query.where(Application.status == filters.status)
    if filters.cs_decision:
        query = query.where(Application.cs_decision == filters.cs_decision)
    if filters.stage_type:
        query = query.where(Application.stage_type == filters.stage_type)
    if filters.destination_country:
        query = query.where(Application.destination_country == filters.destination_country)
    if filters.is_eligible is not None:
        query = query.where(Application.is_eligible == filters.is_eligible)
    if filters.start_date_from:
        query = query.where(Application.start_date >= filters.start_date_from)
    if filters.start_date_to:
        query = query.where(Application.start_date <= filters.start_date_to)
    
    # Join with User for user-related filters
    if filters.zone_id or filters.user_grade:
        query = query.join(Application.user)
        if filters.zone_id:
            # TODO: Implement zone filtering - zones are related to indemnities, not users
            pass
        if filters.user_grade:
            query = query.where(User.grade == filters.user_grade)
    
    # Execute query
    result = await db.execute(query.order_by(desc(Application.created_at)))
    applications = result.scalars().all()
    
    # Recent applications (last 10)
    recent_applications = applications[:10]
    
    # Count by status
    status_counts = []
    decision_counts = []
    eligible_count = 0
    approved_count = 0
    rejected_count = 0
    pending_cs_count = 0
    
    status_dict = {}
    decision_dict = {}
    
    for app in applications:
        # Status counts
        status_dict[app.status] = status_dict.get(app.status, 0) + 1
        
        # Decision counts
        decision_dict[app.cs_decision] = decision_dict.get(app.cs_decision, 0) + 1
        
        # Other counts
        if app.is_eligible:
            eligible_count += 1
        if app.cs_decision == CSDecision.approved:
            approved_count += 1
        elif app.cs_decision == CSDecision.rejected:
            rejected_count += 1
        if app.status == Status.CS_PREPARATION:
            pending_cs_count += 1
    
    for status, count in status_dict.items():
        status_counts.append(StatusCount(status=status, count=count))
    
    for decision, count in decision_dict.items():
        decision_counts.append(CSDecisionCount(decision=decision, count=count))
    
    return AdminDashboardResponse(
        total_applications=len(applications),
        applications_by_status=status_counts,
        applications_by_decision=decision_counts,
        recent_applications=[ApplicationResponse.model_validate(app) for app in recent_applications],
        eligible_count=eligible_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        pending_cs_count=pending_cs_count,
        current_session_name=target_session.name,
        filters_applied=filters
    )

async def get_cs_dashboard(user_id: str, db: AsyncSession):
    """
    Get dashboard for CS: applications ready for deliberation in current session only
    """
    user = await verify_cs_admin_role(user_id, db)
    
    current_session = await get_current_session(db)
    if not current_session:
        return CSDashboardResponse(
            ready_for_deliberation=[],
            total_ready=0,
            average_score=None,
            high_priority_count=0,
            current_session_name=None
        )
    
    # Get applications ready for CS deliberation in current session only
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.session_id == current_session.id)
        .where(Application.status == Status.CS_PREPARATION)
        .order_by(desc(Application.score))
    )
    applications = result.scalars().all()
    
    # Calculate stats
    total_ready = len(applications)
    scores = [app.score for app in applications if app.score is not None]
    average_score = sum(scores) / len(scores) if scores else None
    high_priority_count = len([app for app in applications if app.score and app.score > 80])
    
    return CSDashboardResponse(
        ready_for_deliberation=[ApplicationResponse.model_validate(app) for app in applications],
        total_ready=total_ready,
        average_score=average_score,
        high_priority_count=high_priority_count,
        current_session_name=current_session.name
    )

async def get_statistics(db: AsyncSession):
    """
    Get overall system statistics
    """
    # Total applications all time
    result = await db.execute(select(func.count(Application.id)))
    total_applications_all_time = result.scalar()
    
    # Total sessions
    result = await db.execute(select(func.count(Session.id)))
    total_sessions = result.scalar()
    
    # Current session applications
    current_session = await get_current_session(db)
    current_session_applications = 0
    if current_session:
        result = await db.execute(
            select(func.count(Application.id))
            .where(Application.session_id == current_session.id)
        )
        current_session_applications = result.scalar()
    
    # Total users
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()
    
    # Total funding allocated (sum of calculated_fees for approved applications)
    result = await db.execute(
        select(func.sum(Application.calculated_fees))
        .where(Application.cs_decision == CSDecision.approved)
    )
    total_funding_allocated = result.scalar() or 0
    
    # Average processing time (from submitted to decision)
    # This would require more complex query, for now return None
    average_processing_time_days = None
    
    return StatisticsResponse(
        total_applications_all_time=total_applications_all_time,
        total_sessions=total_sessions,
        current_session_applications=current_session_applications,
        total_users=total_users,
        total_funding_allocated=total_funding_allocated,
        average_processing_time_days=average_processing_time_days
    )