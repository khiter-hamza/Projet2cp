from fastapi import HTTPException, Response , Depends
from uuid import UUID
from datetime import datetime
from pydantic import ValidationError
from sqlalchemy import select, desc, asc, or_, String
from app.core.database import AsyncSession
from app.schemas.application import *
from app.models.application import Application
from app.models.user import User
from app.models.session import Session
from app.models.enums import *
from app.services.application.eligibility_service import perform_eligibility_check
from app.core.database import AsyncSessionLocal, get_db
from app.services.auth_service_utils import (
    verify_chercheur_role,
    verify_cs_admin_role,
    verify_cs_admin_or_chercheur,
    verify_ownership
)


async def getUserApplication(app_id: UUID, user_id: UUID, db: AsyncSession):
    """
    Get an application.
    
    Authorization:
    - chercheur: Can only get own applications
    - CS admin:  Can get any application
    """
    user = await verify_cs_admin_or_chercheur(user_id, db)
    
    application = await db.get(Application, app_id)
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
    Restrictions: Max 1 draft per user at a time
    """
    user = await verify_chercheur_role(user_id, db)
    
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user_id)
        .where(Application.status == Status.DRAFT)
    )
    existing_draft = result.scalar_one_or_none()
    
    if existing_draft:
        raise HTTPException(status_code=409, detail="A draft already exists for this user")
    
    application = Application(user_id=user.id, **data.model_dump())
    
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
    
    return ApplicationResponse.model_validate(application)


async def updateDraft(app_id: UUID, data: ApplicationUpsert, db: AsyncSession, user_id: UUID):
    """
    Update a draft application.
    
    Authorization: chercheur only (own application)
    """
    user = await verify_chercheur_role(user_id, db)
    
    draft = await db.get(Application, app_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    # Verify ownership
    await verify_ownership(draft.user_id, user_id)
    
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
    
    return ApplicationResponse.model_validate(draft)


async def listApplications(db: AsyncSession, user_id: UUID, appFilterQuery: ApplicationFilterParams ):
    """
    List applications.
    
    Authorization:
    - chercheur: Can only list own applications
    - CS admin:  Can list all applications
    """
    user = await verify_cs_admin_or_chercheur(user_id, db)
    
    filters = appFilterQuery.model_dump()
    query = select(Application)
    
    # Chercheur can only see own applications
    if user.role == UserRole.chercheur:
        query = query.where(Application.user_id == user_id)
    
    if filters.get("status"):
        query = query.where(Application.status == filters["status"])    
    
    if filters.get("user_id"):
        # CS admin can filter by user_id, chercheur cannot
        if user.role == UserRole.chercheur:
            raise HTTPException(status_code=403, detail="Cannot filter by other user_id")
        query = query.where(Application.user_id.cast(String) == filters["user_id"])
    
    if filters.get("stage_type"):
        query = query.where(Application.stage_type == filters["stage_type"])
    
    if filters.get("destination_country"):
        query = query.where(Application.destination_country == filters["destination_country"])
    
    if filters.get("cs_decision"):
        query = query.where(Application.cs_decision == filters["cs_decision"])
    
    if filters.get("start_date_from"):
        query = query.where(Application.start_date >= filters["start_date_from"])
    
    if filters.get("start_date_to"):
        query = query.where(Application.start_date <= filters["start_date_to"])
    
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.join(Application.user).where(
            or_(
                User.username.ilike(search_term),
                Application.scientific_objective.ilike(search_term),
                Application.host_institution.ilike(search_term),
                Application.destination_city.ilike(search_term),
                Application.id.cast(String).ilike(search_term)
            )
        )
    
    sort_column = getattr(Application, filters.get("sort_by", "submitted_at"), Application.created_at)
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
    
    application = await db.get(Application, app_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Verify ownership
    await verify_ownership(application.user_id, user_id)
    
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


async def deleteDraft(app_id: UUID, db: AsyncSession, user_id: UUID):
    """
    Delete a draft application.
    
    Authorization: chercheur only (own application)
    """
    user = await verify_chercheur_role(user_id, db)
    
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id)
        .where(Application.user_id == user_id)
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

async def get_current_session(db: AsyncSessionLocal = Depends(get_db)):
    result = await db.execute(
        select(Session).where(Session.is_active == True, Session.end_date >= datetime.date.today())
    )
    session = result.scalar_one_or_none()
    return session