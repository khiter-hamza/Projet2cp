from fastapi import HTTPException, Response
from uuid import UUID
from datetime import datetime
from pydantic import ValidationError
from sqlalchemy import select, desc, asc, or_, String
from app.core.database import AsyncSession
from app.schemas.application import *
from app.models.application import Application
from app.models.user import User
from app.models.enums import *


async def getUserApplication(app_id: UUID, db: AsyncSession):
    application = await db.get(Application, app_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationResponse.model_validate(application)


async def createDraft(data: ApplicationUpsert, db: AsyncSession, user_id: UUID):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != UserRole.chercheur:
        raise HTTPException(status_code=403, detail="Not authorized to create applications")
    

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
    draft = await db.get(Application, app_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if draft.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this application")
    
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
    filters = appFilterQuery.model_dump()
    query = select(Application)
    
    if filters.get("status"):
        query = query.where(Application.status == filters["status"])    
    
    if filters.get("user_id"):
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
                Application.scientific_objective.ilike(search_term),
                Application.host_institution.ilike(search_term),
                Application.destination_city.ilike(search_term),
                Application.id.cast(String).ilike(search_term),
                User.username.ilike(search_term)
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
    application = await db.get(Application, app_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
    
    return {"message": "Application submitted successfully", "id": str(application.id)}


async def deleteDraft(app_id: UUID, db: AsyncSession, user_id: UUID):
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