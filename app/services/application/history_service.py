from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy import select, or_, String
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSession
from app.models.application import Application
from app.models.enums import UserRole, Status, CSDecision
from app.schemas.application import ApplicationResponse
from app.schemas.history import (
    ApplicationHistoryListResponse,
    ApplicationHistoryResponse,
    ApplicationHistoryPageResponse,
)
from app.services.auth_service_utils import verify_cs_admin_or_chercheur


def _to_verification_result(is_eligible: bool | None) -> str | None:
    if is_eligible is None:
        return None
    return "eligible" if is_eligible else "ineligible"


async def get_application_history(
    application_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> ApplicationHistoryListResponse:
    current_user = await verify_cs_admin_or_chercheur(user_id, db)

    result = await db.execute(select(Application).where(Application.id == application_id))
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == UserRole.chercheur and application.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this application history")

    entries: list[ApplicationHistoryResponse] = []

    def add_event(
        changed_at,
        action: str,
        new_status,
        description: str | None = None,
        verification_result: str | None = None,
        verification_details: str | None = None,
        changed_by: UUID | None = None,
    ):
        if not changed_at:
            return
        previous_status = entries[-1].new_status if entries else None
        entries.append(ApplicationHistoryResponse(
            id=uuid4(),
            application_id=application.id,
            previous_status=previous_status,
            new_status=new_status,
            action=action,
            description=description,
            changed_by=changed_by,
            changed_at=changed_at,
            verification_result=verification_result,
            verification_details=verification_details,
        ))

    add_event(
        application.created_at,
        action="draft_created",
        new_status=Status.DRAFT,
        description="Draft created",
        changed_by=application.user_id,
    )
    add_event(
        application.submitted_at,
        action="submitted",
        new_status=Status.SUBMITTED,
        description="Application submitted",
        changed_by=application.user_id,
    )
    add_event(
        application.verified_at,
        action="verification_completed",
        new_status=application.status,
        description="Eligibility verification completed",
        verification_result=_to_verification_result(application.is_eligible),
        verification_details=application.verification_errors,
    )
    if application.cs_decision == CSDecision.approuve:
        add_event(
            application.approved_at,
            action="approved",
            new_status=Status.APPROVED,
            description="Application approved",
        )
    elif application.cs_decision == CSDecision.rejete:
        add_event(
            application.rejected_at,
            action="rejected",
            new_status=Status.REJECTED,
            description="Application rejected",
        )
    add_event(
        application.stage_report_submitted_at,
        action="stage_report_submitted",
        new_status=application.status,
        description="Stage report submitted",
    )
    add_event(
        application.attestation_submitted_at,
        action="attestation_submitted",
        new_status=application.status,
        description="Attestation submitted",
    )
    add_event(
        application.completed_at,
        action="completed",
        new_status=Status.COMPLETED,
        description="Application completed",
    )
    add_event(
        application.closed_at,
        action="closed",
        new_status=Status.CLOSED,
        description="Application closed",
    )
    add_event(
        application.cancelled_at,
        action="cancelled",
        new_status=Status.CANCELLED,
        description=f"Application cancelled. Reason: {application.cancellation_reason}"
        if application.cancellation_reason else "Application cancelled",
    )

    sliced_entries = entries[offset : offset + limit]
    return ApplicationHistoryListResponse(total=len(entries), history=sliced_entries)


async def get_application_history_page(
    user_id: UUID,
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "submitted_at",
    sort_order: str = "desc",
    status: Status | None = None,
    cs_decision: CSDecision | None = None,
    search: str | None = None,
    session_filter: str = "this",
) -> ApplicationHistoryPageResponse:
    """
    Get application history page with filtering and pagination.
    
    session_filter options:
    - "this": Current session only
    - "previous": Previous sessions only
    - "all": All sessions
    """
    from app.services.application.application_service import get_current_session
    
    current_user = await verify_cs_admin_or_chercheur(user_id, db)

    query = select(Application).options(selectinload(Application.documents))

    if current_user.role == UserRole.chercheur:
        query = query.where(Application.user_id == user_id)

    # Handle session filtering
    if session_filter == "this":
        current_session = await get_current_session(db)
        if current_session:
            query = query.where(Application.session_id == current_session.id)
    elif session_filter == "previous":
        current_session = await get_current_session(db)
        if current_session:
            query = query.where(Application.session_id != current_session.id)
    # "all" doesn't filter by session

    if status:
        query = query.where(Application.status == status)
    if cs_decision:
        query = query.where(Application.cs_decision == cs_decision)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Application.host_institution.ilike(search_term),
                Application.destination_city.ilike(search_term),
                Application.scientific_objective.ilike(search_term),
                Application.id.cast(String).ilike(search_term),
            )
        )

    sort_column = getattr(Application, sort_by, Application.submitted_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    result = await db.execute(query)
    applications = result.scalars().all()

    total = len(applications)
    page = applications[offset : offset + limit]
    has_more = (offset + limit) < total
    current_page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    approved_count = sum(1 for app in applications if app.status == Status.APPROVED)
    in_progress_count = sum(1 for app in applications if app.status in [Status.SUBMITTED, Status.CS_PREPARATION])
    rejected_count = sum(1 for app in applications if app.status == Status.REJECTED)
    closed_count = sum(1 for app in applications if app.status == Status.CLOSED)
    cancelled_count = sum(1 for app in applications if app.status == Status.CANCELLED)

    return ApplicationHistoryPageResponse(
        total=total,
        approved_count=approved_count,
        in_progress_count=in_progress_count,
        rejected_count=rejected_count,
        closed_count=closed_count,
        cancelled_count=cancelled_count,
        applications=[ApplicationResponse.model_validate(app) for app in page],
        has_more=has_more,
        current_page=current_page,
        total_pages=total_pages,
    )
