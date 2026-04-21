from fastapi import HTTPException, Response , Depends
from uuid import UUID
from datetime import datetime, date
from pydantic import ValidationError
from sqlalchemy import select, func, desc, asc, or_, String
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSession
from app.schemas.application import *
from app.models.application import Application
from app.models.user import User
from app.models.session import Session
from app.models.enums import *
from app.services.evaluation.criteria_service import calculate_score
from app.services.application.eligibility_service import perform_eligibility_check
from app.services.financial.indemnity_service import generate_indemnity_for_application
from app.core.database import AsyncSessionLocal, get_db
from app.services.auth_service_utils import (
    verify_chercheur_role,
    verify_cs_admin_role,
    verify_cs_admin_or_chercheur,
    verify_ownership
)
from app.services.notification.notification_service import create_notification, notify_admins
from app.models.enums import NotificationType

async def getCurrentApplication(db: AsyncSession, user_id: UUID):
    current_session = await get_current_session(db)
    await verify_chercheur_role(user_id=user_id,db=db)
    
    if not current_session:
        raise HTTPException(status_code=400, detail="No active session available")

    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.user_id == user_id, Application.session_id == current_session.id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return ApplicationResponse.model_validate(application)


async def getUserApplication(app_id: UUID, user_id: UUID, db: AsyncSession):
    """
    Get an application.
    
    Authorization:
    - chercheur: Can only get own applications
    - CS admin:  Can get any application
    """
    user = await verify_cs_admin_or_chercheur(user_id, db)
    
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.id == app_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Chercheur can only see own applications
    if user.role == UserRole.chercheur and application.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this application")
    
    return ApplicationResponse.model_validate(application)


async def createDraft(data: ApplicationUpsert, db: AsyncSession, user_id: UUID):
    """
    Create a new draft application.
    
    Authorization: chercheur only
    Restrictions: Max 1 draft per user at a time, must be in current session
    """
    user = await verify_chercheur_role(user_id, db)
    
    # Get current session
    current_session = await get_current_session(db)
    if not current_session:
        raise HTTPException(status_code=400, detail="No active session available for creating applications")
    
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user_id)
        .where(Application.status == Status.DRAFT)
        .where(Application.session_id == current_session.id)
    )
    existing_draft = result.scalar_one_or_none()
    
    if existing_draft:
        raise HTTPException(status_code=409, detail="A draft already exists for this user in the current session")
    
    application = Application(user_id=user.id, session_id=current_session.id, **data.model_dump())
    
    if user.grade in (UserGrade.doctorant_non_salarie, UserGrade.doctorant_salarie):
        application.stage_type = StageType.stage_perfectionnement
    else:
        application.stage_type = StageType.sejour_scientifique
    
    try:
        db.add(application)
        await db.commit()
        await db.refresh(application)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Load documents relationship
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.id == application.id)
    )
    application_with_docs = result.scalar_one()
    return ApplicationResponse.model_validate(application_with_docs)


async def updateDraft(app_id: UUID, data: ApplicationUpsert, db: AsyncSession, user_id: UUID):
    """
    Update a draft application.
    
    Authorization: chercheur only (own application)
    """
    user = await verify_chercheur_role(user_id, db)
    
    # Get current session
    current_session = await get_current_session(db)
    if not current_session:
        raise HTTPException(status_code=400, detail="No active session available")
    
    draft = await db.get(Application, app_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Verify ownership
    await verify_ownership(draft.user_id, user_id)
    
    # Verify session
    if draft.session_id != current_session.id:
        raise HTTPException(status_code=403, detail="Application is not in the current session")
    
    if draft.status != Status.DRAFT:
        raise HTTPException(status_code=403, detail="Only drafts can be updated")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    
    try:
        await db.commit()
        await db.refresh(draft)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Load documents relationship
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.id == draft.id)
    )
    draft_with_docs = result.scalar_one()
    return ApplicationResponse.model_validate(draft_with_docs)


async def listApplications(db: AsyncSession, user_id: UUID, appFilterQuery: ApplicationFilterParams ):
    """
    List applications.
    
    Authorization:
    - chercheur: Can only list own applications in current session
    - CS admin:  Can list all applications in current session
    """
    user = await verify_cs_admin_or_chercheur(user_id, db)
    
    filters = appFilterQuery.model_dump()
    query = select(Application).join(Application.user).options(selectinload(Application.documents))  # Join for user filters and load documents
    
    # Default filter: current session
    current_session = await get_current_session(db)
    if current_session:
        query = query.where(Application.session_id == current_session.id)
    
    # Chercheur can only see own applications
    if user.role == UserRole.chercheur:
        query = query.where(Application.user_id == user_id)
    
    if filters.get("status"):
        query = query.where(Application.status == filters["status"])    
    
    if filters.get("user_id"):
        # CS admin can filter by user_id, chercheur cannot
        if user.role == UserRole.chercheur:
            raise HTTPException(status_code=403, detail="Cannot filter by other user_id")
        query = query.where(Application.user_id == UUID(filters["user_id"]))
    
    if filters.get("session_id"):
        query = query.where(Application.session_id == UUID(filters["session_id"]))
    
    if filters.get("stage_type"):
        query = query.where(Application.stage_type == filters["stage_type"])
    
    if filters.get("destination_country"):
        query = query.where(Application.destination_country == filters["destination_country"])
    
    if filters.get("cs_decision"):
        query = query.where(Application.cs_decision == filters["cs_decision"])
    
    if filters.get("is_eligible") is not None:
        query = query.where(Application.is_eligible == filters["is_eligible"])
    
    if filters.get("zone_id"):
        # TODO: Implement zone filtering - zones are related to indemnities, not users
        pass
    
    if filters.get("user_grade"):
        query = query.where(User.grade == filters["user_grade"])
    
    if filters.get("start_date_from"):
        query = query.where(Application.start_date >= filters["start_date_from"])
    
    if filters.get("start_date_to"):
        query = query.where(Application.start_date <= filters["start_date_to"])
    
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.where(
            or_(
                User.username.ilike(search_term),
                Application.scientific_objective.ilike(search_term),
                Application.host_institution.ilike(search_term),
                Application.destination_city.ilike(search_term),
                Application.id.cast(String).ilike(search_term)
            )
        )
    
    # Sorting
    sort_by = filters.get("sort_by", "submitted_at")
    if sort_by == "zone":
        sort_column = User.zone
    elif sort_by == "user_grade":
        sort_column = User.grade
    elif sort_by == "session_id":
        sort_column = Application.session_id
    else:
        sort_column = getattr(Application, sort_by, Application.created_at)
    
    if filters.get("sort_order") == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    result = await db.execute(query)
    applications = result.scalars().all()
    
    if not applications:
        return []
    
    return [ApplicationResponse.model_validate(app) for app in applications]


async def submitDraft(app_id: UUID, data: ApplicationUpsert | None, db: AsyncSession, user_id: UUID):
    """
    Submit a draft application for review.
    
    Authorization: chercheur only (own application)
    Actions: Transitions DRAFT → SUBMITTED, runs eligibility check
    """
    user = await verify_chercheur_role(user_id, db)
    
    # Get current session
    current_session = await get_current_session(db)
    if not current_session:
        raise HTTPException(status_code=400, detail="No active session available")
    
    application = await db.get(Application, app_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Verify ownership
    await verify_ownership(application.user_id, user_id)
    
    # Verify session
    if application.session_id != current_session.id:
        raise HTTPException(status_code=403, detail="Application is not in the current session")
    
    if application.status != Status.DRAFT:
        raise HTTPException(status_code=409, detail="Only drafts can be submitted")
    
    if data:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(application, field, value)
    
    try:
        ApplicationSubmission.model_validate(application)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Incomplete application: {str(e)}")
    
    application.status = Status.SUBMITTED
    application.submitted_at = datetime.today()
    
    try:
        score = await calculate_score(db,user_id)
        application.score = score
        
        # Automatically calculate indemnity budget for the submission
        await generate_indemnity_for_application(application, db)
        
        await db.commit()
        await db.refresh(application)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Run automatic eligibility verification
    try:
        eligibility_result = await perform_eligibility_check(application.id, db)
        return {
            "message": "Application submitted successfully",
            "id": str(application.id),
            "eligibility_status": "eligible" if eligibility_result.is_eligible else "rejected",
            "verification_errors": eligibility_result.errors if eligibility_result.errors else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")


async def cancel_application(app_id: UUID, data: ApplicationCancellationRequest, db: AsyncSession, user_id: UUID):
    
    user = await verify_chercheur_role(user_id, db)

    application = await db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this application")

    if application.status != Status.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=f"Only approved applications can be cancelled. Current status: {application.status}"
        )

    if not data.reason or not data.reason.strip():
        raise HTTPException(status_code=400, detail="Cancellation reason is required")

    application.status = Status.CANCELLATION_REQUEST
    application.cancellation_reason = data.reason.strip()
    application.cancelled_at = datetime.now()
    application.cancellation_requested_by = user.id
    application.closed_at = datetime.now()

    try:
        await db.commit()
        await db.refresh(application)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    message = f"Application {application.id} has been cancelled by the researcher. Reason: {application.cancellation_reason}"
    try:
        await create_notification(
            db,
            user.id,
            "Your application has been cancelled",
            message,
            NotificationType.status_change,
            demande_id=application.id,
        )
        await notify_admins(
            db,
            "Researcher cancelled an approved application",
            message,
            NotificationType.status_change,
            demande_id=application.id,
        )
    except Exception:
        pass
    # Reload with documents for response serialization
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.id == application.id)
    )
    application_with_docs = result.scalar_one()
    return ApplicationResponse.model_validate(application_with_docs)


async def deleteDraft(app_id: UUID, db: AsyncSession, user_id: UUID):
    """
    Delete a draft application.
    
    Authorization: chercheur only (own application)
    """
    user = await verify_chercheur_role(user_id, db)
    
    # Get current session
    current_session = await get_current_session(db)
    if not current_session:
        raise HTTPException(status_code=400, detail="No active session available")
    
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id)
        .where(Application.user_id == user_id)
        .where(Application.session_id == current_session.id)
    )
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found or not authorized")
    
    if draft.status != Status.DRAFT:
        raise HTTPException(status_code=403, detail="Only drafts can be deleted")
    
    try:
        await db.delete(draft)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return Response(status_code=204)

async def get_current_session(db: AsyncSession):
    result = await db.execute(
        select(Session).where(Session.is_open == True).where(Session.end_date >= date.today())
    )
    session = result.scalar_one_or_none()
    return session