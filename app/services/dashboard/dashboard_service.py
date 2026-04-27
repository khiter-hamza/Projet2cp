from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSession
from app.models.application import Application
from app.models.user import User
from app.models.session import Session
from app.models.enums import Status
from app.schemas.application import ApplicationResponse
from app.schemas.dashboard import *
from app.services.auth_service_utils import verify_chercheur_role, verify_cs_admin_role
from app.services.application.application_service import get_current_session
from typing import List
from uuid import UUID

FUNDED_STATUSES = {
    Status.APPROVED,
    Status.COMPLETED,
    Status.CANCELLATION_REQUEST,
    Status.CORRECTION_NEEDED,
    Status.CLOSED,
}

async def get_researcher_current_application(user_id: str, db: AsyncSession) -> ApplicationResponse | None:
    """Get the current session application details for the researcher."""
    user = await verify_chercheur_role(user_id, db)
    current_session = await get_current_session(db)
    if not current_session:
        return None

    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.user_id == user.id)
        .where(Application.session_id == current_session.id)
        .order_by(desc(Application.created_at))
        .limit(1)
    )
    application = result.scalar_one_or_none()
    return ApplicationResponse.model_validate(application) if application else None

async def get_researcher_dashboard(user_id: str, db: AsyncSession):
    """
    Get dashboard for researcher: their applications and status counts
    """
    user = await verify_chercheur_role(user_id, db)
    
    current_session = await get_current_session(db)
    if not current_session:
        return ResearcherDashboardResponse(
            application=None,
            current_session_name=None,
            current_session_opened=False
        )
    
    # Get applications for this user in the current open session
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.user_id == user.id)
        .where(Application.session_id == current_session.id)
        .order_by(desc(Application.created_at))
        .limit(1)
    )
    application = result.scalar_one_or_none()
    
    return ResearcherDashboardResponse(
        application=ApplicationResponse.model_validate(application) if application else None,
        current_session_name=current_session.name,
        current_session_opened=True
    )

async def get_admin_dashboard(user_id: str, db: AsyncSession, filters: AdminDashboardFilters = None):
    """
    Get dashboard for admin: applications statistics with optional filters and pagination
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
            applications=[],
            has_more=False,
            eligible_count=0,
            approved_count=0,
            rejected_count=0,
            pending_cs_count=0,
            budget_status=None,
            current_session_name=None,
            session_id=None,
            filters_applied=filters
        )
    
    # Build base query for applications
    base_query = select(Application).where(Application.session_id == target_session.id).options(selectinload(Application.documents))
    
    # Apply filters
    if filters.status:
        base_query = base_query.where(Application.status == filters.status)
    if filters.cs_decision:
        base_query = base_query.where(Application.cs_decision == filters.cs_decision)
    if filters.stage_type:
        base_query = base_query.where(Application.stage_type == filters.stage_type)
    if filters.destination_country:
        base_query = base_query.where(Application.destination_country == filters.destination_country)
    if filters.is_eligible is not None:
        base_query = base_query.where(Application.is_eligible == filters.is_eligible)
    if filters.start_date_from:
        base_query = base_query.where(Application.start_date >= filters.start_date_from)
    if filters.start_date_to:
        base_query = base_query.where(Application.start_date <= filters.start_date_to)
    if filters.search:
        search_term = f"%{filters.search}%"
        base_query = base_query.where(
            or_(
                Application.host_institution.ilike(search_term),
                Application.destination_city.ilike(search_term),
                Application.scientific_objective.ilike(search_term),
            )
        )
    
    # Join with User for user-related filters
    if filters.zone_id or filters.user_grade:
        base_query = base_query.join(Application.user)
        if filters.user_grade:
            base_query = base_query.where(User.grade == filters.user_grade)
    
    # Execute query to get all applications
    result = await db.execute(base_query.order_by(desc(Application.submitted_at)))
    all_applications = result.scalars().all()
    total_applications = len(all_applications)
    
    # Paginate
    paginated_apps = all_applications[filters.offset:filters.offset + filters.limit]
    has_more = (filters.offset + filters.limit) < total_applications
    
    # Count by status and calculate metrics (from all results)
    status_counts = []
    decision_counts = []
    eligible_count = 0
    approved_count = 0
    rejected_count = 0
    pending_cs_count = 0
    total_committed = 0
    beneficiary_set = set()
    
    status_dict = {}
    decision_dict = {}
    
    for app in all_applications:
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
        if app.status == Status.SUBMITTED:
            pending_cs_count += 1
        
        # Budget tracking for applications that reserve or already consumed of session 
        if app.calculated_fees and app.status in FUNDED_STATUSES:
            total_committed += app.calculated_fees
            beneficiary_set.add(app.user_id)
    
    for status, count in status_dict.items():
        status_counts.append(StatusCount(status=status, count=count))
    
    for decision, count in decision_dict.items():
        decision_counts.append(CSDecisionCount(decision=decision, count=count))
    
    total_budget = float(target_session.budget or 0)
    budget_status = BudgetStatus(
        total_budget=total_budget,
        committed_amount=total_committed,
        percentage_used=(total_committed / total_budget * 100) if total_budget > 0 else 0.0,
        remaining_budget=max(0, total_budget - total_committed),
        beneficiary_count=len(beneficiary_set)
    )
    
    return AdminDashboardResponse(
        total_applications=total_applications,
        applications_by_status=status_counts,
        applications_by_decision=decision_counts,
        applications=[ApplicationResponse.model_validate(app) for app in paginated_apps],
        has_more=has_more,
        eligible_count=eligible_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        pending_cs_count=pending_cs_count,
        budget_status=budget_status,
        current_session_name=target_session.name,
        session_id=str(target_session.id),
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
        .where(Application.status == Status.SUBMITTED)
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
