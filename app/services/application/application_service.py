from fastapi import HTTPException ,Depends ,Response
from pydantic import ValidationError
from typing import Annotated
from sqlalchemy import select
from app.services.auth.auth_service import get_current_user
from app.core.database import get_db
from app.core.database import AsyncSession
from app.schemas.application import ApplicationResponse , ApplicationUpsert ,ApplicationSubmission
from app.models.application import Application
from app.models.user import User
from app.models.enums import *
from uuid import UUID
from sqlalchemy.orm import selectinload

async def getApplication(app_id:UUID,db:AsyncSession):
    application = await db.get(Application,app_id)
    if(not application):
        raise HTTPException(status_code=404,detail="Application not found")
    return ApplicationResponse.model_validate(application)

async def createDraft(data:ApplicationUpsert,db:AsyncSession ,user_id: UUID):
    user = await db.get(User,user_id)
    if(not user):
        raise HTTPException(status_code=404,detail="User not found.")
    result = await db.execute(select(Application).where(Application.user_id==user_id).where(Application.status==Status.brouillon))
    result = result.scalar_one_or_none()
    if(result):
        raise HTTPException(status_code=409,detail="A draft application already exists for this user.")
    data = data.model_dump()
    application = Application(user_id=user.id,**data)
    if(user.grade in (UserGrade.doctorant_non_salarie , UserGrade.doctorant_salarie)):
        application.stage_type = StageType.stage_perfectionnement
    else:
        application.stage_type = StageType.sejour_scientifique

    try:
        db.add(application)
        await db.commit()
        await db.refresh(application) 
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error.")

    try:
        response = ApplicationResponse.model_validate(application)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return response


async def updateDraft(app_id:UUID , data:ApplicationUpsert,db:AsyncSession,user_id: UUID):
    draft = await db.get(Application,app_id)
    if not draft:
        raise HTTPException(status_code=404, detail="No draft application found.")
    
    if draft.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this application.")
    
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(draft, field, value)

    try:
        await db.commit()
        await db.refresh(draft)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error.")
    try:
        return ApplicationResponse.model_validate(draft)
    except ValidationError as e:
        raise HTTPException(status_code=422,detail=str(e))

async def getUserApplications(db:AsyncSession,user_id:UUID):
    user = await db.get(User,user_id,options=[selectinload(User.applications)])
    try:
        result = [ApplicationResponse.model_validate(application) for application in user.applications]
    except ValidationError as e :
        raise HTTPException(status_code=422 , detail=str(e))
    return result

async def listAllApplications(db:AsyncSession):
    result = await db.execute(select(Application))
    result = result.scalars().all()
    if not result:
        return result
    try:
        result = [ApplicationResponse.model_validate(application) for application in result]
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return result

async def submitDraft(data: ApplicationUpsert, app_id: UUID, db: AsyncSession, user_id: UUID):
    application = await db.get(Application, app_id)

    if not application:
        if not data:
            raise HTTPException(status_code=404, detail="Draft not found")
        await createDraft(data, db, user_id)
        result = await db.execute(
            select(Application)
            .where(Application.user_id == user_id)
            .where(Application.status == Status.brouillon)
        )
        application = result.scalar_one()

    if application.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this application.")

    if application.status != Status.brouillon:
        raise HTTPException(status_code=409, detail="Only draft applications can be submitted.")

    try:
        if data:
            await updateDraft(app_id, data, db, user_id)
        await db.refresh(application)
        ApplicationSubmission.model_validate(application)
        application.status = Status.soumis
        await db.commit()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error.")

    return {"message": "Submission successful"}

async def deleteDraft(app_id: UUID, db: AsyncSession, user_id:UUID ):
    result = await db.execute(select(Application).where(Application.id==app_id).where(Application.status==Status.brouillon))
    draft = result.scalar_one_or_none()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found.")
    
    if draft.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this application.")
    
    try:
        await db.delete(draft)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error.")
    
    return Response(status_code=204)